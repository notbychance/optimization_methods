from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import List, Optional

from matrix_tools import (
    format_fraction,
    format_matrix,
    format_vector,
    invert_matrix,
    matrix_multiply,
    matrix_vector_multiply,
    select_columns,
    vector_matrix_multiply,
)


class SnapshotWriter:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if self.file_path.parent != Path("."):
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

        self.file_path.write_text(
            "# Снимки работы двойственного симплекс-метода\n\n",
            encoding="utf-8",
        )

    def write_tableau(
        self,
        title: str,
        iteration: int,
        tableau: List[List[Fraction]],
        column_names: List[str],
        basis: List[int],
        objective_label: str,
        notes: str,
        matrix: Optional[List[List[Fraction]]] = None,
        rhs: Optional[List[Fraction]] = None,
        max_costs: Optional[List[Fraction]] = None,
    ) -> None:
        lines: List[str] = []

        lines.append(f"## {title}")
        lines.append("")
        lines.append(f"- Итерация: {iteration}")
        lines.append(f"- Пояснение: {notes}")
        lines.append("")

        lines.append("### Симплекс-таблица")
        lines.append("")
        header = ["Базис"] + column_names + ["Свободные члены"]
        lines.append(self._markdown_row(header))
        lines.append(self._markdown_separator(len(header)))

        for row_index, row in enumerate(tableau):
            if row_index < len(basis):
                basis_name = column_names[basis[row_index]]
            else:
                basis_name = objective_label

            row_values = [basis_name] + [format_fraction(value) for value in row]
            lines.append(self._markdown_row(row_values))

        lines.append("")

        if matrix is not None and rhs is not None and max_costs is not None:
            lines.extend(
                self._build_matrix_representation_section(
                    column_names=column_names,
                    basis=basis,
                    matrix=matrix,
                    rhs=rhs,
                    max_costs=max_costs,
                )
            )

        lines.append("")
        lines.append("")

        with self.file_path.open("a", encoding="utf-8") as file:
            file.write("\n".join(lines))

    def _build_matrix_representation_section(
        self,
        column_names: List[str],
        basis: List[int],
        matrix: List[List[Fraction]],
        rhs: List[Fraction],
        max_costs: List[Fraction],
    ) -> List[str]:
        lines: List[str] = []

        try:
            basis_matrix = select_columns(matrix, basis)
            inverse_basis_matrix = invert_matrix(basis_matrix)
            transformed_matrix = matrix_multiply(inverse_basis_matrix, matrix)
            basis_solution = matrix_vector_multiply(inverse_basis_matrix, rhs)
            basis_costs = [max_costs[column_index] for column_index in basis]
            simplex_multipliers = vector_matrix_multiply(basis_costs, inverse_basis_matrix)
            estimates = [
                value - max_costs[column_index]
                for column_index, value in enumerate(vector_matrix_multiply(simplex_multipliers, matrix))
            ]
            objective_value = sum(basis_costs[row_index] * basis_solution[row_index] for row_index in range(len(basis)))
        except ValueError as error:
            lines.append("### Матричное представление")
            lines.append("")
            lines.append(f"Матричное представление не построено: {error}")
            lines.append("")
            return lines

        lines.append("### Матричное представление текущего базисного решения")
        lines.append("")
        lines.append("Базис:")
        lines.append("")
        lines.append(", ".join(column_names[column_index] for column_index in basis))
        lines.append("")

        lines.append("Матрица базиса B:")
        lines.extend(self._markdown_matrix(format_matrix(basis_matrix)))
        lines.append("")

        lines.append("Обратная матрица B^(-1):")
        lines.extend(self._markdown_matrix(format_matrix(inverse_basis_matrix)))
        lines.append("")

        lines.append("Вектор базисного решения X_B = B^(-1) * b:")
        lines.append("")
        lines.append(self._markdown_row(["Переменная", "Значение"]))
        lines.append(self._markdown_separator(2))
        for row_index, variable_value in enumerate(basis_solution):
            lines.append(self._markdown_row([column_names[basis[row_index]], format_fraction(variable_value)]))
        lines.append("")

        lines.append("Преобразованная матрица B^(-1) * A:")
        lines.extend(self._markdown_matrix(format_matrix(transformed_matrix), headers=column_names))
        lines.append("")

        lines.append("Оценки z_j - c_j:")
        lines.append("")
        lines.append(self._markdown_row(column_names))
        lines.append(self._markdown_separator(len(column_names)))
        lines.append(self._markdown_row(format_vector(estimates)))
        lines.append("")

        lines.append(f"Значение целевой функции в max-форме: {format_fraction(objective_value)}")
        lines.append("")

        return lines

    def _markdown_matrix(self, matrix: List[List[str]], headers: Optional[List[str]] = None) -> List[str]:
        if len(matrix) == 0:
            return ["", "Пустая матрица.", ""]

        lines: List[str] = []

        if headers is None:
            headers = [f"c{index + 1}" for index in range(len(matrix[0]))]

        lines.append("")
        lines.append(self._markdown_row(headers))
        lines.append(self._markdown_separator(len(headers)))
        for row in matrix:
            lines.append(self._markdown_row(row))
        lines.append("")
        return lines

    def _markdown_row(self, values: List[str]) -> str:
        return "| " + " | ".join(values) + " |"

    def _markdown_separator(self, size: int) -> str:
        return "| " + " | ".join(["---" for _ in range(size)]) + " |"
