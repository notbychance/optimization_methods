from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from graph_models import Edge, NetworkProblem, Number


class ProblemReader:
    SUPPORTED_PROBLEM_TYPES: Set[str] = {
        'mst',
        'shortest_path',
        'max_flow',
        'min_cost_flow',
        'prewinning_tictactoe_configuration',
        'project_scheduling',
        'critical_path',
    }

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
        if problem_type == 'critical_path':
            problem_type = 'project_scheduling'

        if problem_type not in ProblemReader.SUPPORTED_PROBLEM_TYPES:
            raise ValueError(
                'Поле problem_type должно иметь одно из значений: '
                'mst, shortest_path, max_flow, min_cost_flow, '
                'prewinning_tictactoe_configuration, project_scheduling, critical_path.'
            )

        if problem_type == 'prewinning_tictactoe_configuration':
            return ProblemReader._read_tictactoe_problem(data, problem_type)

        if problem_type == 'project_scheduling':
            return ProblemReader._read_project_scheduling_problem(data, problem_type)

        directed = bool(data.get('directed', problem_type != 'mst'))
        raw_nodes = data.get('nodes')
        raw_edges = data.get('edges')

        if not isinstance(raw_edges, list) or len(raw_edges) == 0:
            raise ValueError('Поле edges должно быть непустым списком ребер/дуг.')

        edges = [ProblemReader._read_edge(raw_edge, directed) for raw_edge in raw_edges]
        nodes = ProblemReader._read_nodes(raw_nodes=raw_nodes, edges=edges)
        node_set = set(nodes)
        ProblemReader._validate_edge_nodes(edges=edges, node_set=node_set)

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
            metadata=ProblemReader._read_metadata(data),
        )

    @staticmethod
    def _read_project_scheduling_problem(data: Dict[str, Any], problem_type: str) -> NetworkProblem:
        raw_edges = data.get('edges')
        if not isinstance(raw_edges, list) or len(raw_edges) == 0:
            raise ValueError('Для project_scheduling поле edges должно быть непустым списком работ.')

        edges = [ProblemReader._read_project_work(raw_edge) for raw_edge in raw_edges]
        nodes = ProblemReader._read_nodes(raw_nodes=data.get('nodes'), edges=edges)
        node_set = set(nodes)
        ProblemReader._validate_edge_nodes(edges=edges, node_set=node_set)

        source = data.get('start_event', data.get('source_event'))
        target = data.get('finish_event', data.get('target_event'))

        if source is None and data.get('source') is not None and str(data.get('source')) in node_set:
            source = data.get('source')
        if target is None and data.get('target') is not None and str(data.get('target')) in node_set:
            target = data.get('target')

        if source is not None:
            source = str(source)
            if source not in node_set:
                raise ValueError('start_event должен входить в список nodes.')
        if target is not None:
            target = str(target)
            if target not in node_set:
                raise ValueError('finish_event должен входить в список nodes.')

        metadata = ProblemReader._read_metadata(data)
        for key in ['schedule_mode', 'mode', 'cost_unit', 'duration_unit']:
            if key in data:
                metadata[key] = data[key]

        return NetworkProblem(
            problem_type=problem_type,
            nodes=nodes,
            edges=edges,
            directed=True,
            source=source,
            target=target,
            metadata=metadata,
        )

    @staticmethod
    def _read_tictactoe_problem(data: Dict[str, Any], problem_type: str) -> NetworkProblem:
        symbols = data.get('symbols')
        if not isinstance(symbols, dict):
            symbols = {}

        first_player_symbol = str(symbols.get('first_player', data.get('first_player_symbol', 'X')))
        second_player_symbol = str(symbols.get('second_player', data.get('second_player_symbol', 'O')))
        empty_cell_symbol = str(symbols.get('empty_cell', data.get('empty_cell_symbol', '.')))

        if len(first_player_symbol) != 1 or len(second_player_symbol) != 1 or len(empty_cell_symbol) != 1:
            raise ValueError('Символы игроков и пустой клетки должны состоять ровно из одного символа.')
        if len({first_player_symbol, second_player_symbol, empty_cell_symbol}) != 3:
            raise ValueError('Символы игроков и пустой клетки должны быть различными.')

        win_length = int(data.get('win_length', 5))
        if win_length <= 0:
            raise ValueError('win_length должен быть положительным целым числом.')

        board = ProblemReader._read_board(
            raw_board=data.get('board'),
            allowed_symbols={first_player_symbol, second_player_symbol, empty_cell_symbol},
        )

        nodes: List[str] = []
        if board is not None:
            nodes = [
                f'({row_index + 1},{column_index + 1})'
                for row_index in range(len(board))
                for column_index in range(len(board[row_index]))
            ]

        return NetworkProblem(
            problem_type=problem_type,
            nodes=nodes,
            edges=[],
            directed=False,
            board=board,
            win_length=win_length,
            first_player_symbol=first_player_symbol,
            second_player_symbol=second_player_symbol,
            empty_cell_symbol=empty_cell_symbol,
            metadata=ProblemReader._read_metadata(data),
        )

    @staticmethod
    def _read_nodes(raw_nodes: Any, edges: List[Edge]) -> List[str]:
        if raw_nodes is None:
            node_set = set()
            for edge in edges:
                node_set.add(edge.start)
                node_set.add(edge.end)
            return sorted(node_set, key=ProblemReader._node_sort_key)

        if not isinstance(raw_nodes, list) or len(raw_nodes) == 0:
            raise ValueError('Поле nodes должно быть непустым списком вершин.')
        return [str(node) for node in raw_nodes]

    @staticmethod
    def _validate_edge_nodes(edges: List[Edge], node_set: Set[str]) -> None:
        for edge in edges:
            if edge.start not in node_set or edge.end not in node_set:
                raise ValueError(f'Ребро {edge.start} -> {edge.end} содержит вершину, отсутствующую в nodes.')

    @staticmethod
    def _read_board(raw_board: Any, allowed_symbols: Set[str]) -> Optional[List[List[str]]]:
        if raw_board is None:
            return None

        if isinstance(raw_board, str):
            prepared = raw_board.strip()
            if prepared == '':
                return None
            if '\n' not in prepared:
                return None
            rows = [line.strip() for line in prepared.splitlines() if line.strip() != '']
            board = [list(row) for row in rows]
        elif isinstance(raw_board, list):
            if len(raw_board) == 0:
                return None
            board = []
            for row in raw_board:
                if isinstance(row, str):
                    board.append(list(row.strip()))
                elif isinstance(row, list):
                    board.append([str(cell) for cell in row])
                else:
                    raise ValueError('Каждая строка board должна быть строкой или списком символов.')
        else:
            raise ValueError('Поле board должно быть строкой, списком строк или списком списков символов.')

        if len(board) == 0:
            return None

        column_count = len(board[0])
        if column_count == 0:
            raise ValueError('Поле board не должно содержать пустые строки.')

        for row_index, row in enumerate(board, start=1):
            if len(row) != column_count:
                raise ValueError('Все строки board должны иметь одинаковую длину.')
            for column_index, cell in enumerate(row, start=1):
                if cell not in allowed_symbols:
                    raise ValueError(
                        f'Недопустимый символ board[{row_index}][{column_index}] = {cell!r}. '
                        f'Разрешены только: {", ".join(sorted(allowed_symbols))}.'
                    )

        return board

    @staticmethod
    def _read_metadata(data: Dict[str, Any]) -> Dict[str, object]:
        metadata_keys = ['source', 'variant_number', 'condition_summary', 'field_size']
        return {key: data[key] for key in metadata_keys if key in data}

    @staticmethod
    def _read_project_work(raw_edge: Dict[str, Any]) -> Edge:
        if not isinstance(raw_edge, dict):
            raise ValueError('Каждая работа должна быть объектом JSON.')

        start = raw_edge.get('from', raw_edge.get('start'))
        end = raw_edge.get('to', raw_edge.get('end'))
        if start is None or end is None:
            raise ValueError('Для каждой работы нужно задать поля from и to.')

        raw_duration = raw_edge.get('duration', raw_edge.get('weight'))
        if raw_duration is None:
            raise ValueError(f'Для работы {start} -> {end} нужно задать duration.')
        duration = ProblemReader._to_number(raw_duration)
        if duration < 0:
            raise ValueError(f'Продолжительность работы {start} -> {end} не может быть отрицательной.')

        raw_cost = raw_edge.get('cost', raw_edge.get('work_cost', 0))
        cost = ProblemReader._to_number(raw_cost)
        if cost < 0:
            raise ValueError(f'Стоимость работы {start} -> {end} не может быть отрицательной.')

        return Edge(
            start=str(start),
            end=str(end),
            weight=duration,
            capacity=0,
            cost=cost,
            directed=True,
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

    @staticmethod
    def _node_sort_key(node: str) -> tuple[int, object]:
        text = str(node)
        if text.isdigit():
            return 0, int(text)
        return 1, text
