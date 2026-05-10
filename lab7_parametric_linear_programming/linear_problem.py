from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class ParametricVector:
    """Vector of the form base + parameter * lambda."""

    base: List[Fraction]
    parameter: List[Fraction]

    def value_at(self, parameter_value: Fraction) -> List[Fraction]:
        return [
            self.base[index] + self.parameter[index] * parameter_value
            for index in range(len(self.base))
        ]


@dataclass(frozen=True)
class ParametricConstraint:
    coefficients: List[Fraction]
    sign: str
    rhs_base: Fraction
    rhs_parameter: Fraction = Fraction(0)


@dataclass(frozen=True)
class ParametricLinearProblem:
    objective_type: str
    objective: ParametricVector
    constraints: List[ParametricConstraint]
    parameter_name: str = "lambda"
    parameter_interval: Tuple[Optional[Fraction], Optional[Fraction]] = (None, None)
    variable_names: Optional[List[str]] = None


@dataclass(frozen=True)
class StandardFormProblem:
    objective_type: str
    objective: ParametricVector
    matrix: List[List[Fraction]]
    rhs: ParametricVector
    variable_names: List[str]
    original_variable_count: int
    parameter_name: str
    parameter_interval: Tuple[Optional[Fraction], Optional[Fraction]]


@dataclass(frozen=True)
class LinearExpression:
    constant: Fraction
    parameter_coefficient: Fraction

    def value_at(self, parameter_value: Fraction) -> Fraction:
        return self.constant + self.parameter_coefficient * parameter_value

    def as_text(self, parameter_name: str = "lambda") -> str:
        constant_text = format_fraction(self.constant)
        parameter_text = format_fraction(abs(self.parameter_coefficient))

        if self.parameter_coefficient == 0:
            return constant_text

        if self.constant == 0:
            if self.parameter_coefficient == 1:
                return parameter_name
            if self.parameter_coefficient == -1:
                return f"-{parameter_name}"
            return f"{format_fraction(self.parameter_coefficient)}*{parameter_name}"

        sign = "+" if self.parameter_coefficient > 0 else "-"
        if abs(self.parameter_coefficient) == 1:
            return f"{constant_text} {sign} {parameter_name}"
        return f"{constant_text} {sign} {parameter_text}*{parameter_name}"


@dataclass(frozen=True)
class BasisAnalysis:
    basis_indices: List[int]
    basis_names: List[str]
    non_basis_indices: List[int]
    inverse_basis_matrix: List[List[Fraction]]
    basic_solution: Dict[str, LinearExpression]
    reduced_costs: Dict[str, LinearExpression]
    feasibility_interval: Tuple[Optional[Fraction], Optional[Fraction]]
    optimality_interval: Tuple[Optional[Fraction], Optional[Fraction]]
    valid_interval: Tuple[Optional[Fraction], Optional[Fraction]]
    is_valid: bool
    sample_parameter_value: Optional[Fraction]
    sample_solution: Dict[str, Fraction]
    sample_objective_value: Optional[Fraction]


@dataclass(frozen=True)
class ParametricSimplexResult:
    status: str
    message: str
    basis_analyses: List[BasisAnalysis]
    valid_intervals: List[BasisAnalysis]
    parameter_name: str


def format_fraction(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def format_interval(interval: Tuple[Optional[Fraction], Optional[Fraction]], parameter_name: str = "lambda") -> str:
    left, right = interval
    left_text = "-inf" if left is None else format_fraction(left)
    right_text = "+inf" if right is None else format_fraction(right)
    return f"{left_text} <= {parameter_name} <= {right_text}"
