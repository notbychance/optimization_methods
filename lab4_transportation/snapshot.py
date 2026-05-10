from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import List, Optional, Set, Tuple


Cell = Tuple[int, int]


class SnapshotWriter:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if self.file_path.parent != Path("."):
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text("# Снимки решения транспортной задачи\n\n", encoding="utf-8")

    def write_problem(
        self,
        title: str,
        costs: List[List[Fraction]],
        supply: List[Fraction],
        demand: List[Fraction],
        source_names: List[str],
        destination_names: List[str],
        notes: str,
    ) -> None:
        lines: List[str] = []
        lines.append(f"## {title}")
        lines.append("")
        lines.append(notes)
        lines.append("")
        lines.append("### Матрица тарифов")
        lines.append("")

        header = ["Поставщик / потребитель"] + destination_names + ["Запас"]
        lines.append(self._markdown_row(header))
        lines.append(self._markdown_separator(len(header)))

        for row_index, row in enumerate(costs):
            values = [source_names[row_index]] + [self.format_fraction(value) for value in row] + [self.format_fraction(supply[row_index])]
            lines.append(self._markdown_row(values))

        values = ["Потребность"] + [self.format_fraction(value) for value in demand] + [self.format_fraction(sum(demand))]
        lines.append(self._markdown_row(values))
        lines.append("")
        lines.append("")
        self._append(lines)

    def write_solution(
        self,
        title: str,
        costs: List[List[Fraction]],
        allocations: List[List[Fraction]],
        basis: Set[Cell],
        source_names: List[str],
        destination_names: List[str],
        notes: str,
        potentials: Optional[Tuple[List[Fraction], List[Fraction]]],
        deltas: Optional[List[List[Optional[Fraction]]]],
        cycle: Optional[List[Cell]],
        theta: Optional[Fraction],
        total_cost: Fraction,
    ) -> None:
        lines: List[str] = []
        lines.append(f"## {title}")
        lines.append("")
        lines.append(notes)
        lines.append("")
        lines.append(f"Текущая стоимость плана: **{self.format_fraction(total_cost)}**")
        lines.append("")

        if potentials is not None:
            u, v = potentials
            lines.append("### Потенциалы")
            lines.append("")
            lines.append("**u:** " + ", ".join(f"u{i + 1} = {self.format_fraction(value)}" for i, value in enumerate(u)))
            lines.append("")
            lines.append("**v:** " + ", ".join(f"v{j + 1} = {self.format_fraction(value)}" for j, value in enumerate(v)))
            lines.append("")

        if cycle is not None:
            lines.append("### Цикл перераспределения")
            lines.append("")
            cycle_items: List[str] = []
            for index, cell in enumerate(cycle):
                sign = "+" if index % 2 == 0 else "-"
                row_index, column_index = cell
                cycle_items.append(f"{sign}({source_names[row_index]}, {destination_names[column_index]})")
            lines.append(" → ".join(cycle_items))
            if theta is not None:
                lines.append("")
                lines.append(f"θ = {self.format_fraction(theta)}")
            lines.append("")

        lines.append("### Транспортная таблица")
        lines.append("")
        lines.append("В ячейке указывается `перевозка / тариф`. Звездочка `*` означает базисную клетку.")
        lines.append("")

        header = ["Поставщик / потребитель"] + destination_names
        lines.append(self._markdown_row(header))
        lines.append(self._markdown_separator(len(header)))

        for row_index, row in enumerate(costs):
            values = [source_names[row_index]]
            for column_index, cost in enumerate(row):
                allocation = allocations[row_index][column_index]
                basis_mark = "*" if (row_index, column_index) in basis else ""
                values.append(f"{self.format_fraction(allocation)} / {self.format_fraction(cost)}{basis_mark}")
            lines.append(self._markdown_row(values))
        lines.append("")

        if deltas is not None:
            lines.append("### Оценки свободных клеток")
            lines.append("")
            lines.append("Для базисных клеток оценка не выводится.")
            lines.append("")
            lines.append(self._markdown_row(header))
            lines.append(self._markdown_separator(len(header)))
            for row_index, row in enumerate(deltas):
                values = [source_names[row_index]]
                for column_index, delta in enumerate(row):
                    if delta is None:
                        values.append("—")
                    else:
                        values.append(self.format_fraction(delta))
                lines.append(self._markdown_row(values))
            lines.append("")

        lines.append("")
        self._append(lines)

    def _append(self, lines: List[str]) -> None:
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
