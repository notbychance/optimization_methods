from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Union

Number = Union[int, float]


@dataclass(frozen=True)
class KnapsackItem:
    name: str
    weight: int
    profit: Number
    max_count: Optional[int] = None


@dataclass(frozen=True)
class KnapsackProblem:
    optimization: str
    capacity: int
    items: List[KnapsackItem]


@dataclass(frozen=True)
class Transition:
    state: str
    decision: str
    next_state: str
    value: Number


@dataclass(frozen=True)
class Stage:
    name: str
    states: List[str]
    transitions: List[Transition]


@dataclass(frozen=True)
class FiniteHorizonProblem:
    optimization: str
    initial_state: str
    stages: List[Stage]
    terminal_values: Dict[str, Number]


@dataclass(frozen=True)
class KnapsackResult:
    status: str
    objective_value: Number
    item_counts: Dict[str, int]
    used_capacity: int
    message: str


@dataclass(frozen=True)
class FiniteHorizonResult:
    status: str
    objective_value: Number
    initial_state: str
    path: List[Dict[str, Union[str, Number]]]
    message: str
