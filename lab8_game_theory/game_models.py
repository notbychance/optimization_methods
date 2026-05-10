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


@dataclass
class PreventiveMaintenanceProblem:
    fleet_size: int
    failure_probability_by_month: Dict[int, Fraction]
    later_failure_probability: Fraction
    random_failure_cost: Fraction
    preventive_repair_cost: Fraction
    max_cycle_months: int
    source: Optional[str] = None
    condition_summary: Optional[str] = None


@dataclass
class PreventiveMaintenanceCycleRow:
    cycle_months: int
    expected_cycle_cost_per_vehicle: Fraction
    expected_cycle_length_months: Fraction
    average_cost_per_vehicle_per_month: Fraction
    expected_cycle_cost_for_fleet: Fraction
    average_cost_for_fleet_per_month: Fraction
    survival_probability_to_preventive_repair: Fraction
    failure_probability_before_preventive_repair: Fraction


@dataclass
class PreventiveMaintenanceMonthRow:
    month: int
    conditional_failure_probability: Fraction
    survival_probability_before_month: Fraction
    unconditional_failure_probability: Fraction
    survival_probability_after_month: Fraction
    expected_failure_cost_per_vehicle: Fraction
    expected_duration_contribution: Fraction


@dataclass
class PreventiveMaintenanceResult:
    status: str
    optimal_cycle_months: Optional[int]
    minimal_average_cost_per_vehicle_per_month: Optional[Fraction]
    minimal_average_cost_for_fleet_per_month: Optional[Fraction]
    cycle_rows: List[PreventiveMaintenanceCycleRow]
    optimal_month_rows: List[PreventiveMaintenanceMonthRow]
    message: str
