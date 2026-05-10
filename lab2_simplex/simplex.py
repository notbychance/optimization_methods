from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Optional, Set, Tuple

from snapshot import SnapshotWriter


@dataclass
class Constraint:
    coefficients: List[Fraction]
    sign: str
    rhs: Fraction


@dataclass
class LinearProblem:
    objective_type: str
    objective: List[Fraction]
    constraints: List[Constraint]
    variable_names: Optional[List[str]] = None


@dataclass
class SimplexResult:
    status: str
    objective_value: Optional[Fraction]
    variables: Dict[str, Fraction]
    iterations: int
    message: str


class SimplexSolver:
    def __init__(self, problem: LinearProblem, snapshot_writer: Optional[SnapshotWriter] = None):
        self.problem = problem
        self.snapshot_writer = snapshot_writer
        self.iterations = 0
        self.original_variable_count = len(problem.objective)
        self.original_variable_names = (
            problem.variable_names[:]
            if problem.variable_names is not None
            else [f"x{i + 1}" for i in range(self.original_variable_count)]
        )

    def solve(self) -> SimplexResult:
        self._validate_problem()

        objective_type = self.problem.objective_type.lower()
        original_costs = self.problem.objective[:]
        max_costs = original_costs[:] if objective_type == "max" else [-value for value in original_costs]

        normalized_constraints = self._normalize_constraints(self.problem.constraints)

        tableau, column_names, phase_two_costs, basis, artificial_columns = self._build_initial_tableau(
            max_costs=max_costs,
            constraints=normalized_constraints,
            original_names=self.original_variable_names,
        )

        if len(artificial_columns) > 0:
            phase_one_costs = [Fraction(0) for _ in column_names]
            for artificial_column in artificial_columns:
                phase_one_costs[artificial_column] = Fraction(-1)

            tableau.append(self._build_objective_row(phase_one_costs, tableau, basis))

            self._snapshot(
                title="Фаза I. Исходная симплекс-таблица",
                phase="I",
                iteration=0,
                tableau=tableau,
                column_names=column_names,
                basis=basis,
                objective_label="W",
                notes="Введены искусственные переменные. Вспомогательная функция: W = - сумма искусственных переменных.",
            )

            phase_one_status = self._run_simplex(
                tableau=tableau,
                column_names=column_names,
                basis=basis,
                phase="I",
                objective_label="W",
            )

            if phase_one_status == "unbounded":
                return SimplexResult(
                    status="infeasible",
                    objective_value=None,
                    variables={name: Fraction(0) for name in self.original_variable_names},
                    iterations=self.iterations,
                    message="В фазе I задача не получила допустимого опорного решения.",
                )

            if tableau[-1][-1] != 0:
                return SimplexResult(
                    status="infeasible",
                    objective_value=None,
                    variables={name: Fraction(0) for name in self.original_variable_names},
                    iterations=self.iterations,
                    message="Система ограничений несовместна: максимум вспомогательной функции W не равен 0.",
                )

            self._snapshot(
                title="Фаза I завершена",
                phase="I",
                iteration=self.iterations,
                tableau=tableau,
                column_names=column_names,
                basis=basis,
                objective_label="W",
                notes="Получено допустимое опорное решение исходной задачи. Искусственные переменные должны быть удалены.",
            )

            self._remove_artificial_variables_from_basis(
                tableau=tableau,
                column_names=column_names,
                basis=basis,
                artificial_columns=artificial_columns,
                objective_label="W",
            )

            tableau, column_names, phase_two_costs, basis = self._drop_artificial_columns(
                tableau=tableau,
                column_names=column_names,
                costs=phase_two_costs,
                basis=basis,
                artificial_columns=artificial_columns,
            )

            tableau[-1] = self._build_objective_row(phase_two_costs, tableau[:-1], basis)

            self._snapshot(
                title="Переход к фазе II",
                phase="II",
                iteration=0,
                tableau=tableau,
                column_names=column_names,
                basis=basis,
                objective_label="L",
                notes="Искусственные переменные удалены. В таблицу подставлена исходная целевая функция.",
            )
        else:
            tableau.append(self._build_objective_row(phase_two_costs, tableau, basis))

            self._snapshot(
                title="Фаза II. Исходная симплекс-таблица",
                phase="II",
                iteration=0,
                tableau=tableau,
                column_names=column_names,
                basis=basis,
                objective_label="L",
                notes="Искусственные переменные не требуются: начальный базис получен за счет остаточных переменных.",
            )

        phase_two_status = self._run_simplex(
            tableau=tableau,
            column_names=column_names,
            basis=basis,
            phase="II",
            objective_label="L",
        )

        if phase_two_status == "unbounded":
            return SimplexResult(
                status="unbounded",
                objective_value=None,
                variables={name: Fraction(0) for name in self.original_variable_names},
                iterations=self.iterations,
                message="Целевая функция не ограничена на множестве допустимых решений.",
            )

        all_values = [Fraction(0) for _ in column_names]
        for row_index, basis_column in enumerate(basis):
            all_values[basis_column] = tableau[row_index][-1]

        original_values = all_values[: self.original_variable_count]
        objective_value = sum(original_costs[index] * original_values[index] for index in range(self.original_variable_count))

        variables = {
            self.original_variable_names[index]: original_values[index]
            for index in range(self.original_variable_count)
        }

        self._snapshot(
            title="Итоговая симплекс-таблица",
            phase="II",
            iteration=self.iterations,
            tableau=tableau,
            column_names=column_names,
            basis=basis,
            objective_label="L",
            notes=f"Оптимальное решение найдено. Значение исходной целевой функции: {self.format_fraction(objective_value)}.",
        )

        return SimplexResult(
            status="optimal",
            objective_value=objective_value,
            variables=variables,
            iterations=self.iterations,
            message="Оптимальное решение найдено.",
        )

    def _validate_problem(self) -> None:
        objective_type = self.problem.objective_type.lower()
        if objective_type not in {"max", "min"}:
            raise ValueError("Тип целевой функции должен быть 'max' или 'min'.")

        variable_count = len(self.problem.objective)
        if variable_count == 0:
            raise ValueError("Целевая функция должна содержать хотя бы один коэффициент.")

        if self.problem.variable_names is not None and len(self.problem.variable_names) != variable_count:
            raise ValueError("Количество имен переменных должно совпадать с количеством коэффициентов целевой функции.")

        if len(self.problem.constraints) == 0:
            raise ValueError("Должно быть задано хотя бы одно ограничение.")

        for constraint_index, constraint in enumerate(self.problem.constraints, start=1):
            if len(constraint.coefficients) != variable_count:
                raise ValueError(
                    f"В ограничении {constraint_index} количество коэффициентов не совпадает с целевой функцией."
                )
            if constraint.sign not in {"<=", ">=", "="}:
                raise ValueError(f"В ограничении {constraint_index} используется недопустимый знак: {constraint.sign}.")

    def _normalize_constraints(self, constraints: List[Constraint]) -> List[Constraint]:
        normalized_constraints: List[Constraint] = []

        for constraint in constraints:
            coefficients = constraint.coefficients[:]
            sign = constraint.sign
            rhs = constraint.rhs

            if rhs < 0:
                coefficients = [-value for value in coefficients]
                rhs = -rhs
                sign = self._reverse_inequality(sign)

            normalized_constraints.append(Constraint(coefficients=coefficients, sign=sign, rhs=rhs))

        return normalized_constraints

    def _reverse_inequality(self, sign: str) -> str:
        if sign == "<=":
            return ">="
        if sign == ">=":
            return "<="
        return sign

    def _build_initial_tableau(
        self,
        max_costs: List[Fraction],
        constraints: List[Constraint],
        original_names: List[str],
    ) -> Tuple[List[List[Fraction]], List[str], List[Fraction], List[int], Set[int]]:
        column_names = original_names[:]
        phase_two_costs = max_costs[:]
        rows: List[List[Fraction]] = []
        right_parts: List[Fraction] = []
        basis: List[int] = []
        artificial_columns: Set[int] = set()

        slack_counter = 0
        surplus_counter = 0
        artificial_counter = 0

        for constraint in constraints:
            row = constraint.coefficients[:] + [Fraction(0) for _ in range(len(column_names) - len(original_names))]

            def add_variable(name: str, coefficient: Fraction, is_artificial: bool = False) -> int:
                for existing_row in rows:
                    existing_row.append(Fraction(0))

                row.append(coefficient)
                column_names.append(name)
                phase_two_costs.append(Fraction(0))
                column_index = len(column_names) - 1

                if is_artificial:
                    artificial_columns.add(column_index)

                return column_index

            if constraint.sign == "<=":
                slack_counter += 1
                slack_index = add_variable(f"s{slack_counter}", Fraction(1))
                basis.append(slack_index)
            elif constraint.sign == ">=":
                surplus_counter += 1
                add_variable(f"e{surplus_counter}", Fraction(-1))

                artificial_counter += 1
                artificial_index = add_variable(f"r{artificial_counter}", Fraction(1), is_artificial=True)
                basis.append(artificial_index)
            elif constraint.sign == "=":
                artificial_counter += 1
                artificial_index = add_variable(f"r{artificial_counter}", Fraction(1), is_artificial=True)
                basis.append(artificial_index)
            else:
                raise ValueError(f"Недопустимый знак ограничения: {constraint.sign}.")

            rows.append(row)
            right_parts.append(constraint.rhs)

        tableau = [rows[index] + [right_parts[index]] for index in range(len(rows))]
        return tableau, column_names, phase_two_costs, basis, artificial_columns

    def _build_objective_row(
        self,
        costs: List[Fraction],
        constraint_rows: List[List[Fraction]],
        basis: List[int],
    ) -> List[Fraction]:
        objective_row = [-cost for cost in costs] + [Fraction(0)]

        for row_index, basis_column in enumerate(basis):
            basis_cost = costs[basis_column]
            if basis_cost == 0:
                continue

            for column_index in range(len(objective_row)):
                objective_row[column_index] += basis_cost * constraint_rows[row_index][column_index]

        return objective_row

    def _run_simplex(
        self,
        tableau: List[List[Fraction]],
        column_names: List[str],
        basis: List[int],
        phase: str,
        objective_label: str,
    ) -> str:
        local_iteration = 0

        while True:
            entering_column = self._choose_entering_column(tableau[-1])

            if entering_column is None:
                self._snapshot(
                    title=f"Фаза {phase}. Условие оптимальности выполнено",
                    phase=phase,
                    iteration=local_iteration,
                    tableau=tableau,
                    column_names=column_names,
                    basis=basis,
                    objective_label=objective_label,
                    notes="В строке целевой функции нет отрицательных коэффициентов. Текущий базис оптимален.",
                )
                return "optimal"

            leaving_row = self._choose_leaving_row(tableau, entering_column)

            if leaving_row is None:
                self._snapshot(
                    title=f"Фаза {phase}. Обнаружена неограниченность",
                    phase=phase,
                    iteration=local_iteration,
                    tableau=tableau,
                    column_names=column_names,
                    basis=basis,
                    objective_label=objective_label,
                    notes=f"Для вводимого столбца {column_names[entering_column]} нет положительных элементов в ограничениях.",
                )
                return "unbounded"

            old_basis_name = column_names[basis[leaving_row]]
            entering_name = column_names[entering_column]

            self._pivot(tableau=tableau, leaving_row=leaving_row, entering_column=entering_column)
            basis[leaving_row] = entering_column
            self.iterations += 1
            local_iteration += 1

            self._snapshot(
                title=f"Фаза {phase}. Итерация {local_iteration}",
                phase=phase,
                iteration=local_iteration,
                tableau=tableau,
                column_names=column_names,
                basis=basis,
                objective_label=objective_label,
                notes=f"В базис введена переменная {entering_name}; из базиса выведена переменная {old_basis_name}.",
            )

    def _choose_entering_column(self, objective_row: List[Fraction]) -> Optional[int]:
        entering_column: Optional[int] = None
        best_value = Fraction(0)

        for column_index, value in enumerate(objective_row[:-1]):
            if value < best_value:
                best_value = value
                entering_column = column_index

        return entering_column

    def _choose_leaving_row(self, tableau: List[List[Fraction]], entering_column: int) -> Optional[int]:
        best_row: Optional[int] = None
        best_ratio: Optional[Fraction] = None

        for row_index, row in enumerate(tableau[:-1]):
            coefficient = row[entering_column]

            if coefficient <= 0:
                continue

            ratio = row[-1] / coefficient

            if best_ratio is None or ratio < best_ratio:
                best_ratio = ratio
                best_row = row_index

        return best_row

    def _pivot(self, tableau: List[List[Fraction]], leaving_row: int, entering_column: int) -> None:
        pivot_value = tableau[leaving_row][entering_column]

        if pivot_value == 0:
            raise ZeroDivisionError("Ведущий элемент равен нулю, пересчет симплекс-таблицы невозможен.")

        tableau[leaving_row] = [value / pivot_value for value in tableau[leaving_row]]
        normalized_pivot_row = tableau[leaving_row][:]

        for row_index in range(len(tableau)):
            if row_index == leaving_row:
                continue

            factor = tableau[row_index][entering_column]
            if factor == 0:
                continue

            tableau[row_index] = [
                tableau[row_index][column_index] - factor * normalized_pivot_row[column_index]
                for column_index in range(len(tableau[row_index]))
            ]

    def _remove_artificial_variables_from_basis(
        self,
        tableau: List[List[Fraction]],
        column_names: List[str],
        basis: List[int],
        artificial_columns: Set[int],
        objective_label: str,
    ) -> None:
        for row_index, basis_column in enumerate(basis):
            if basis_column not in artificial_columns:
                continue

            entering_column: Optional[int] = None

            for column_index, coefficient in enumerate(tableau[row_index][:-1]):
                if column_index not in artificial_columns and coefficient != 0:
                    entering_column = column_index
                    break

            if entering_column is None:
                continue

            old_basis_name = column_names[basis_column]
            entering_name = column_names[entering_column]

            self._pivot(tableau=tableau, leaving_row=row_index, entering_column=entering_column)
            basis[row_index] = entering_column

            self._snapshot(
                title="Искусственная переменная выведена из базиса",
                phase="I",
                iteration=self.iterations,
                tableau=tableau,
                column_names=column_names,
                basis=basis,
                objective_label=objective_label,
                notes=f"Переменная {old_basis_name} заменена в базисе на переменную {entering_name}.",
            )

    def _drop_artificial_columns(
        self,
        tableau: List[List[Fraction]],
        column_names: List[str],
        costs: List[Fraction],
        basis: List[int],
        artificial_columns: Set[int],
    ) -> Tuple[List[List[Fraction]], List[str], List[Fraction], List[int]]:
        kept_columns = [
            column_index
            for column_index in range(len(column_names))
            if column_index not in artificial_columns
        ]
        column_mapping = {
            old_column_index: new_column_index
            for new_column_index, old_column_index in enumerate(kept_columns)
        }

        new_tableau: List[List[Fraction]] = []
        new_basis: List[int] = []

        for row_index, row in enumerate(tableau[:-1]):
            if basis[row_index] in artificial_columns:
                if row[-1] == 0:
                    continue
                raise ValueError("Искусственная переменная осталась в базисе с ненулевым значением.")

            new_row = [row[column_index] for column_index in kept_columns] + [row[-1]]
            new_tableau.append(new_row)
            new_basis.append(column_mapping[basis[row_index]])

        new_column_names = [column_names[column_index] for column_index in kept_columns]
        new_costs = [costs[column_index] for column_index in kept_columns]

        new_tableau.append([Fraction(0) for _ in range(len(new_column_names) + 1)])

        return new_tableau, new_column_names, new_costs, new_basis

    def _snapshot(
        self,
        title: str,
        phase: str,
        iteration: int,
        tableau: List[List[Fraction]],
        column_names: List[str],
        basis: List[int],
        objective_label: str,
        notes: str,
    ) -> None:
        if self.snapshot_writer is None:
            return

        self.snapshot_writer.write_tableau(
            title=title,
            phase=phase,
            iteration=iteration,
            tableau=tableau,
            column_names=column_names,
            basis=basis,
            objective_label=objective_label,
            notes=notes,
        )

    @staticmethod
    def format_fraction(value: Fraction) -> str:
        if value.denominator == 1:
            return str(value.numerator)
        return f"{value.numerator}/{value.denominator}"
