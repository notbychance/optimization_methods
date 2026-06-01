from __future__ import annotations

from fractions import Fraction
from typing import Any, Dict, List, Optional, Set, Tuple

from linear_problem import CanonicalProblem, Constraint, DualSimplexResult, LinearProblem
from snapshot import SnapshotWriter


class DualSimplexSolver:
    def __init__(self, snapshot_writer: Optional[SnapshotWriter] = None):
        self.snapshot_writer = snapshot_writer
        self.iterations = 0

    def solve_model(self, problem: LinearProblem) -> DualSimplexResult:
        canonical_problem = self._build_canonical_problem(problem)
        tableau = [
            canonical_problem.matrix[row_index][:] + [canonical_problem.rhs[row_index]]
            for row_index in range(len(canonical_problem.matrix))
        ]
        objective_row = self._build_objective_row(
            costs=canonical_problem.max_costs,
            constraint_rows=tableau,
            basis=canonical_problem.basis,
        )
        tableau.append(objective_row)

        result = self._solve_tableau(
            tableau=tableau,
            column_names=canonical_problem.column_names,
            basis=canonical_problem.basis,
            max_costs=canonical_problem.max_costs,
            original_objective=canonical_problem.original_objective,
            original_variable_count=canonical_problem.original_variable_count,
            original_variable_names=canonical_problem.original_variable_names,
            objective_type=canonical_problem.objective_type,
            matrix=canonical_problem.matrix,
            rhs=canonical_problem.rhs,
        )

        if result.status == "not_dual_feasible":
            fallback_result = PrimalDiagnosticSimplexSolver(
                problem=problem,
                snapshot_writer=self.snapshot_writer,
            ).solve()
            fallback_result.message = (
                result.message
                + " Выполнена дополнительная диагностика обычным двухфазным симплекс-методом: "
                + fallback_result.message
            )
            return fallback_result

        return result

    def solve_tableau(self, data: Dict[str, Any]) -> DualSimplexResult:
        column_names: List[str] = data["column_names"]
        basis_names: List[str] = data["basis"]
        rows: List[List[Fraction]] = data["rows"]
        objective_row: List[Fraction] = data["objective_row"]
        max_costs: List[Fraction] = data["max_costs"]
        original_variable_count: int = data["original_variable_count"]
        original_objective: List[Fraction] = data["original_objective"]
        objective_type: str = data["objective_type"]

        if len(max_costs) != len(column_names):
            raise ValueError("Длина max_costs должна совпадать с количеством столбцов.")

        basis = []
        for basis_name in basis_names:
            if basis_name not in column_names:
                raise ValueError(f"Базисная переменная {basis_name} отсутствует в column_names.")
            basis.append(column_names.index(basis_name))

        for row_index, row in enumerate(rows, start=1):
            if len(row) != len(column_names) + 1:
                raise ValueError(f"Строка {row_index} должна содержать коэффициенты всех переменных и свободный член.")

        if len(objective_row) != len(column_names) + 1:
            raise ValueError("objective_row должна содержать коэффициенты всех переменных и свободный член.")

        tableau = [row[:] for row in rows] + [objective_row[:]]
        matrix = [row[:-1] for row in rows]
        rhs = [row[-1] for row in rows]
        original_variable_names = column_names[:original_variable_count]

        return self._solve_tableau(
            tableau=tableau,
            column_names=column_names,
            basis=basis,
            max_costs=max_costs,
            original_objective=original_objective,
            original_variable_count=original_variable_count,
            original_variable_names=original_variable_names,
            objective_type=objective_type,
            matrix=matrix,
            rhs=rhs,
        )

    def _solve_tableau(
        self,
        tableau: List[List[Fraction]],
        column_names: List[str],
        basis: List[int],
        max_costs: List[Fraction],
        original_objective: List[Fraction],
        original_variable_count: int,
        original_variable_names: List[str],
        objective_type: str,
        matrix: List[List[Fraction]],
        rhs: List[Fraction],
    ) -> DualSimplexResult:
        self.iterations = 0
        self._validate_tableau(tableau=tableau, column_names=column_names, basis=basis)

        self._snapshot(
            title="Исходная таблица двойственного симплекс-метода",
            iteration=0,
            tableau=tableau,
            column_names=column_names,
            basis=basis,
            objective_label="L",
            notes=(
                "Начальная таблица должна быть двойственно допустимой: "
                "в строке целевой функции все оценки z_j - c_j неотрицательны."
            ),
            matrix=matrix,
            rhs=rhs,
            max_costs=max_costs,
        )

        if not self._is_dual_feasible(tableau):
            return DualSimplexResult(
                status="not_dual_feasible",
                objective_value=None,
                variables={name: Fraction(0) for name in original_variable_names},
                iterations=self.iterations,
                message=(
                    "Начальная таблица не является двойственно допустимой: "
                    "в строке целевой функции есть отрицательные оценки. "
                    "Для такой таблицы нужен обычный симплекс-метод или другая начальная таблица."
                ),
            )

        while True:
            leaving_row = self._choose_leaving_row(tableau)

            if leaving_row is None:
                variables, objective_value = self._extract_solution(
                    tableau=tableau,
                    column_names=column_names,
                    basis=basis,
                    original_objective=original_objective,
                    original_variable_count=original_variable_count,
                    original_variable_names=original_variable_names,
                )
                self._snapshot(
                    title="Итоговая таблица",
                    iteration=self.iterations,
                    tableau=tableau,
                    column_names=column_names,
                    basis=basis,
                    objective_label="L",
                    notes="Все свободные члены неотрицательны, а оценки z_j - c_j неотрицательны. Оптимальное решение найдено.",
                    matrix=matrix,
                    rhs=rhs,
                    max_costs=max_costs,
                )
                return DualSimplexResult(
                    status="optimal",
                    objective_value=objective_value,
                    variables=variables,
                    iterations=self.iterations,
                    message="Оптимальное решение найдено двойственным симплекс-методом.",
                )

            entering_column = self._choose_entering_column(tableau, leaving_row)

            if entering_column is None:
                self._snapshot(
                    title="Допустимое решение отсутствует",
                    iteration=self.iterations,
                    tableau=tableau,
                    column_names=column_names,
                    basis=basis,
                    objective_label="L",
                    notes=(
                        f"В строке {column_names[basis[leaving_row]]} свободный член отрицателен, "
                        "но нет отрицательных коэффициентов для выбора вводимой переменной."
                    ),
                    matrix=matrix,
                    rhs=rhs,
                    max_costs=max_costs,
                )
                return DualSimplexResult(
                    status="infeasible",
                    objective_value=None,
                    variables={name: Fraction(0) for name in original_variable_names},
                    iterations=self.iterations,
                    message="У задачи отсутствует допустимое решение.",
                )

            old_basis_name = column_names[basis[leaving_row]]
            entering_name = column_names[entering_column]

            self._pivot(tableau=tableau, leaving_row=leaving_row, entering_column=entering_column)
            basis[leaving_row] = entering_column
            self.iterations += 1

            self._snapshot(
                title=f"Итерация {self.iterations}",
                iteration=self.iterations,
                tableau=tableau,
                column_names=column_names,
                basis=basis,
                objective_label="L",
                notes=(
                    f"Из базиса выведена переменная {old_basis_name}; "
                    f"в базис введена переменная {entering_name}."
                ),
                matrix=matrix,
                rhs=rhs,
                max_costs=max_costs,
            )

    def _build_canonical_problem(self, problem: LinearProblem) -> CanonicalProblem:
        self._validate_problem(problem)

        objective_type = problem.objective_type.lower()
        original_objective = problem.objective[:]
        max_costs = original_objective[:] if objective_type == "max" else [-value for value in original_objective]
        original_variable_count = len(problem.objective)
        original_variable_names = (
            problem.variable_names[:]
            if problem.variable_names is not None
            else [f"x{index + 1}" for index in range(original_variable_count)]
        )

        column_names = original_variable_names[:]
        matrix: List[List[Fraction]] = []
        rhs: List[Fraction] = []
        basis: List[int] = []
        additional_counter = 0

        for constraint in problem.constraints:
            row = constraint.coefficients[:] + [Fraction(0) for _ in range(len(column_names) - original_variable_count)]
            right_side = constraint.rhs

            def add_basis_variable(name: str, coefficient: Fraction) -> int:
                for existing_row in matrix:
                    existing_row.append(Fraction(0))
                row.append(coefficient)
                column_names.append(name)
                max_costs.append(Fraction(0))
                return len(column_names) - 1

            if constraint.sign == "<=":
                additional_counter += 1
                basis_column = add_basis_variable(f"s{additional_counter}", Fraction(1))
            elif constraint.sign == ">=":
                row = [-value for value in row]
                right_side = -right_side
                additional_counter += 1
                basis_column = add_basis_variable(f"s{additional_counter}", Fraction(1))
            elif constraint.sign == "=":
                additional_counter += 1
                basis_column = add_basis_variable(f"a{additional_counter}", Fraction(1))
            else:
                raise ValueError(f"Недопустимый знак ограничения: {constraint.sign}")

            matrix.append(row)
            rhs.append(right_side)
            basis.append(basis_column)

        return CanonicalProblem(
            objective_type=objective_type,
            original_objective=original_objective,
            max_costs=max_costs,
            column_names=column_names,
            original_variable_names=original_variable_names,
            original_variable_count=original_variable_count,
            matrix=matrix,
            rhs=rhs,
            basis=basis,
        )

    def _validate_problem(self, problem: LinearProblem) -> None:
        objective_type = problem.objective_type.lower()
        if objective_type not in {"max", "min"}:
            raise ValueError("Тип целевой функции должен быть 'max' или 'min'.")

        variable_count = len(problem.objective)
        if variable_count == 0:
            raise ValueError("Целевая функция должна содержать хотя бы один коэффициент.")

        if problem.variable_names is not None and len(problem.variable_names) != variable_count:
            raise ValueError("Количество имен переменных должно совпадать с количеством коэффициентов целевой функции.")

        if len(problem.constraints) == 0:
            raise ValueError("Должно быть задано хотя бы одно ограничение.")

        for constraint_index, constraint in enumerate(problem.constraints, start=1):
            if len(constraint.coefficients) != variable_count:
                raise ValueError(
                    f"В ограничении {constraint_index} количество коэффициентов не совпадает с целевой функцией."
                )
            if constraint.sign not in {"<=", ">=", "="}:
                raise ValueError(f"В ограничении {constraint_index} используется недопустимый знак: {constraint.sign}.")

    def _validate_tableau(self, tableau: List[List[Fraction]], column_names: List[str], basis: List[int]) -> None:
        if len(tableau) < 2:
            raise ValueError("Симплекс-таблица должна содержать хотя бы одну строку ограничений и строку целевой функции.")

        expected_row_length = len(column_names) + 1
        for row_index, row in enumerate(tableau, start=1):
            if len(row) != expected_row_length:
                raise ValueError(f"Строка {row_index} симплекс-таблицы имеет неверную длину.")

        if len(basis) != len(tableau) - 1:
            raise ValueError("Количество базисных переменных должно совпадать с количеством строк ограничений.")

        for basis_column in basis:
            if basis_column < 0 or basis_column >= len(column_names):
                raise ValueError("В базисе указан индекс переменной, которого нет в таблице.")

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

    def _is_dual_feasible(self, tableau: List[List[Fraction]]) -> bool:
        return all(value >= 0 for value in tableau[-1][:-1])

    def _choose_leaving_row(self, tableau: List[List[Fraction]]) -> Optional[int]:
        leaving_row = None
        smallest_rhs = Fraction(0)

        for row_index, row in enumerate(tableau[:-1]):
            if row[-1] < smallest_rhs:
                smallest_rhs = row[-1]
                leaving_row = row_index

        return leaving_row

    def _choose_entering_column(self, tableau: List[List[Fraction]], leaving_row: int) -> Optional[int]:
        best_column = None
        best_ratio = None
        objective_row = tableau[-1]
        selected_row = tableau[leaving_row]

        for column_index, coefficient in enumerate(selected_row[:-1]):
            if coefficient >= 0:
                continue

            ratio = objective_row[column_index] / (-coefficient)
            if best_ratio is None or ratio < best_ratio:
                best_ratio = ratio
                best_column = column_index

        return best_column

    def _pivot(self, tableau: List[List[Fraction]], leaving_row: int, entering_column: int) -> None:
        pivot_value = tableau[leaving_row][entering_column]

        if pivot_value == 0:
            raise ZeroDivisionError("Ведущий элемент равен нулю, пересчет таблицы невозможен.")

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

    def _extract_solution(
        self,
        tableau: List[List[Fraction]],
        column_names: List[str],
        basis: List[int],
        original_objective: List[Fraction],
        original_variable_count: int,
        original_variable_names: List[str],
    ) -> Tuple[dict[str, Fraction], Fraction]:
        all_values = [Fraction(0) for _ in column_names]
        for row_index, basis_column in enumerate(basis):
            all_values[basis_column] = tableau[row_index][-1]

        variables = {
            original_variable_names[index]: all_values[index]
            for index in range(original_variable_count)
        }
        objective_value = sum(
            original_objective[index] * all_values[index]
            for index in range(min(original_variable_count, len(original_objective)))
        )

        return variables, objective_value

    def _snapshot(
        self,
        title: str,
        iteration: int,
        tableau: List[List[Fraction]],
        column_names: List[str],
        basis: List[int],
        objective_label: str,
        notes: str,
        matrix: List[List[Fraction]],
        rhs: List[Fraction],
        max_costs: List[Fraction],
    ) -> None:
        if self.snapshot_writer is None:
            return

        self.snapshot_writer.write_tableau(
            title=title,
            iteration=iteration,
            tableau=tableau,
            column_names=column_names,
            basis=basis,
            objective_label=objective_label,
            notes=notes,
            matrix=matrix,
            rhs=rhs,
            max_costs=max_costs,
        )


class PrimalDiagnosticSimplexSolver:
    """Дополнительная диагностика для случаев, когда начальная таблица
    двойственного симплекс-метода не является двойственно допустимой.

    Класс использует обычный двухфазный симплекс-метод, чтобы отличить
    техническую проблему стартовой таблицы от математических итогов задачи:
    оптимум, несовместность или неограниченность целевой функции.
    """

    def __init__(self, problem: LinearProblem, snapshot_writer: Optional[SnapshotWriter] = None):
        self.problem = problem
        self.snapshot_writer = snapshot_writer
        self.iterations = 0
        self.original_variable_count = len(problem.objective)
        self.original_variable_names = (
            problem.variable_names[:]
            if problem.variable_names is not None
            else [f"x{index + 1}" for index in range(self.original_variable_count)]
        )

    def solve(self) -> DualSimplexResult:
        objective_type = self.problem.objective_type.lower()
        original_costs = self.problem.objective[:]
        max_costs = original_costs[:] if objective_type == "max" else [-value for value in original_costs]
        normalized_constraints = self._normalize_constraints(self.problem.constraints)

        tableau, column_names, phase_two_costs, basis, artificial_columns = self._build_initial_tableau(
            max_costs=max_costs,
            constraints=normalized_constraints,
            original_names=self.original_variable_names,
        )

        if artificial_columns:
            phase_one_costs = [Fraction(0) for _ in column_names]
            for artificial_column in artificial_columns:
                phase_one_costs[artificial_column] = Fraction(-1)

            tableau.append(self._build_objective_row(phase_one_costs, tableau, basis))
            self._snapshot(
                title="Дополнительная диагностика. Фаза I",
                iteration=0,
                tableau=tableau,
                column_names=column_names,
                basis=basis,
                objective_label="W",
                notes=(
                    "Начальная таблица двойственного симплекс-метода не была двойственно допустимой. "
                    "Для проверки математического статуса задачи запущен обычный двухфазный симплекс-метод."
                ),
            )

            phase_one_status = self._run_simplex(
                tableau=tableau,
                column_names=column_names,
                basis=basis,
                objective_label="W",
                stage_name="Фаза I",
            )

            if phase_one_status == "unbounded" or tableau[-1][-1] != 0:
                return DualSimplexResult(
                    status="infeasible",
                    objective_value=None,
                    variables={name: Fraction(0) for name in self.original_variable_names},
                    iterations=self.iterations,
                    message="система ограничений несовместна, допустимое решение отсутствует.",
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
                title="Дополнительная диагностика. Переход к фазе II",
                iteration=0,
                tableau=tableau,
                column_names=column_names,
                basis=basis,
                objective_label="L",
                notes="Искусственные переменные удалены. Проверяется исходная целевая функция.",
            )
        else:
            tableau.append(self._build_objective_row(phase_two_costs, tableau, basis))
            self._snapshot(
                title="Дополнительная диагностика. Фаза II",
                iteration=0,
                tableau=tableau,
                column_names=column_names,
                basis=basis,
                objective_label="L",
                notes="Искусственные переменные не требуются.",
            )

        phase_two_status = self._run_simplex(
            tableau=tableau,
            column_names=column_names,
            basis=basis,
            objective_label="L",
            stage_name="Фаза II",
        )

        if phase_two_status == "unbounded":
            return DualSimplexResult(
                status="unbounded",
                objective_value=None,
                variables={name: Fraction(0) for name in self.original_variable_names},
                iterations=self.iterations,
                message="целевая функция не ограничена на множестве допустимых решений.",
            )

        all_values = [Fraction(0) for _ in column_names]
        for row_index, basis_column in enumerate(basis):
            all_values[basis_column] = tableau[row_index][-1]

        original_values = all_values[: self.original_variable_count]
        variables = {
            self.original_variable_names[index]: original_values[index]
            for index in range(self.original_variable_count)
        }
        objective_value = sum(
            original_costs[index] * original_values[index]
            for index in range(self.original_variable_count)
        )

        self._snapshot(
            title="Дополнительная диагностика. Итоговая таблица",
            iteration=self.iterations,
            tableau=tableau,
            column_names=column_names,
            basis=basis,
            objective_label="L",
            notes="Оптимальное решение найдено обычным симплекс-методом.",
        )

        return DualSimplexResult(
            status="optimal",
            objective_value=objective_value,
            variables=variables,
            iterations=self.iterations,
            message="оптимальное решение найдено обычным двухфазным симплекс-методом.",
        )

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

    @staticmethod
    def _reverse_inequality(sign: str) -> str:
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
                basis.append(add_variable(f"s{slack_counter}", Fraction(1)))
            elif constraint.sign == ">=":
                surplus_counter += 1
                add_variable(f"e{surplus_counter}", Fraction(-1))
                artificial_counter += 1
                basis.append(add_variable(f"r{artificial_counter}", Fraction(1), is_artificial=True))
            elif constraint.sign == "=":
                artificial_counter += 1
                basis.append(add_variable(f"r{artificial_counter}", Fraction(1), is_artificial=True))
            else:
                raise ValueError(f"Недопустимый знак ограничения: {constraint.sign}")

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
        objective_label: str,
        stage_name: str,
    ) -> str:
        local_iteration = 0
        while True:
            entering_column = self._choose_entering_column(tableau[-1])
            if entering_column is None:
                self._snapshot(
                    title=f"Дополнительная диагностика. {stage_name}: условие оптимальности выполнено",
                    iteration=local_iteration,
                    tableau=tableau,
                    column_names=column_names,
                    basis=basis,
                    objective_label=objective_label,
                    notes="В строке целевой функции нет отрицательных коэффициентов.",
                )
                return "optimal"

            leaving_row = self._choose_leaving_row(tableau, entering_column)
            if leaving_row is None:
                self._snapshot(
                    title=f"Дополнительная диагностика. {stage_name}: обнаружена неограниченность",
                    iteration=local_iteration,
                    tableau=tableau,
                    column_names=column_names,
                    basis=basis,
                    objective_label=objective_label,
                    notes=(
                        f"Для вводимого столбца {column_names[entering_column]} "
                        "нет положительных элементов в ограничениях."
                    ),
                )
                return "unbounded"

            old_basis_name = column_names[basis[leaving_row]]
            entering_name = column_names[entering_column]
            self._pivot(tableau=tableau, leaving_row=leaving_row, entering_column=entering_column)
            basis[leaving_row] = entering_column
            self.iterations += 1
            local_iteration += 1
            self._snapshot(
                title=f"Дополнительная диагностика. {stage_name}: итерация {local_iteration}",
                iteration=local_iteration,
                tableau=tableau,
                column_names=column_names,
                basis=basis,
                objective_label=objective_label,
                notes=f"В базис введена переменная {entering_name}; из базиса выведена переменная {old_basis_name}.",
            )

    @staticmethod
    def _choose_entering_column(objective_row: List[Fraction]) -> Optional[int]:
        entering_column: Optional[int] = None
        best_value = Fraction(0)
        for column_index, value in enumerate(objective_row[:-1]):
            if value < best_value:
                best_value = value
                entering_column = column_index
        return entering_column

    @staticmethod
    def _choose_leaving_row(tableau: List[List[Fraction]], entering_column: int) -> Optional[int]:
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

    @staticmethod
    def _pivot(tableau: List[List[Fraction]], leaving_row: int, entering_column: int) -> None:
        pivot_value = tableau[leaving_row][entering_column]
        if pivot_value == 0:
            raise ZeroDivisionError("Ведущий элемент равен нулю, пересчет таблицы невозможен.")
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
                title="Дополнительная диагностика. Искусственная переменная выведена из базиса",
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
            new_tableau.append([row[column_index] for column_index in kept_columns] + [row[-1]])
            new_basis.append(column_mapping[basis[row_index]])
        new_column_names = [column_names[column_index] for column_index in kept_columns]
        new_costs = [costs[column_index] for column_index in kept_columns]
        new_tableau.append([Fraction(0) for _ in range(len(new_column_names) + 1)])
        return new_tableau, new_column_names, new_costs, new_basis

    def _snapshot(
        self,
        title: str,
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
            iteration=iteration,
            tableau=tableau,
            column_names=column_names,
            basis=basis,
            objective_label=objective_label,
            notes=notes,
        )
