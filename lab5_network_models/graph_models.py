from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

Number = Union[int, float]


@dataclass(frozen=True)
class Edge:
    start: str
    end: str
    weight: Number = 1
    capacity: Number = 0
    cost: Number = 0
    directed: bool = False


@dataclass
class NetworkProblem:
    problem_type: str
    nodes: List[str]
    edges: List[Edge]
    directed: bool = False
    source: Optional[str] = None
    target: Optional[str] = None
    desired_flow: Optional[Number] = None
    board: Optional[List[List[str]]] = None
    win_length: int = 5
    first_player_symbol: str = 'X'
    second_player_symbol: str = 'O'
    empty_cell_symbol: str = '.'
    metadata: Dict[str, object] = field(default_factory=dict)


@dataclass
class NetworkResult:
    status: str
    message: str
    problem_type: str
    total_value: Optional[Number] = None
    path: Optional[List[str]] = None
    selected_edges: Optional[List[Edge]] = None
    flows: Optional[Dict[Tuple[str, str], Number]] = None
    distances: Optional[Dict[str, Number]] = None
    winning_moves: Optional[List[Dict[str, object]]] = None
    event_early_times: Optional[Dict[str, Number]] = None
    event_late_times: Optional[Dict[str, Number]] = None
    work_reserves: Optional[Dict[Tuple[str, str], Number]] = None
    details: Dict[str, object] = field(default_factory=dict)
