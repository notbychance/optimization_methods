from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from linear_problem import BasisAnalysis, LinearExpression, StandardFormProblem, format_fraction, format_interval


class SnapshotWriter:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if self.file_path.parent != Path("."):
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text("# Снимки алгоритма параметрического линейного программирования\n\n", encoding="utf-8")

    def write_standard_form(self, problem: StandardFormProblem) -> None:
        lines: List[str] = []
        parameter_name = problem.parameter_name

        lines.append("## 1. Приведение задачи к стандартной форме")
        lines.append("")
        lines.append(f"Параметр: `{parameter_name}`")
        lines.append(f"Интервал параметра: `{format_interval(problem.parameter_interval, parameter_name)}`")
        lines.append("")
        lines.append("### Целевая функция")
        lines.append("")
        objective_parts = []
        for index, variable_name in enumerate(problem.variable_names):
            expression = LinearExpression(problem.objective.base[index], problem.objective.parameter[index])
            objective_parts.append(f"({expression.as_text(parameter_name)})*{variable_name}")
        lines.append(f"{problem.objective_type.upper()} z = " + " + ".join(objective_parts))
        lines.append("")
        lines.append("### Матрица ограничений")
        lines.append("")
        header = ["№"] + problem.variable_names + ["Правая часть"]
        lines.append(self._markdown_row(header))
        lines.append(self._markdown_separator(len(header)))
        for row_index, row in enumerate(problem.matrix):
            rhs_expression = LinearExpression(problem.rhs.base[row_index], problem.rhs.parameter[row_index])
            values = [str(row_index + 1)] + [format_fraction(value) for value in row] + [rhs_expression.as_text(parameter_name)]
            lines.append(self._markdown_row(values))
        lines.append("")
        self._append_lines(lines)

    def write_basis_analysis(self, analysis: BasisAnalysis, problem: StandardFormProblem, number: int) -> None:
        lines: List[str] = []
        parameter_name = problem.parameter_name
        lines.append(f"## 2.{number}. Анализ базиса: {', '.join(analysis.basis_names)}")
        lines.append("")

        if not analysis.inverse_basis_matrix:
            lines.append("Базисная матрица вырождена, поэтому обратная матрица не существует. Такой базис не рассматривается как допустимый кандидат.")
            lines.append("")
            lines.append(f"Базис подходит: `нет`")
            lines.append("")
            self._append_lines(lines)
            return

        lines.append("### Обратная матрица базиса B^(-1)")
        lines.append("")
        lines.extend(self._matrix_table(analysis.inverse_basis_matrix, [f"col{index + 1}" for index in range(len(analysis.inverse_basis_matrix))]))
        lines.append("")

        lines.append("### Базисное решение X_B(lambda) = B^(-1) * b(lambda)")
        lines.append("")
        lines.append(self._markdown_row(["Базисная переменная", "Значение"] ))
        lines.append(self._markdown_separator(2))
        for variable_name in analysis.basis_names:
            lines.append(self._markdown_row([variable_name, analysis.basic_solution[variable_name].as_text(parameter_name)]))
        lines.append("")
        lines.append(f"Интервал допустимости: `{format_interval(analysis.feasibility_interval, parameter_name)}`")
        lines.append("")

        lines.append("### Оценки небазисных переменных")
        lines.append("")
        lines.append("Для задачи максимизации используется условие оптимальности: `r_j(lambda) = c_j(lambda) - c_B(lambda)^T * B^(-1) * A_j <= 0`.")
        lines.append("")
        lines.append(self._markdown_row(["Небазисная переменная", "r_j(lambda)"]))
        lines.append(self._markdown_separator(2))
        for variable_index in analysis.non_basis_indices:
            variable_name = problem.variable_names[variable_index]
            lines.append(self._markdown_row([variable_name, analysis.reduced_costs[variable_name].as_text(parameter_name)]))
        lines.append("")
        lines.append(f"Интервал оптимальности: `{format_interval(analysis.optimality_interval, parameter_name)}`")
        lines.append(f"Итоговый интервал базиса: `{format_interval(analysis.valid_interval, parameter_name)}`")
        lines.append(f"Базис подходит: `{'да' if analysis.is_valid else 'нет'}`")
        lines.append("")

        if analysis.sample_parameter_value is not None:
            lines.append("### Контрольная точка внутри найденного интервала")
            lines.append("")
            lines.append(f"Значение параметра: `{format_fraction(analysis.sample_parameter_value)}`")
            lines.append("")
            lines.append(self._markdown_row(["Переменная", "Значение"]))
            lines.append(self._markdown_separator(2))
            for variable_name, value in analysis.sample_solution.items():
                lines.append(self._markdown_row([variable_name, format_fraction(value)]))
            if analysis.sample_objective_value is not None:
                lines.append("")
                lines.append(f"Значение целевой функции в контрольной точке: `{format_fraction(analysis.sample_objective_value)}`")
            lines.append("")

        self._append_lines(lines)

    def write_summary(self, valid_analyses: List[BasisAnalysis], problem: StandardFormProblem) -> None:
        parameter_name = problem.parameter_name
        lines: List[str] = []
        lines.append("## 3. Итоговые интервалы оптимальности")
        lines.append("")

        if not valid_analyses:
            lines.append("На заданном интервале параметра не найдено ни одного оптимального базиса.")
            lines.append("")
            self._append_lines(lines)
            return

        lines.append(self._markdown_row(["Базис", f"Интервал {parameter_name}", "Контрольное значение", "z в контрольной точке"]))
        lines.append(self._markdown_separator(4))
        for analysis in valid_analyses:
            sample_text = "-" if analysis.sample_parameter_value is None else format_fraction(analysis.sample_parameter_value)
            objective_text = "-" if analysis.sample_objective_value is None else format_fraction(analysis.sample_objective_value)
            lines.append(
                self._markdown_row(
                    [
                        ", ".join(analysis.basis_names),
                        format_interval(analysis.valid_interval, parameter_name),
                        sample_text,
                        objective_text,
                    ]
                )
            )
        lines.append("")
        self._append_lines(lines)

    def _matrix_table(self, matrix: List[List[Fraction]], headers: List[str]) -> List[str]:
        lines: List[str] = []
        table_header = ["№"] + headers
        lines.append(self._markdown_row(table_header))
        lines.append(self._markdown_separator(len(table_header)))
        for row_index, row in enumerate(matrix):
            lines.append(self._markdown_row([str(row_index + 1)] + [format_fraction(value) for value in row]))
        return lines

    def _append_lines(self, lines: List[str]) -> None:
        with self.file_path.open("a", encoding="utf-8") as file:
            file.write("\n".join(lines))
            file.write("\n\n")

    def _markdown_row(self, values: Iterable[str]) -> str:
        return "| " + " | ".join(str(value) for value in values) + " |"

    def _markdown_separator(self, size: int) -> str:
        return "| " + " | ".join("---" for _ in range(size)) + " |"
