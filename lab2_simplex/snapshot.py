from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import List


class SnapshotWriter:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if self.file_path.parent != Path("."):
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

        self.file_path.write_text(
            "# Снимки работы симплекс-метода\n\n",
            encoding="utf-8",
        )

    def write_tableau(
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
        lines: List[str] = []

        lines.append(f"## {title}")
        lines.append("")
        lines.append(f"- Фаза: {phase}")
        lines.append(f"- Номер итерации внутри фазы: {iteration}")
        lines.append(f"- Пояснение: {notes}")
        lines.append("")

        header = ["Базис"] + column_names + ["Свободные члены"]
        lines.append(self._markdown_row(header))
        lines.append(self._markdown_separator(len(header)))

        for row_index, row in enumerate(tableau):
            if row_index < len(basis):
                basis_name = column_names[basis[row_index]]
            else:
                basis_name = objective_label

            row_values = [basis_name] + [self.format_fraction(value) for value in row]
            lines.append(self._markdown_row(row_values))

        lines.append("")
        lines.append("")

        with self.file_path.open("a", encoding="utf-8") as file:
            file.write("\n".join(lines))

    def _markdown_row(self, values: List[str]) -> str:
        return "| " + " | ".join(values) + " |"

    def _markdown_separator(self, size: int) -> str:
        return "| " + " | ".join(["---" for _ in range(size)]) + " |"

    @staticmethod
    def format_fraction(value: Fraction) -> str:
        if value.denominator == 1:
            return str(value.numerator)
        return f"{value.numerator}/{value.denominator}"
