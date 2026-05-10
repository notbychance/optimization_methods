from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import List, Optional


@dataclass
class Constraint:
    coefficients: List[Fraction]
    sign: str
    rhs: Fraction


@dataclass
class LinearProblem:
    objective_type: str
    objective: List[Fraction]
    constraints: List[Constraint]
    variable_names: Optional[List[str]] = None


@dataclass
class CanonicalProblem:
    objective_type: str
    original_objective: List[Fraction]
    max_costs: List[Fraction]
    column_names: List[str]
    original_variable_names: List[str]
    original_variable_count: int
    matrix: List[List[Fraction]]
    rhs: List[Fraction]
    basis: List[int]


@dataclass
class DualSimplexResult:
    status: str
    objective_value: Optional[Fraction]
    variables: dict[str, Fraction]
    iterations: int
    message: str
