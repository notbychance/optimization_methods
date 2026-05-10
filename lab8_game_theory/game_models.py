from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Optional, Tuple


@dataclass
class MatrixGameProblem:
    payoff_matrix: List[List[Fraction]]
    row_strategy_names: List[str]
    column_strategy_names: List[str]


@dataclass
class MatrixGameResult:
    status: str
    game_value: Optional[Fraction]
    row_strategy_probabilities: Dict[str, Fraction]
    column_strategy_probabilities: Dict[str, Fraction]
    row_support: List[str]
    column_support: List[str]
    saddle_points: List[Tuple[str, str, Fraction]]
    message: str


@dataclass
class DecisionProblem:
    objective: str
    payoff_matrix: List[List[Fraction]]
    alternative_names: List[str]
    state_names: List[str]
    probabilities: Optional[List[Fraction]]
    hurwicz_alpha: Fraction


@dataclass
class CriterionResult:
    criterion_name: str
    values_by_alternative: Dict[str, Fraction]
    best_value: Fraction
    best_alternatives: List[str]


@dataclass
class DecisionResult:
    status: str
    criteria: List[CriterionResult]
    message: str


@dataclass
class BimatrixGameProblem:
    row_player_matrix: List[List[Fraction]]
    column_player_matrix: List[List[Fraction]]
    row_strategy_names: List[str]
    column_strategy_names: List[str]


@dataclass
class NashEquilibrium:
    row_strategy: str
    column_strategy: str
    row_player_payoff: Fraction
    column_player_payoff: Fraction


@dataclass
class BimatrixGameResult:
    status: str
    pure_equilibria: List[NashEquilibrium]
    message: str
