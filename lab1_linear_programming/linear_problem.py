from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Constraint:
    name: str
    coefficients: List[Fraction]
    sign: str
    rhs: Fraction
    description: str = ""


@dataclass(frozen=True)
class DerivedVariable:
    name: str
    coefficients: List[Fraction]
    constant: Fraction = Fraction(0)
    description: str = ""
    expression: str = ""


@dataclass(frozen=True)
class LinearProblem2D:
    title: str
    variant: Optional[int]
    objective_type: str
    objective: List[Fraction]
    constraints: List[Constraint]
    variable_names: List[str]
    variable_descriptions: Dict[str, str] = field(default_factory=dict)
    derived_variables: List[DerivedVariable] = field(default_factory=list)
    x_axis_label: str = "x1"
    y_axis_label: str = "x2"
    objective_description: str = ""
    note: str = ""


@dataclass(frozen=True)
class PointEvaluation:
    x: Fraction
    y: Fraction
    objective_value: Fraction
    active_constraints: List[str]


@dataclass(frozen=True)
class GraphicalSolution:
    status: str
    message: str
    vertices: List[PointEvaluation]
    optimal_point: Optional[PointEvaluation]
    derived_values: Dict[str, Fraction]
    plot_path: Optional[str]
