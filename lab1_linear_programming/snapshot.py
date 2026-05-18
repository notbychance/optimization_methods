from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional

from linear_problem import GraphicalSolution, LinearProblem2D, PointEvaluation


class SnapshotWriter:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if self.file_path.parent != Path("."):
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def write_solution(self, problem: LinearProblem2D, solution: GraphicalSolution) -> None:
        lines: List[str] = []

        lines.append("# Лабораторная работа №1. Решение задачи линейного программирования")
        lines.append("")
        lines.append(f"## {problem.title}")
        lines.append("")
        if problem.variant is not None:
            lines.append(f"- Вариант: {problem.variant}")
        lines.append(f"- Статус решения: `{solution.status}`")
        lines.append(f"- Сообщение: {solution.message}")
        if problem.note:
            lines.append(f"- Примечание: {problem.note}")
        lines.append("")

        lines.extend(self._build_model_section(problem))
        lines.extend(self._build_vertices_section(problem, solution.vertices))
        lines.extend(self._build_result_section(problem, solution))
        lines.extend(self._build_graph_section(solution.plot_path))

        self.file_path.write_text("\n".join(lines), encoding="utf-8")

    def _build_model_section(self, problem: LinearProblem2D) -> List[str]:
        lines: List[str] = []
        lines.append("## Математическая модель")
        lines.append("")
        lines.append("### Основные переменные")
        lines.append("")
        for variable in problem.variable_names:
            description = problem.variable_descriptions.get(variable, "")
            if description:
                lines.append(f"- `{variable}` — {description}")
            else:
                lines.append(f"- `{variable}`")
        lines.append("")

        if problem.derived_variables:
            lines.append("### Производные переменные")
            lines.append("")
            for derived_variable in problem.derived_variables:
                expression = derived_variable.expression or self._format_affine_expression(
                    derived_variable.coefficients,
                    problem.variable_names,
                    derived_variable.constant,
                )
                description = f" — {derived_variable.description}" if derived_variable.description else ""
                lines.append(f"- `{derived_variable.name} = {expression}`{description}")
            lines.append("")

        objective_word = "Максимизировать" if problem.objective_type == "max" else "Минимизировать"
        lines.append("### Целевая функция")
        lines.append("")
        lines.append(
            f"{objective_word}: `F = {self._format_linear_expression(problem.objective, problem.variable_names)}`"
        )
        if problem.objective_description:
            lines.append(f"  ")
            lines.append(problem.objective_description)
        lines.append("")

        lines.append("### Ограничения")
        lines.append("")
        lines.append("| № | Название | Ограничение | Пояснение |")
        lines.append("|---|---|---|---|")
        for index, constraint in enumerate(problem.constraints, start=1):
            expression = self._format_linear_expression(constraint.coefficients, problem.variable_names)
            lines.append(
                f"| {index} | {constraint.name} | `{expression} {constraint.sign} {self.format_fraction(constraint.rhs)}` | {constraint.description} |"
            )
        lines.append(
            f"| - | Неотрицательность | `{problem.variable_names[0]} >= 0`, `{problem.variable_names[1]} >= 0` | Область решений находится в первой четверти. |"
        )
        lines.append("")
        return lines

    def _build_vertices_section(
        self,
        problem: LinearProblem2D,
        vertices: List[PointEvaluation],
    ) -> List[str]:
        lines: List[str] = []
        lines.append("## Угловые точки области допустимых решений")
        lines.append("")
        if not vertices:
            lines.append("Допустимые угловые точки не найдены.")
            lines.append("")
            return lines

        lines.append(
            f"| № | {problem.variable_names[0]} | {problem.variable_names[1]} | F | Активные ограничения |"
        )
        lines.append("|---|---:|---:|---:|---|")
        for index, point in enumerate(vertices, start=1):
            lines.append(
                f"| {index} | {self.format_fraction(point.x)} | {self.format_fraction(point.y)} | {self.format_fraction(point.objective_value)} | {', '.join(point.active_constraints)} |"
            )
        lines.append("")
        return lines

    def _build_result_section(
        self,
        problem: LinearProblem2D,
        solution: GraphicalSolution,
    ) -> List[str]:
        lines: List[str] = []
        lines.append("## Ответ")
        lines.append("")

        if solution.optimal_point is None:
            lines.append("Оптимальное решение не найдено.")
            lines.append("")
            return lines

        optimal_point = solution.optimal_point
        lines.append(f"- `{problem.variable_names[0]} = {self.format_fraction(optimal_point.x)}`")
        lines.append(f"- `{problem.variable_names[1]} = {self.format_fraction(optimal_point.y)}`")
        for name, value in solution.derived_values.items():
            lines.append(f"- `{name} = {self.format_fraction(value)}`")
        lines.append(f"- `F = {self.format_fraction(optimal_point.objective_value)}`")
        lines.append("")
        return lines

    def _build_graph_section(self, plot_path: Optional[str]) -> List[str]:
        lines: List[str] = []
        lines.append("## Графическая интерпретация")
        lines.append("")
        if plot_path is None:
            lines.append("График не был построен.")
        else:
            plot_file = Path(plot_path)
            try:
                relative_plot_path = plot_file.relative_to(self.file_path.parent)
            except ValueError:
                relative_plot_path = plot_file
            lines.append(f"![Графическое решение]({relative_plot_path.as_posix()})")
        lines.append("")
        return lines

    def _format_linear_expression(self, coefficients: List[Fraction], variable_names: List[str]) -> str:
        parts: List[str] = []
        for coefficient, variable in zip(coefficients, variable_names):
            if coefficient == 0:
                continue
            if coefficient == 1:
                parts.append(variable)
            elif coefficient == -1:
                parts.append(f"-{variable}")
            else:
                parts.append(f"{self.format_fraction(coefficient)}{variable}")

        if not parts:
            return "0"

        expression = parts[0]
        for part in parts[1:]:
            if part.startswith("-"):
                expression += f" - {part[1:]}"
            else:
                expression += f" + {part}"
        return expression

    def _format_affine_expression(
        self,
        coefficients: List[Fraction],
        variable_names: List[str],
        constant: Fraction,
    ) -> str:
        expression = self._format_linear_expression(coefficients, variable_names)
        if constant == 0:
            return expression
        if expression == "0":
            return self.format_fraction(constant)
        if constant > 0:
            return f"{expression} + {self.format_fraction(constant)}"
        return f"{expression} - {self.format_fraction(-constant)}"

    @staticmethod
    def format_fraction(value: Fraction | None) -> str:
        if value is None:
            return "-"

        if value.denominator == 1:
            return str(value.numerator)

        return f"{value.numerator}/{value.denominator}"
