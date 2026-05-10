from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Tuple

from fraction_tools import ceil_fraction, floor_fraction, format_fraction, is_integer
from linear_problem import (
    BranchConstraint,
    BranchNode,
    Constraint,
    IntegerLinearProblem,
    IntegerResult,
    LinearProblem,
    LpResult,
)
from simplex import SimplexSolver
from snapshot import SnapshotWriter


class BranchAndBoundSolver:
    def __init__(self, problem: IntegerLinearProblem, snapshot_writer: Optional[SnapshotWriter] = None):
        self.problem = problem
        self.snapshot_writer = snapshot_writer
        self.next_node_id = 1
        self.explored_nodes = 0
        self.best_objective: Optional[Fraction] = None
        self.best_variables: Dict[str, Fraction] = {}

    def solve(self) -> IntegerResult:
        self._validate_problem()

        root_constraints = self._build_root_constraints()

        if self.snapshot_writer is not None:
            self.snapshot_writer.write_problem(
                objective_type=self.problem.objective_type,
                objective=self.problem.objective,
                variable_names=self.problem.variable_names,
                variable_types=self.problem.variable_types,
                constraints=root_constraints,
            )

        root_node = BranchNode(
            node_id=self._take_node_id(),
            depth=0,
            branch_constraints=[],
            parent_id=None,
            description="исходная LP-релаксация",
        )

        stack: List[BranchNode] = [root_node]

        while len(stack) > 0:
            if self.explored_nodes >= self.problem.max_nodes:
                result = IntegerResult(
                    status="node_limit",
                    objective_value=self.best_objective,
                    variables=self.best_variables,
                    explored_nodes=self.explored_nodes,
                    message=f"Достигнут предел числа узлов: {self.problem.max_nodes}.",
                )
                self._write_final(result)
                return result

            node = stack.pop()
            self.explored_nodes += 1

            if self.snapshot_writer is not None:
                self.snapshot_writer.write_node_start(node=node, variable_names=self.problem.variable_names)

            lp_problem = self._build_lp_relaxation(root_constraints=root_constraints, node=node)
            lp_result = SimplexSolver(
                problem=lp_problem,
                snapshot_writer=self.snapshot_writer,
                node_id=node.node_id,
            ).solve()

            if lp_result.status == "infeasible":
                self._write_node_result(
                    node=node,
                    lp_result=lp_result,
                    note="Узел отброшен: LP-релаксация несовместна.",
                )
                continue

            if lp_result.status == "unbounded":
                result = IntegerResult(
                    status="unbounded",
                    objective_value=None,
                    variables={},
                    explored_nodes=self.explored_nodes,
                    message="LP-релаксация одного из узлов неограничена. Для данной реализации задача считается неограниченной.",
                )
                self._write_node_result(
                    node=node,
                    lp_result=lp_result,
                    note="Обнаружена неограниченная LP-релаксация.",
                )
                self._write_final(result)
                return result

            if lp_result.objective_value is None:
                self._write_node_result(
                    node=node,
                    lp_result=lp_result,
                    note="Узел отброшен: значение целевой функции не получено.",
                )
                continue

            if self._can_prune_by_bound(lp_result.objective_value):
                self._write_node_result(
                    node=node,
                    lp_result=lp_result,
                    note=(
                        "Узел отброшен по границе: оценка LP-релаксации не лучше "
                        f"текущего рекорда {format_fraction(self.best_objective)}."
                    ),
                )
                continue

            fractional_variable = self._find_fractional_integer_variable(lp_result.variables)

            if fractional_variable is None:
                self._write_node_result(
                    node=node,
                    lp_result=lp_result,
                    note="Получено допустимое целочисленное решение.",
                )
                self._try_update_incumbent(lp_result=lp_result, node_id=node.node_id)
                continue

            variable_index, variable_value = fractional_variable
            variable_name = self.problem.variable_names[variable_index]
            left_value = floor_fraction(variable_value)
            right_value = ceil_fraction(variable_value)

            left_branch = BranchConstraint(
                variable_index=variable_index,
                sign="<=",
                value=left_value,
            )
            right_branch = BranchConstraint(
                variable_index=variable_index,
                sign=">=",
                value=right_value,
            )

            self._write_node_result(
                node=node,
                lp_result=lp_result,
                note=(
                    f"Решение LP-релаксации нецелочисленное: "
                    f"{variable_name} = {format_fraction(variable_value)}. Выполняется ветвление."
                ),
            )

            if self.snapshot_writer is not None:
                self.snapshot_writer.write_branching(
                    node=node,
                    variable_name=variable_name,
                    value=variable_value,
                    left_text=left_branch.to_text(self.problem.variable_names),
                    right_text=right_branch.to_text(self.problem.variable_names),
                )

            right_node = BranchNode(
                node_id=self._take_node_id(),
                depth=node.depth + 1,
                branch_constraints=node.branch_constraints + [right_branch],
                parent_id=node.node_id,
                description=right_branch.to_text(self.problem.variable_names),
            )
            left_node = BranchNode(
                node_id=self._take_node_id(),
                depth=node.depth + 1,
                branch_constraints=node.branch_constraints + [left_branch],
                parent_id=node.node_id,
                description=left_branch.to_text(self.problem.variable_names),
            )

            stack.append(right_node)
            stack.append(left_node)

        if self.best_objective is None:
            result = IntegerResult(
                status="infeasible",
                objective_value=None,
                variables={},
                explored_nodes=self.explored_nodes,
                message="Целочисленное допустимое решение не найдено.",
            )
        else:
            result = IntegerResult(
                status="optimal",
                objective_value=self.best_objective,
                variables=self.best_variables,
                explored_nodes=self.explored_nodes,
                message="Оптимальное целочисленное решение найдено методом ветвей и границ.",
            )

        self._write_final(result)
        return result

    def _validate_problem(self) -> None:
        objective_type = self.problem.objective_type.lower()
        if objective_type not in {"max", "min"}:
            raise ValueError("Тип целевой функции должен быть 'max' или 'min'.")

        variable_count = len(self.problem.objective)
        if variable_count == 0:
            raise ValueError("Целевая функция должна содержать хотя бы один коэффициент.")

        if len(self.problem.variable_names) != variable_count:
            raise ValueError("Количество имен переменных должно совпадать с количеством коэффициентов целевой функции.")

        if len(self.problem.variable_types) != variable_count:
            raise ValueError("Количество типов переменных должно совпадать с количеством переменных.")

        for variable_type in self.problem.variable_types:
            if variable_type not in {"integer", "binary", "continuous"}:
                raise ValueError(f"Недопустимый тип переменной: {variable_type}.")

        for constraint_index, constraint in enumerate(self.problem.constraints, start=1):
            if len(constraint.coefficients) != variable_count:
                raise ValueError(
                    f"В ограничении {constraint_index} количество коэффициентов не совпадает с целевой функцией."
                )
            if constraint.sign not in {"<=", ">=", "="}:
                raise ValueError(f"В ограничении {constraint_index} используется недопустимый знак: {constraint.sign}.")

    def _build_root_constraints(self) -> List[Constraint]:
        root_constraints = [
            Constraint(
                coefficients=constraint.coefficients[:],
                sign=constraint.sign,
                rhs=constraint.rhs,
                name=constraint.name,
            )
            for constraint in self.problem.constraints
        ]

        for variable_index, variable_type in enumerate(self.problem.variable_types):
            if variable_type == "binary":
                coefficients = [Fraction(0) for _ in self.problem.variable_names]
                coefficients[variable_index] = Fraction(1)
                root_constraints.append(
                    Constraint(
                        coefficients=coefficients,
                        sign="<=",
                        rhs=Fraction(1),
                        name=f"binary upper bound for {self.problem.variable_names[variable_index]}",
                    )
                )

        return root_constraints

    def _build_lp_relaxation(self, root_constraints: List[Constraint], node: BranchNode) -> LinearProblem:
        constraints = [
            Constraint(
                coefficients=constraint.coefficients[:],
                sign=constraint.sign,
                rhs=constraint.rhs,
                name=constraint.name,
            )
            for constraint in root_constraints
        ]

        for branch_constraint in node.branch_constraints:
            coefficients = [Fraction(0) for _ in self.problem.variable_names]
            coefficients[branch_constraint.variable_index] = Fraction(1)
            constraints.append(
                Constraint(
                    coefficients=coefficients,
                    sign=branch_constraint.sign,
                    rhs=branch_constraint.value,
                    name=f"branch: {branch_constraint.to_text(self.problem.variable_names)}",
                )
            )

        return LinearProblem(
            objective_type=self.problem.objective_type,
            objective=self.problem.objective[:],
            constraints=constraints,
            variable_names=self.problem.variable_names[:],
        )

    def _can_prune_by_bound(self, lp_objective: Fraction) -> bool:
        if self.best_objective is None:
            return False

        if self.problem.objective_type == "max":
            return lp_objective <= self.best_objective

        return lp_objective >= self.best_objective

    def _find_fractional_integer_variable(self, variables: Dict[str, Fraction]) -> Optional[Tuple[int, Fraction]]:
        selected: Optional[Tuple[int, Fraction]] = None
        selected_distance = Fraction(-1)

        for index, variable_type in enumerate(self.problem.variable_types):
            if variable_type == "continuous":
                continue

            variable_name = self.problem.variable_names[index]
            value = variables[variable_name]

            if is_integer(value):
                continue

            lower = floor_fraction(value)
            upper = ceil_fraction(value)
            distance = min(value - lower, upper - value)

            if selected is None or distance > selected_distance:
                selected = (index, value)
                selected_distance = distance

        return selected

    def _try_update_incumbent(self, lp_result: LpResult, node_id: int) -> None:
        if lp_result.objective_value is None:
            return

        is_better = False
        if self.best_objective is None:
            is_better = True
        elif self.problem.objective_type == "max" and lp_result.objective_value > self.best_objective:
            is_better = True
        elif self.problem.objective_type == "min" and lp_result.objective_value < self.best_objective:
            is_better = True

        if not is_better:
            return

        self.best_objective = lp_result.objective_value
        self.best_variables = lp_result.variables.copy()

        if self.snapshot_writer is not None:
            self.snapshot_writer.write_incumbent(
                objective_value=self.best_objective,
                variables=self.best_variables,
                node_id=node_id,
            )

    def _write_node_result(self, node: BranchNode, lp_result: LpResult, note: str) -> None:
        if self.snapshot_writer is None:
            return

        self.snapshot_writer.write_node_result(
            node=node,
            status=lp_result.status,
            objective_value=lp_result.objective_value,
            variables=lp_result.variables,
            note=note,
        )

    def _write_final(self, result: IntegerResult) -> None:
        if self.snapshot_writer is None:
            return

        self.snapshot_writer.write_final_result(
            status=result.status,
            objective_value=result.objective_value,
            variables=result.variables,
            explored_nodes=result.explored_nodes,
            message=result.message,
        )

    def _take_node_id(self) -> int:
        node_id = self.next_node_id
        self.next_node_id += 1
        return node_id
