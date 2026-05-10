from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Optional


@dataclass
class Constraint:
    coefficients: List[Fraction]
    sign: str
    rhs: Fraction
    name: str = ""


@dataclass
class LinearProblem:
    objective_type: str
    objective: List[Fraction]
    constraints: List[Constraint]
    variable_names: List[str]


@dataclass
class IntegerLinearProblem:
    objective_type: str
    objective: List[Fraction]
    constraints: List[Constraint]
    variable_names: List[str]
    variable_types: List[str]
    max_nodes: int = 1000


@dataclass
class LpResult:
    status: str
    objective_value: Optional[Fraction]
    variables: Dict[str, Fraction]
    iterations: int
    message: str


@dataclass
class BranchConstraint:
    variable_index: int
    sign: str
    value: Fraction

    def to_text(self, variable_names: List[str]) -> str:
        return f"{variable_names[self.variable_index]} {self.sign} {self.value}"


@dataclass
class BranchNode:
    node_id: int
    depth: int
    branch_constraints: List[BranchConstraint] = field(default_factory=list)
    parent_id: Optional[int] = None
    description: str = "root"

    def constraints_text(self, variable_names: List[str]) -> str:
        if len(self.branch_constraints) == 0:
            return "нет дополнительных ограничений"
        return "; ".join(item.to_text(variable_names) for item in self.branch_constraints)


@dataclass
class IntegerResult:
    status: str
    objective_value: Optional[Fraction]
    variables: Dict[str, Fraction]
    explored_nodes: int
    message: str
