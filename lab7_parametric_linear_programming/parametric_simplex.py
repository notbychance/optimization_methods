from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from itertools import combinations
from typing import Dict, List, Optional, Sequence, Tuple

from linear_problem import (
    BasisAnalysis,
    LinearExpression,
    ParametricLinearProblem,
    ParametricSimplexResult,
    ParametricVector,
    StandardFormProblem,
)
from matrix_tools import get_column, inverse_matrix, multiply_matrix_vector, select_columns
from snapshot import SnapshotWriter

Interval = Tuple[Optional[Fraction], Optional[Fraction]]


class ParametricSimplexSolver:
    """
    Собственный алгоритм решения задачи параметрического линейного программирования.

    Используется перебор невырожденных базисов стандартной формы:
    1. задача приводится к равенствам за счет дополнительных переменных;
    2. для каждого базиса вычисляется B^(-1);
    3. находится X_B(lambda) = B^(-1)b(lambda);
    4. находятся оценки r_j(lambda) = c_j(lambda) - c_B(lambda)^T B^(-1)A_j;
    5. пересекаются интервалы допустимости и оптимальности.
    """

    def __init__(self, problem: ParametricLinearProblem, snapshot_writer: Optional[SnapshotWriter] = None):
        self.problem = problem
        self.snapshot_writer = snapshot_writer

    def solve(self) -> ParametricSimplexResult:
        self._validate_problem()
        standard_problem = self._to_standard_form(self.problem)

        if self.snapshot_writer is not None:
            self.snapshot_writer.write_standard_form(standard_problem)

        analyses: List[BasisAnalysis] = []
        valid_analyses: List[BasisAnalysis] = []

        row_count = len(standard_problem.matrix)
        column_count = len(standard_problem.variable_names)

        for basis_number, basis_indices_tuple in enumerate(combinations(range(column_count), row_count), start=1):
            basis_indices = list(basis_indices_tuple)
            analysis = self._analyze_basis(standard_problem, basis_indices)
            analyses.append(analysis)

            if self.snapshot_writer is not None:
                self.snapshot_writer.write_basis_analysis(analysis, standard_problem, basis_number)

            if analysis.is_valid:
                valid_analyses.append(analysis)

        valid_analyses.sort(key=lambda item: self._interval_sort_key(item.valid_interval))

        if self.snapshot_writer is not None:
            self.snapshot_writer.write_summary(valid_analyses, standard_problem)

        if not valid_analyses:
            return ParametricSimplexResult(
                status="no_optimal_interval",
                message="На заданном интервале параметра не найдено оптимального базиса. Возможна несовместность или неограниченность задачи на рассматриваемом диапазоне.",
                basis_analyses=analyses,
                valid_intervals=valid_analyses,
                parameter_name=standard_problem.parameter_name,
            )

        return ParametricSimplexResult(
            status="optimal_intervals",
            message="Найдены интервалы параметра, на которых соответствующие базисы являются оптимальными.",
            basis_analyses=analyses,
            valid_intervals=valid_analyses,
            parameter_name=standard_problem.parameter_name,
        )

    def _validate_problem(self) -> None:
        if self.problem.objective_type.lower() not in {"max", "min"}:
            raise ValueError("Тип целевой функции должен быть max или min.")

        variable_count = len(self.problem.objective.base)
        if variable_count == 0:
            raise ValueError("Целевая функция должна содержать хотя бы один коэффициент.")
        if len(self.problem.objective.parameter) != variable_count:
            raise ValueError("objective.base и objective.parameter должны иметь одинаковую длину.")
        if self.problem.variable_names is not None and len(self.problem.variable_names) != variable_count:
            raise ValueError("Количество имен переменных должно совпадать с количеством исходных переменных.")
        if not self.problem.constraints:
            raise ValueError("Должно быть задано хотя бы одно ограничение.")

        for index, constraint in enumerate(self.problem.constraints, start=1):
            if len(constraint.coefficients) != variable_count:
                raise ValueError(f"В ограничении {index} количество коэффициентов не совпадает с целевой функцией.")
            if constraint.sign not in {"<=", ">=", "="}:
                raise ValueError(f"В ограничении {index} задан недопустимый знак: {constraint.sign}.")

    def _to_standard_form(self, problem: ParametricLinearProblem) -> StandardFormProblem:
        original_variable_count = len(problem.objective.base)
        variable_names = problem.variable_names[:] if problem.variable_names is not None else [f"x{index + 1}" for index in range(original_variable_count)]

        objective_base = problem.objective.base[:]
        objective_parameter = problem.objective.parameter[:]

        if problem.objective_type.lower() == "min":
            objective_base = [-value for value in objective_base]
            objective_parameter = [-value for value in objective_parameter]

        matrix: List[List[Fraction]] = []
        rhs_base: List[Fraction] = []
        rhs_parameter: List[Fraction] = []
        additional_variable_counter = 0

        for constraint in problem.constraints:
            for row in matrix:
                row.append(Fraction(0))

            row = constraint.coefficients[:] + [Fraction(0) for _ in range(len(variable_names) - original_variable_count)]

            if constraint.sign == "<=":
                additional_variable_counter += 1
                variable_names.append(f"s{additional_variable_counter}")
                objective_base.append(Fraction(0))
                objective_parameter.append(Fraction(0))
                row.append(Fraction(1))
            elif constraint.sign == ">=":
                additional_variable_counter += 1
                variable_names.append(f"e{additional_variable_counter}")
                objective_base.append(Fraction(0))
                objective_parameter.append(Fraction(0))
                row.append(Fraction(-1))
            elif constraint.sign == "=":
                pass
            else:
                raise ValueError(f"Недопустимый знак ограничения: {constraint.sign}")

            matrix.append(row)
            rhs_base.append(constraint.rhs_base)
            rhs_parameter.append(constraint.rhs_parameter)

        return StandardFormProblem(
            objective_type="max",
            objective=ParametricVector(base=objective_base, parameter=objective_parameter),
            matrix=matrix,
            rhs=ParametricVector(base=rhs_base, parameter=rhs_parameter),
            variable_names=variable_names,
            original_variable_count=original_variable_count,
            parameter_name=problem.parameter_name,
            parameter_interval=problem.parameter_interval,
        )

    def _analyze_basis(self, problem: StandardFormProblem, basis_indices: List[int]) -> BasisAnalysis:
        basis_names = [problem.variable_names[index] for index in basis_indices]
        non_basis_indices = [index for index in range(len(problem.variable_names)) if index not in basis_indices]

        try:
            basis_matrix = select_columns(problem.matrix, basis_indices)
            inverse_basis = inverse_matrix(basis_matrix)
        except ValueError:
            return self._invalid_basis(problem, basis_indices, basis_names, non_basis_indices)

        x_base_constants = multiply_matrix_vector(inverse_basis, problem.rhs.base)
        x_base_parameters = multiply_matrix_vector(inverse_basis, problem.rhs.parameter)

        basic_solution: Dict[str, LinearExpression] = {}
        for index, variable_name in enumerate(basis_names):
            basic_solution[variable_name] = LinearExpression(x_base_constants[index], x_base_parameters[index])

        feasibility_interval = self._interval_from_linear_expressions(
            expressions=list(basic_solution.values()),
            relation=">=",
            base_interval=problem.parameter_interval,
        )

        c_b_base = [problem.objective.base[index] for index in basis_indices]
        c_b_parameter = [problem.objective.parameter[index] for index in basis_indices]

        reduced_costs: Dict[str, LinearExpression] = {}
        for variable_index in non_basis_indices:
            column = get_column(problem.matrix, variable_index)
            beta_column = multiply_matrix_vector(inverse_basis, column)
            y_a_base = sum(c_b_base[index] * beta_column[index] for index in range(len(basis_indices)))
            y_a_parameter = sum(c_b_parameter[index] * beta_column[index] for index in range(len(basis_indices)))

            reduced_constant = problem.objective.base[variable_index] - y_a_base
            reduced_parameter = problem.objective.parameter[variable_index] - y_a_parameter
            reduced_costs[problem.variable_names[variable_index]] = LinearExpression(reduced_constant, reduced_parameter)

        optimality_interval = self._interval_from_linear_expressions(
            expressions=list(reduced_costs.values()),
            relation="<=",
            base_interval=problem.parameter_interval,
        )

        valid_interval = self._intersect_intervals(feasibility_interval, optimality_interval)
        is_valid = self._is_non_empty_interval(valid_interval)
        sample_parameter_value = self._choose_sample_value(valid_interval) if is_valid else None

        sample_solution: Dict[str, Fraction] = {}
        sample_objective_value: Optional[Fraction] = None

        if sample_parameter_value is not None:
            all_values = {variable_name: Fraction(0) for variable_name in problem.variable_names}
            for variable_name, expression in basic_solution.items():
                all_values[variable_name] = expression.value_at(sample_parameter_value)

            sample_solution = {
                problem.variable_names[index]: all_values[problem.variable_names[index]]
                for index in range(problem.original_variable_count)
            }
            sample_objective_value = self._calculate_original_objective_value(sample_solution, sample_parameter_value)

        return BasisAnalysis(
            basis_indices=basis_indices,
            basis_names=basis_names,
            non_basis_indices=non_basis_indices,
            inverse_basis_matrix=inverse_basis,
            basic_solution=basic_solution,
            reduced_costs=reduced_costs,
            feasibility_interval=feasibility_interval,
            optimality_interval=optimality_interval,
            valid_interval=valid_interval,
            is_valid=is_valid,
            sample_parameter_value=sample_parameter_value,
            sample_solution=sample_solution,
            sample_objective_value=sample_objective_value,
        )

    def _invalid_basis(
        self,
        problem: StandardFormProblem,
        basis_indices: List[int],
        basis_names: List[str],
        non_basis_indices: List[int],
    ) -> BasisAnalysis:
        empty_interval = (Fraction(1), Fraction(0))
        return BasisAnalysis(
            basis_indices=basis_indices,
            basis_names=basis_names,
            non_basis_indices=non_basis_indices,
            inverse_basis_matrix=[],
            basic_solution={},
            reduced_costs={},
            feasibility_interval=empty_interval,
            optimality_interval=empty_interval,
            valid_interval=empty_interval,
            is_valid=False,
            sample_parameter_value=None,
            sample_solution={},
            sample_objective_value=None,
        )

    def _interval_from_linear_expressions(
        self,
        expressions: Sequence[LinearExpression],
        relation: str,
        base_interval: Interval,
    ) -> Interval:
        current_interval = base_interval
        for expression in expressions:
            expression_interval = self._single_linear_inequality_interval(expression, relation)
            current_interval = self._intersect_intervals(current_interval, expression_interval)
            if not self._is_non_empty_interval(current_interval):
                return current_interval
        return current_interval

    def _single_linear_inequality_interval(self, expression: LinearExpression, relation: str) -> Interval:
        a = expression.constant
        b = expression.parameter_coefficient

        if relation not in {">=", "<="}:
            raise ValueError("Поддерживаются только отношения >= и <=.")

        if b == 0:
            if (relation == ">=" and a >= 0) or (relation == "<=" and a <= 0):
                return None, None
            return Fraction(1), Fraction(0)

        border = -a / b

        if relation == ">=":
            if b > 0:
                return border, None
            return None, border

        if relation == "<=":
            if b > 0:
                return None, border
            return border, None

        raise ValueError("Недопустимое отношение.")

    def _intersect_intervals(self, first: Interval, second: Interval) -> Interval:
        left = self._max_bound(first[0], second[0])
        right = self._min_bound(first[1], second[1])
        return left, right

    def _is_non_empty_interval(self, interval: Interval) -> bool:
        left, right = interval
        if left is not None and right is not None and left > right:
            return False
        return True

    def _max_bound(self, first: Optional[Fraction], second: Optional[Fraction]) -> Optional[Fraction]:
        if first is None:
            return second
        if second is None:
            return first
        return max(first, second)

    def _min_bound(self, first: Optional[Fraction], second: Optional[Fraction]) -> Optional[Fraction]:
        if first is None:
            return second
        if second is None:
            return first
        return min(first, second)

    def _choose_sample_value(self, interval: Interval) -> Fraction:
        left, right = interval
        if left is not None and right is not None:
            return (left + right) / 2
        if left is not None:
            return left + 1
        if right is not None:
            return right - 1
        return Fraction(0)

    def _calculate_original_objective_value(self, solution: Dict[str, Fraction], parameter_value: Fraction) -> Fraction:
        variable_names = self.problem.variable_names[:] if self.problem.variable_names is not None else [f"x{index + 1}" for index in range(len(self.problem.objective.base))]
        objective_coefficients = self.problem.objective.value_at(parameter_value)
        return sum(objective_coefficients[index] * solution[variable_names[index]] for index in range(len(variable_names)))

    def _interval_sort_key(self, interval: Interval) -> Tuple[int, Fraction]:
        left = interval[0]
        if left is None:
            return 0, Fraction(0)
        return 1, left
