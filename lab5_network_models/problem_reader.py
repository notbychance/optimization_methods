from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from graph_models import Edge, NetworkProblem, Number


class ProblemReader:
    @staticmethod
    def read(file_path: str) -> NetworkProblem:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f'Файл с условием не найден: {file_path}')
        if path.suffix.lower() != '.json':
            raise ValueError('Поддерживается только формат JSON.')
        data = json.loads(path.read_text(encoding='utf-8'))
        return ProblemReader._from_json(data)

    @staticmethod
    def _from_json(data: Dict[str, Any]) -> NetworkProblem:
        problem_type = str(data.get('problem_type', data.get('type', ''))).strip().lower()
        if problem_type not in {'mst', 'shortest_path', 'max_flow', 'min_cost_flow'}:
            raise ValueError(
                'Поле problem_type должно иметь одно из значений: '
                'mst, shortest_path, max_flow, min_cost_flow.'
            )

        directed = bool(data.get('directed', problem_type != 'mst'))
        raw_nodes = data.get('nodes')
        raw_edges = data.get('edges')

        if not isinstance(raw_edges, list) or len(raw_edges) == 0:
            raise ValueError('Поле edges должно быть непустым списком ребер/дуг.')

        edges = [ProblemReader._read_edge(raw_edge, directed) for raw_edge in raw_edges]

        if raw_nodes is None:
            node_set = set()
            for edge in edges:
                node_set.add(edge.start)
                node_set.add(edge.end)
            nodes = sorted(node_set)
        else:
            if not isinstance(raw_nodes, list) or len(raw_nodes) == 0:
                raise ValueError('Поле nodes должно быть непустым списком вершин.')
            nodes = [str(node) for node in raw_nodes]

        node_set = set(nodes)
        for edge in edges:
            if edge.start not in node_set or edge.end not in node_set:
                raise ValueError(f'Ребро {edge.start} -> {edge.end} содержит вершину, отсутствующую в nodes.')

        source = data.get('source')
        target = data.get('target')
        if source is not None:
            source = str(source)
        if target is not None:
            target = str(target)

        if problem_type in {'shortest_path', 'max_flow', 'min_cost_flow'}:
            if source is None or target is None:
                raise ValueError('Для shortest_path, max_flow и min_cost_flow нужно задать source и target.')
            if source not in node_set or target not in node_set:
                raise ValueError('source и target должны входить в список nodes.')

        desired_flow = data.get('desired_flow')
        if desired_flow is not None:
            desired_flow = ProblemReader._to_number(desired_flow)
            if desired_flow < 0:
                raise ValueError('desired_flow не может быть отрицательным.')

        return NetworkProblem(
            problem_type=problem_type,
            nodes=nodes,
            edges=edges,
            directed=directed,
            source=source,
            target=target,
            desired_flow=desired_flow,
        )

    @staticmethod
    def _read_edge(raw_edge: Dict[str, Any], default_directed: bool) -> Edge:
        if not isinstance(raw_edge, dict):
            raise ValueError('Каждое ребро должно быть объектом JSON.')

        start = raw_edge.get('from', raw_edge.get('start'))
        end = raw_edge.get('to', raw_edge.get('end'))
        if start is None or end is None:
            raise ValueError('Для каждого ребра нужно задать поля from и to.')

        weight = ProblemReader._to_number(raw_edge.get('weight', 1))
        capacity = ProblemReader._to_number(raw_edge.get('capacity', 0))
        cost = ProblemReader._to_number(raw_edge.get('cost', weight))
        directed = bool(raw_edge.get('directed', default_directed))

        return Edge(
            start=str(start),
            end=str(end),
            weight=weight,
            capacity=capacity,
            cost=cost,
            directed=directed,
        )

    @staticmethod
    def _to_number(value: Any) -> Number:
        if isinstance(value, bool):
            raise ValueError(f'Логическое значение не является числом: {value}')
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return value
        if isinstance(value, str):
            prepared_value = value.strip().replace(',', '.')
            if prepared_value == '':
                raise ValueError('Пустая строка не может быть числом.')
            number = float(prepared_value) if '.' in prepared_value else int(prepared_value)
            return number
        raise ValueError(f'Невозможно преобразовать значение в число: {value}')
