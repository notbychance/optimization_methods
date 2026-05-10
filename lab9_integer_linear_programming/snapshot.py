from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional

from fraction_tools import format_fraction
from linear_problem import BranchNode, Constraint


class SnapshotWriter:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if self.file_path.parent != Path("."):
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

        self.file_path.write_text(
            "# Снимки работы алгоритма целочисленного линейного программирования\n\n",
            encoding="utf-8",
        )

    def write_problem(
        self,
        objective_type: str,
        objective: List[Fraction],
        variable_names: List[str],
        variable_types: List[str],
        constraints: List[Constraint],
    ) -> None:
        lines: List[str] = []
        lines.append("## Исходная задача")
        lines.append("")
        lines.append(f"Тип целевой функции: `{objective_type}`")
        lines.append("")
        terms = []
        for coefficient, name in zip(objective, variable_names):
            terms.append(f"{format_fraction(coefficient)}*{name}")
        lines.append("Целевая функция:")
        lines.append("")
        lines.append(f"```text\n{objective_type} F = " + " + ".join(terms) + "\n```")
        lines.append("")
        lines.append("Типы переменных:")
        lines.append("")
        lines.append(self._markdown_row(["Переменная", "Тип"]))
        lines.append(self._markdown_separator(2))
        for name, variable_type in zip(variable_names, variable_types):
            lines.append(self._markdown_row([name, variable_type]))
        lines.append("")
        lines.append("Ограничения:")
        lines.append("")
        lines.append(self._markdown_row(["№", "Левая часть", "Знак", "Правая часть", "Имя"]))
        lines.append(self._markdown_separator(5))
        for index, constraint in enumerate(constraints, start=1):
            left_part = " + ".join(
                f"{format_fraction(coefficient)}*{variable_names[column_index]}"
                for column_index, coefficient in enumerate(constraint.coefficients)
            )
            lines.append(
                self._markdown_row(
                    [
                        str(index),
                        left_part,
                        constraint.sign,
                        format_fraction(constraint.rhs),
                        constraint.name,
                    ]
                )
            )
        lines.append("")
        self._append(lines)

    def write_node_start(self, node: BranchNode, variable_names: List[str]) -> None:
        lines = [
            f"## Узел {node.node_id}",
            "",
            f"- Глубина: {node.depth}",
            f"- Родительский узел: {node.parent_id if node.parent_id is not None else '-'}",
            f"- Описание ветвления: {node.description}",
            f"- Дополнительные ограничения: {node.constraints_text(variable_names)}",
            "",
        ]
        self._append(lines)

    def write_node_result(
        self,
        node: BranchNode,
        status: str,
        objective_value: Optional[Fraction],
        variables: Dict[str, Fraction],
        note: str,
    ) -> None:
        lines = [
            f"### Результат LP-релаксации узла {node.node_id}",
            "",
            f"Статус: `{status}`",
            "",
            f"Значение целевой функции LP-релаксации: `{format_fraction(objective_value)}`",
            "",
            "Значения переменных LP-релаксации:",
            "",
            self._markdown_row(["Переменная", "Значение"]),
            self._markdown_separator(2),
        ]
        for name, value in variables.items():
            lines.append(self._markdown_row([name, format_fraction(value)]))
        lines.append("")
        lines.append(f"Решение по узлу: {note}")
        lines.append("")
        self._append(lines)

    def write_branching(
        self,
        node: BranchNode,
        variable_name: str,
        value: Fraction,
        left_text: str,
        right_text: str,
    ) -> None:
        lines = [
            f"### Ветвление из узла {node.node_id}",
            "",
            f"Выбрана переменная `{variable_name}` со значением `{format_fraction(value)}`.",
            "",
            f"Левая ветвь: `{left_text}`",
            "",
            f"Правая ветвь: `{right_text}`",
            "",
        ]
        self._append(lines)

    def write_incumbent(
        self,
        objective_value: Fraction,
        variables: Dict[str, Fraction],
        node_id: int,
    ) -> None:
        lines = [
            f"### Обновление рекорда после узла {node_id}",
            "",
            f"Новое лучшее целочисленное значение: `{format_fraction(objective_value)}`.",
            "",
            self._markdown_row(["Переменная", "Значение"]),
            self._markdown_separator(2),
        ]
        for name, value in variables.items():
            lines.append(self._markdown_row([name, format_fraction(value)]))
        lines.append("")
        self._append(lines)

    def write_final_result(
        self,
        status: str,
        objective_value: Optional[Fraction],
        variables: Dict[str, Fraction],
        explored_nodes: int,
        message: str,
    ) -> None:
        lines = [
            "## Итоговый результат",
            "",
            f"Статус: `{status}`",
            "",
            f"Количество рассмотренных узлов: `{explored_nodes}`",
            "",
            f"Значение целевой функции: `{format_fraction(objective_value)}`",
            "",
            f"Сообщение: {message}",
            "",
        ]
        if len(variables) > 0:
            lines.append(self._markdown_row(["Переменная", "Значение"]))
            lines.append(self._markdown_separator(2))
            for name, value in variables.items():
                lines.append(self._markdown_row([name, format_fraction(value)]))
            lines.append("")
        self._append(lines)

    def write_tableau(
        self,
        title: str,
        node_id: int,
        phase: str,
        iteration: int,
        tableau: List[List[Fraction]],
        column_names: List[str],
        basis: List[int],
        objective_label: str,
        notes: str,
    ) -> None:
        lines: List[str] = []
        lines.append(f"### {title}")
        lines.append("")
        lines.append(f"- Узел дерева ветвей и границ: {node_id}")
        lines.append(f"- Фаза симплекс-метода: {phase}")
        lines.append(f"- Итерация внутри фазы: {iteration}")
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
            lines.append(self._markdown_row([basis_name] + [format_fraction(value) for value in row]))

        lines.append("")
        self._append(lines)

    def _append(self, lines: List[str]) -> None:
        with self.file_path.open("a", encoding="utf-8") as file:
            file.write("\n".join(lines))
            file.write("\n")

    def _markdown_row(self, values: List[str]) -> str:
        return "| " + " | ".join(str(value) for value in values) + " |"

    def _markdown_separator(self, size: int) -> str:
        return "| " + " | ".join(["---" for _ in range(size)]) + " |"
