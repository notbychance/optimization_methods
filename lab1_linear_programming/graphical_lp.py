from __future__ import annotations

from fractions import Fraction
from math import atan2
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from linear_problem import Constraint, GraphicalSolution, LinearProblem2D, PointEvaluation

EPSILON = 1e-9


class GraphicalLinearProgrammingSolver:
    def __init__(self, problem: LinearProblem2D):
        self.problem = problem

    def solve(self, plot_path: Optional[str] = None) -> GraphicalSolution:
        vertices = self._find_vertices()

        if not vertices:
            return GraphicalSolution(
                status="infeasible",
                message="Область допустимых решений пуста.",
                vertices=[],
                optimal_point=None,
                derived_values={},
                plot_path=None,
            )

        if self.problem.objective_type == "max":
            optimal_point = max(vertices, key=lambda point: point.objective_value)
        else:
            optimal_point = min(vertices, key=lambda point: point.objective_value)

        derived_values = self._calculate_derived_values(optimal_point)

        saved_plot_path: Optional[str] = None
        if plot_path is not None:
            self.save_plot(plot_path=plot_path, vertices=vertices, optimal_point=optimal_point)
            saved_plot_path = plot_path

        return GraphicalSolution(
            status="optimal",
            message="Оптимальное решение найдено перебором угловых точек области допустимых решений.",
            vertices=vertices,
            optimal_point=optimal_point,
            derived_values=derived_values,
            plot_path=saved_plot_path,
        )

    def _find_vertices(self) -> List[PointEvaluation]:
        boundaries = self._boundaries_with_nonnegativity()
        raw_points: List[Tuple[Fraction, Fraction]] = []

        for first_index in range(len(boundaries)):
            for second_index in range(first_index + 1, len(boundaries)):
                point = self._intersect_boundaries(boundaries[first_index], boundaries[second_index])
                if point is not None and self._is_feasible(point[0], point[1]):
                    raw_points.append(point)

        unique_points = self._unique_points(raw_points)
        evaluated_points = [self._evaluate_point(x, y) for x, y in unique_points]
        evaluated_points.sort(key=lambda point: (point.x, point.y))
        return evaluated_points

    def _boundaries_with_nonnegativity(self) -> List[Constraint]:
        return [
            Constraint(name=f"{self.problem.variable_names[0]} = 0", coefficients=[Fraction(1), Fraction(0)], sign="=", rhs=Fraction(0)),
            Constraint(name=f"{self.problem.variable_names[1]} = 0", coefficients=[Fraction(0), Fraction(1)], sign="=", rhs=Fraction(0)),
            *self.problem.constraints,
        ]

    def _intersect_boundaries(
        self,
        first: Constraint,
        second: Constraint,
    ) -> Optional[Tuple[Fraction, Fraction]]:
        a1, b1 = first.coefficients
        a2, b2 = second.coefficients
        c1 = first.rhs
        c2 = second.rhs

        determinant = a1 * b2 - a2 * b1
        if determinant == 0:
            return None

        x = (c1 * b2 - c2 * b1) / determinant
        y = (a1 * c2 - a2 * c1) / determinant
        return x, y

    def _is_feasible(self, x: Fraction, y: Fraction) -> bool:
        if float(x) < -EPSILON or float(y) < -EPSILON:
            return False

        for constraint in self.problem.constraints:
            left_value = constraint.coefficients[0] * x + constraint.coefficients[1] * y
            if constraint.sign == "<=" and float(left_value - constraint.rhs) > EPSILON:
                return False
            if constraint.sign == ">=" and float(constraint.rhs - left_value) > EPSILON:
                return False
            if constraint.sign == "=" and abs(float(left_value - constraint.rhs)) > EPSILON:
                return False

        return True

    def _unique_points(self, points: Iterable[Tuple[Fraction, Fraction]]) -> List[Tuple[Fraction, Fraction]]:
        unique: Dict[Tuple[Fraction, Fraction], Tuple[Fraction, Fraction]] = {}
        for x, y in points:
            if abs(float(x)) < EPSILON:
                x = Fraction(0)
            if abs(float(y)) < EPSILON:
                y = Fraction(0)
            unique[(x, y)] = (x, y)
        return list(unique.values())

    def _evaluate_point(self, x: Fraction, y: Fraction) -> PointEvaluation:
        objective_value = self.problem.objective[0] * x + self.problem.objective[1] * y
        active_constraints: List[str] = []

        if x == 0:
            active_constraints.append(f"{self.problem.variable_names[0]} = 0")
        if y == 0:
            active_constraints.append(f"{self.problem.variable_names[1]} = 0")

        for constraint in self.problem.constraints:
            left_value = constraint.coefficients[0] * x + constraint.coefficients[1] * y
            if abs(float(left_value - constraint.rhs)) <= EPSILON:
                active_constraints.append(constraint.name)

        return PointEvaluation(
            x=x,
            y=y,
            objective_value=objective_value,
            active_constraints=active_constraints,
        )

    def _calculate_derived_values(self, optimal_point: PointEvaluation) -> Dict[str, Fraction]:
        values: Dict[str, Fraction] = {}
        for derived_variable in self.problem.derived_variables:
            value = (
                derived_variable.constant
                + derived_variable.coefficients[0] * optimal_point.x
                + derived_variable.coefficients[1] * optimal_point.y
            )
            values[derived_variable.name] = value
        return values

    def save_plot(
        self,
        plot_path: str,
        vertices: List[PointEvaluation],
        optimal_point: PointEvaluation,
    ) -> None:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        path = Path(plot_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        max_x, max_y = self._calculate_plot_limits(vertices)
        xs = np.linspace(0, max_x, 700)
        ys = np.linspace(0, max_y, 700)
        grid_x, grid_y = np.meshgrid(xs, ys)
        feasible_mask = np.ones_like(grid_x, dtype=bool)

        for constraint in self.problem.constraints:
            a, b = [float(value) for value in constraint.coefficients]
            rhs = float(constraint.rhs)
            left = a * grid_x + b * grid_y
            if constraint.sign == "<=":
                feasible_mask &= left <= rhs + EPSILON
            elif constraint.sign == ">=":
                feasible_mask &= left >= rhs - EPSILON
            else:
                feasible_mask &= np.abs(left - rhs) <= 0.02 * max(1.0, rhs)

        figure, axis = plt.subplots(figsize=(10, 7))
        axis.contourf(grid_x, grid_y, feasible_mask.astype(int), levels=[0.5, 1.5], alpha=0.25)

        for constraint in self.problem.constraints:
            self._draw_constraint_line(axis, constraint, max_x, max_y)

        polygon = self._sort_polygon_points(vertices)
        if len(polygon) >= 3:
            axis.plot([float(point.x) for point in polygon] + [float(polygon[0].x)], [float(point.y) for point in polygon] + [float(polygon[0].y)], linewidth=2)

        axis.scatter(
            [float(point.x) for point in vertices],
            [float(point.y) for point in vertices],
            zorder=5,
            label="Угловые точки",
        )
        axis.scatter(
            [float(optimal_point.x)],
            [float(optimal_point.y)],
            marker="*",
            s=220,
            zorder=6,
            label="Оптимум",
        )

        self._draw_objective_line(axis, optimal_point, max_x, max_y)

        axis.set_xlim(0, max_x)
        axis.set_ylim(0, max_y)
        axis.set_xlabel(self.problem.x_axis_label)
        axis.set_ylabel(self.problem.y_axis_label)
        axis.set_title(self.problem.title)
        axis.grid(True, alpha=0.35)
        axis.legend(loc="best")
        figure.tight_layout()
        figure.savefig(path, dpi=160)
        plt.close(figure)

    def _calculate_plot_limits(self, vertices: List[PointEvaluation]) -> Tuple[float, float]:
        max_vertex_x = max([float(point.x) for point in vertices] + [1.0])
        max_vertex_y = max([float(point.y) for point in vertices] + [1.0])

        intercept_x_values: List[float] = []
        intercept_y_values: List[float] = []
        for constraint in self.problem.constraints:
            a, b = constraint.coefficients
            if a > 0:
                intercept_x_values.append(float(constraint.rhs / a))
            if b > 0:
                intercept_y_values.append(float(constraint.rhs / b))

        max_x = max([max_vertex_x, *intercept_x_values, 1.0]) * 1.12
        max_y = max([max_vertex_y, *intercept_y_values, 1.0]) * 1.12
        return max_x, max_y

    def _draw_constraint_line(self, axis, constraint: Constraint, max_x: float, max_y: float) -> None:
        import numpy as np

        a, b = [float(value) for value in constraint.coefficients]
        rhs = float(constraint.rhs)

        if abs(b) > EPSILON:
            xs = np.linspace(0, max_x, 300)
            ys = (rhs - a * xs) / b
            visible = (ys >= 0) & (ys <= max_y)
            axis.plot(xs[visible], ys[visible], label=f"{constraint.name}: {self._format_constraint(constraint)}")
        elif abs(a) > EPSILON:
            x = rhs / a
            if 0 <= x <= max_x:
                axis.axvline(x=x, label=f"{constraint.name}: {self._format_constraint(constraint)}")

    def _draw_objective_line(self, axis, optimal_point: PointEvaluation, max_x: float, max_y: float) -> None:
        import numpy as np

        c1, c2 = [float(value) for value in self.problem.objective]
        objective = float(optimal_point.objective_value)

        if abs(c2) > EPSILON:
            xs = np.linspace(0, max_x, 300)
            ys = (objective - c1 * xs) / c2
            visible = (ys >= 0) & (ys <= max_y)
            axis.plot(xs[visible], ys[visible], linestyle="--", linewidth=2, label="Целевая функция в оптимуме")
        elif abs(c1) > EPSILON:
            x = objective / c1
            if 0 <= x <= max_x:
                axis.axvline(x=x, linestyle="--", linewidth=2, label="Целевая функция в оптимуме")

    def _sort_polygon_points(self, vertices: List[PointEvaluation]) -> List[PointEvaluation]:
        center_x = sum(float(point.x) for point in vertices) / len(vertices)
        center_y = sum(float(point.y) for point in vertices) / len(vertices)
        return sorted(vertices, key=lambda point: atan2(float(point.y) - center_y, float(point.x) - center_x))

    def _format_constraint(self, constraint: Constraint) -> str:
        left = self._format_linear_expression(constraint.coefficients)
        return f"{left} {constraint.sign} {self._format_fraction(constraint.rhs)}"

    def _format_linear_expression(self, coefficients: List[Fraction]) -> str:
        parts: List[str] = []
        for coefficient, variable in zip(coefficients, self.problem.variable_names):
            if coefficient == 0:
                continue
            if coefficient == 1:
                parts.append(variable)
            elif coefficient == -1:
                parts.append(f"-{variable}")
            else:
                parts.append(f"{self._format_fraction(coefficient)}{variable}")

        if not parts:
            return "0"

        expression = parts[0]
        for part in parts[1:]:
            if part.startswith("-"):
                expression += f" - {part[1:]}"
            else:
                expression += f" + {part}"
        return expression

    @staticmethod
    def _format_fraction(value: Fraction) -> str:
        if value.denominator == 1:
            return str(value.numerator)
        return f"{value.numerator}/{value.denominator}"
