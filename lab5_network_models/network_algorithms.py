from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from heapq import heappop, heappush
from typing import Dict, List, Optional, Sequence, Tuple

from graph_models import Edge, NetworkProblem, NetworkResult, Number
from snapshot import SnapshotWriter

INF = 10 ** 18
EPS = 1e-12


class DisjointSetUnion:
    def __init__(self, nodes: Sequence[str]):
        self.parent = {node: node for node in nodes}
        self.rank = {node: 0 for node in nodes}

    def find(self, node: str) -> str:
        if self.parent[node] != node:
            self.parent[node] = self.find(self.parent[node])
        return self.parent[node]

    def union(self, first: str, second: str) -> bool:
        root_first = self.find(first)
        root_second = self.find(second)
        if root_first == root_second:
            return False
        if self.rank[root_first] < self.rank[root_second]:
            root_first, root_second = root_second, root_first
        self.parent[root_second] = root_first
        if self.rank[root_first] == self.rank[root_second]:
            self.rank[root_first] += 1
        return True

    def components(self) -> Dict[str, List[str]]:
        result: Dict[str, List[str]] = {}
        for node in self.parent:
            root = self.find(node)
            result.setdefault(root, []).append(node)
        return result


@dataclass
class ResidualArc:
    start: str
    end: str
    capacity: Number
    cost: Number
    reverse_index: int
    original: bool = True


class NetworkSolver:
    def __init__(self, problem: NetworkProblem, snapshot_writer: Optional[SnapshotWriter] = None):
        self.problem = problem
        self.snapshot_writer = snapshot_writer

    def solve(self) -> NetworkResult:
        if self.problem.problem_type == 'mst':
            return self.minimum_spanning_tree()
        if self.problem.problem_type == 'shortest_path':
            return self.shortest_path()
        if self.problem.problem_type == 'max_flow':
            return self.max_flow()
        if self.problem.problem_type == 'min_cost_flow':
            return self.min_cost_flow()
        if self.problem.problem_type == 'prewinning_tictactoe_configuration':
            return self.prewinning_tictactoe_configuration()
        raise ValueError(f'Неподдерживаемый тип задачи: {self.problem.problem_type}')

    def prewinning_tictactoe_configuration(self) -> NetworkResult:
        board = self.problem.board
        if board is None:
            self._write_table(
                title='Проверка предвыигрышной конфигурации невозможна',
                headers=['Показатель', 'Значение'],
                rows=[
                    ['Причина', 'Во входном файле не задана конкретная матрица поля board.'],
                    ['Ожидаемый формат', 'список строк, например [".....", "..XX.", "....."]'],
                    ['Длина победной цепочки', self.problem.win_length],
                    ['Символ первого игрока', self.problem.first_player_symbol],
                    ['Символ второго игрока', self.problem.second_player_symbol],
                    ['Символ пустой клетки', self.problem.empty_cell_symbol],
                ],
                note='Условие 17-го варианта в методичке описывает общий вид задачи m × n, но не содержит конкретной заполненной матрицы. Поэтому программа корректно завершает запуск и сообщает, какие данные нужно добавить.',
            )
            return NetworkResult(
                status='input_required',
                message='Для 17-го варианта нужно задать конкретное поле board. В методичке указано только общее условие m × n.',
                problem_type='prewinning_tictactoe_configuration',
                total_value=None,
                winning_moves=[],
            )

        self._snapshot_board(
            title='Исходная конфигурация поля',
            board=board,
            note=(
                f'Проверяется, можно ли за один ход получить цепочку длиной {self.problem.win_length}. '
                f'Игроки: {self.problem.first_player_symbol}, {self.problem.second_player_symbol}. '
                f'Пустая клетка: {self.problem.empty_cell_symbol}.'
            ),
        )

        winning_moves: List[Dict[str, object]] = []
        checked_rows: List[List[object]] = []
        players = [self.problem.first_player_symbol, self.problem.second_player_symbol]

        for row_index in range(len(board)):
            for column_index in range(len(board[row_index])):
                if board[row_index][column_index] != self.problem.empty_cell_symbol:
                    continue

                for player_symbol in players:
                    best_direction, best_count, best_cells = self._best_tictactoe_line_after_move(
                        board=board,
                        row_index=row_index,
                        column_index=column_index,
                        player_symbol=player_symbol,
                    )
                    is_winning = best_count >= self.problem.win_length
                    checked_rows.append([
                        row_index + 1,
                        column_index + 1,
                        player_symbol,
                        best_direction,
                        best_count,
                        'да' if is_winning else 'нет',
                    ])

                    if is_winning:
                        move = {
                            'row': row_index + 1,
                            'column': column_index + 1,
                            'symbol': player_symbol,
                            'direction': best_direction,
                            'line_length': best_count,
                            'cells': [(cell_row + 1, cell_column + 1) for cell_row, cell_column in best_cells],
                        }
                        winning_moves.append(move)
                        candidate_board = self._copy_board(board)
                        candidate_board[row_index][column_index] = player_symbol
                        self._snapshot_board(
                            title=f'Найден предвыигрышный ход: {player_symbol} в клетку ({row_index + 1}; {column_index + 1})',
                            board=candidate_board,
                            note=(
                                f'Направление: {best_direction}. '
                                f'Длина полученной цепочки: {best_count}. '
                                f'Клетки цепочки: {self._format_cells(move["cells"])}.'
                            ),
                        )

        if not checked_rows:
            checked_rows.append(['—', '—', '—', '—', '—', 'На поле нет пустых клеток'])

        self._write_table(
            title='Проверенные возможные ходы',
            headers=['Строка', 'Столбец', 'Символ', 'Лучшее направление', 'Максимальная цепочка', 'Победный ход'],
            rows=checked_rows,
        )

        if winning_moves:
            result_rows = [
                [
                    move['symbol'],
                    move['row'],
                    move['column'],
                    move['direction'],
                    move['line_length'],
                    self._format_cells(move['cells']),
                ]
                for move in winning_moves
            ]
            self._write_table(
                title='Итог: конфигурация является предвыигрышной',
                headers=['Символ', 'Строка', 'Столбец', 'Направление', 'Длина цепочки', 'Клетки цепочки'],
                rows=result_rows,
                note='Достаточно одного найденного хода, но программа выводит все обнаруженные предвыигрышные ходы.',
            )
            return NetworkResult(
                status='prewinning',
                message='Конфигурация является предвыигрышной: существует ход, дающий цепочку из пяти одинаковых знаков.',
                problem_type='prewinning_tictactoe_configuration',
                total_value=len(winning_moves),
                winning_moves=winning_moves,
            )

        self._write_table(
            title='Итог: конфигурация не является предвыигрышной',
            headers=['Показатель', 'Значение'],
            rows=[['Количество найденных предвыигрышных ходов', 0]],
            note='Ни один допустимый ход не создает цепочку требуемой длины.',
        )
        return NetworkResult(
            status='not_prewinning',
            message='Конфигурация не является предвыигрышной: за один ход нельзя получить цепочку из пяти одинаковых знаков.',
            problem_type='prewinning_tictactoe_configuration',
            total_value=0,
            winning_moves=[],
        )

    def minimum_spanning_tree(self) -> NetworkResult:
        self._snapshot_graph(
            title='Исходная матрица весов графа',
            value_kind='weight',
            note='Для минимального остовного дерева граф рассматривается как неориентированный.',
            directed=False,
        )

        sorted_edges = sorted(self.problem.edges, key=lambda edge: (edge.weight, edge.start, edge.end))
        rows = []
        for index, edge in enumerate(sorted_edges, start=1):
            rows.append([index, edge.start, edge.end, edge.weight])
        self._write_table('Список ребер после сортировки по весу', ['№', 'Начало', 'Конец', 'Вес'], rows)

        dsu = DisjointSetUnion(self.problem.nodes)
        selected_edges: List[Edge] = []
        total_weight: Number = 0

        for step, edge in enumerate(sorted_edges, start=1):
            accepted = dsu.union(edge.start, edge.end)
            if accepted:
                selected_edges.append(edge)
                total_weight += edge.weight
                action = 'ребро добавлено в остов'
            else:
                action = 'ребро отклонено, так как образует цикл'

            components = dsu.components()
            component_text = '; '.join(
                f'{root}: {", ".join(sorted(nodes))}'
                for root, nodes in sorted(components.items())
            )
            selected_text = ', '.join(f'{selected.start}-{selected.end}' for selected in selected_edges) or 'пока нет'
            self._write_table(
                title=f'Краскал. Шаг {step}',
                headers=['Проверяемое ребро', 'Вес', 'Действие', 'Текущий остов', 'Компоненты связности'],
                rows=[[f'{edge.start}-{edge.end}', edge.weight, action, selected_text, component_text]],
            )

            if len(selected_edges) == len(self.problem.nodes) - 1:
                break

        if len(selected_edges) != len(self.problem.nodes) - 1:
            return NetworkResult(
                status='disconnected',
                message='Минимальное остовное дерево не построено: граф несвязный.',
                problem_type='mst',
                total_value=None,
                selected_edges=selected_edges,
            )

        self._write_table(
            title='Итоговое минимальное остовное дерево',
            headers=['Начало', 'Конец', 'Вес'],
            rows=[[edge.start, edge.end, edge.weight] for edge in selected_edges],
            note=f'Суммарный вес остовного дерева: {total_weight}.',
        )

        return NetworkResult(
            status='optimal',
            message='Минимальное остовное дерево построено алгоритмом Краскала.',
            problem_type='mst',
            total_value=total_weight,
            selected_edges=selected_edges,
        )

    def shortest_path(self) -> NetworkResult:
        source = self._required_source()
        target = self._required_target()
        self._ensure_nonnegative_weights()
        adjacency = self._build_weight_adjacency()

        self._snapshot_graph(
            title='Исходная матрица длин дуг',
            value_kind='weight',
            note='Алгоритм Дейкстры используется для графа с неотрицательными весами.',
            directed=self.problem.directed,
        )

        distances = {node: INF for node in self.problem.nodes}
        previous: Dict[str, Optional[str]] = {node: None for node in self.problem.nodes}
        visited = {node: False for node in self.problem.nodes}
        distances[source] = 0
        heap: List[Tuple[Number, str]] = [(0, source)]
        iteration = 0

        self._snapshot_distances(
            title='Дейкстра. Исходные метки расстояний',
            distances=distances,
            previous=previous,
            visited=visited,
        )

        while heap:
            current_distance, current_node = heappop(heap)
            if visited[current_node]:
                continue
            visited[current_node] = True
            iteration += 1

            relax_rows = []
            for neighbor, weight in adjacency.get(current_node, []):
                if visited[neighbor]:
                    relax_rows.append([current_node, neighbor, weight, self._format_number(distances[neighbor]), 'не изменено: вершина уже обработана'])
                    continue
                candidate = current_distance + weight
                if candidate < distances[neighbor]:
                    old_distance = distances[neighbor]
                    distances[neighbor] = candidate
                    previous[neighbor] = current_node
                    heappush(heap, (candidate, neighbor))
                    relax_rows.append([
                        current_node,
                        neighbor,
                        weight,
                        self._format_number(old_distance),
                        f'обновлено до {self._format_number(candidate)}',
                    ])
                else:
                    relax_rows.append([
                        current_node,
                        neighbor,
                        weight,
                        self._format_number(distances[neighbor]),
                        'не изменено',
                    ])

            if not relax_rows:
                relax_rows.append([current_node, '—', '—', '—', 'нет исходящих непосещенных дуг'])

            self._write_table(
                title=f'Дейкстра. Итерация {iteration}: выбрана вершина {current_node}',
                headers=['Откуда', 'Куда', 'Длина дуги', 'Старая метка', 'Результат'],
                rows=relax_rows,
            )
            self._snapshot_distances(
                title=f'Дейкстра. Метки после итерации {iteration}',
                distances=distances,
                previous=previous,
                visited=visited,
            )

            if current_node == target:
                break

        if distances[target] >= INF:
            return NetworkResult(
                status='unreachable',
                message=f'Путь из {source} в {target} не существует.',
                problem_type='shortest_path',
                total_value=None,
                path=None,
                distances=distances,
            )

        path = self._restore_path(previous, source, target)
        self._write_table(
            title='Итоговый кратчайший путь',
            headers=['Показатель', 'Значение'],
            rows=[
                ['Маршрут', ' -> '.join(path)],
                ['Длина маршрута', distances[target]],
            ],
        )

        return NetworkResult(
            status='optimal',
            message='Кратчайший путь найден алгоритмом Дейкстры.',
            problem_type='shortest_path',
            total_value=distances[target],
            path=path,
            distances=distances,
        )

    def max_flow(self) -> NetworkResult:
        source = self._required_source()
        target = self._required_target()
        residual = self._build_capacity_residual()
        total_flow: Number = 0
        flows: Dict[Tuple[str, str], Number] = {}

        self._snapshot_graph(
            title='Исходная матрица пропускных способностей',
            value_kind='capacity',
            note='Максимальный поток находится алгоритмом Форда-Фалкерсона в реализации Эдмондса-Карпа.',
            directed=True,
        )

        iteration = 0
        while True:
            parent = self._find_augmenting_path_bfs(residual, source, target)
            if target not in parent:
                break

            path_edges = self._extract_residual_path(residual, parent, source, target)
            bottleneck = min(edge.capacity for edge in path_edges)
            path_nodes = [source] + [edge.end for edge in path_edges]

            for edge in path_edges:
                reverse_edge = residual[edge.end][edge.reverse_index]
                edge.capacity -= bottleneck
                reverse_edge.capacity += bottleneck
                if edge.original:
                    flows[(edge.start, edge.end)] = flows.get((edge.start, edge.end), 0) + bottleneck
                else:
                    flows[(edge.end, edge.start)] = flows.get((edge.end, edge.start), 0) - bottleneck

            total_flow += bottleneck
            iteration += 1

            self._write_table(
                title=f'Максимальный поток. Увеличивающий путь {iteration}',
                headers=['Путь', 'Минимальная остаточная пропускная способность', 'Текущий поток'],
                rows=[[' -> '.join(path_nodes), bottleneck, total_flow]],
            )
            self._snapshot_flow_matrix(
                title=f'Максимальный поток. Матрица потока после итерации {iteration}',
                flows=flows,
            )
            self._snapshot_residual_capacity(
                title=f'Максимальный поток. Остаточная сеть после итерации {iteration}',
                residual=residual,
            )

        self._write_table(
            title='Итоговый максимальный поток',
            headers=['Показатель', 'Значение'],
            rows=[['Максимальный поток', total_flow]],
            note='Увеличивающих путей в остаточной сети больше нет.',
        )

        return NetworkResult(
            status='optimal',
            message='Максимальный поток найден алгоритмом Эдмондса-Карпа.',
            problem_type='max_flow',
            total_value=total_flow,
            flows=flows,
        )

    def min_cost_flow(self) -> NetworkResult:
        source = self._required_source()
        target = self._required_target()
        residual = self._build_cost_residual()
        desired_flow = self.problem.desired_flow
        total_flow: Number = 0
        total_cost: Number = 0
        flows: Dict[Tuple[str, str], Number] = {}

        self._snapshot_graph(
            title='Исходная матрица пропускных способностей',
            value_kind='capacity',
            note='Для потока наименьшей стоимости учитываются пропускные способности и стоимости дуг.',
            directed=True,
        )
        self._snapshot_graph(
            title='Исходная матрица стоимостей дуг',
            value_kind='cost',
            note='На каждой итерации выбирается кратчайший по стоимости увеличивающий путь в остаточной сети.',
            directed=True,
        )

        iteration = 0
        while desired_flow is None or total_flow < desired_flow:
            parent, distance = self._find_min_cost_path_spfa(residual, source)
            if target not in parent:
                break

            path_edges = self._extract_residual_path(residual, parent, source, target)
            bottleneck = min(edge.capacity for edge in path_edges)
            if desired_flow is not None:
                bottleneck = min(bottleneck, desired_flow - total_flow)
            if bottleneck <= 0:
                break

            path_nodes = [source] + [edge.end for edge in path_edges]
            path_cost = sum(edge.cost for edge in path_edges)

            for edge in path_edges:
                reverse_edge = residual[edge.end][edge.reverse_index]
                edge.capacity -= bottleneck
                reverse_edge.capacity += bottleneck
                if edge.original:
                    flows[(edge.start, edge.end)] = flows.get((edge.start, edge.end), 0) + bottleneck
                else:
                    flows[(edge.end, edge.start)] = flows.get((edge.end, edge.start), 0) - bottleneck

            total_flow += bottleneck
            total_cost += bottleneck * path_cost
            iteration += 1

            distance_rows = [[node, self._format_number(distance.get(node, INF))] for node in self.problem.nodes]
            self._write_table(
                title=f'Поток наименьшей стоимости. Метки кратчайших стоимостей на итерации {iteration}',
                headers=['Вершина', 'Метка стоимости от источника'],
                rows=distance_rows,
            )
            self._write_table(
                title=f'Поток наименьшей стоимости. Увеличивающий путь {iteration}',
                headers=['Путь', 'Стоимость единицы потока по пути', 'Добавленный поток', 'Общий поток', 'Общая стоимость'],
                rows=[[' -> '.join(path_nodes), path_cost, bottleneck, total_flow, total_cost]],
            )
            self._snapshot_flow_matrix(
                title=f'Поток наименьшей стоимости. Матрица потока после итерации {iteration}',
                flows=flows,
            )
            self._snapshot_residual_capacity(
                title=f'Поток наименьшей стоимости. Остаточная сеть после итерации {iteration}',
                residual=residual,
            )

        if desired_flow is not None and total_flow < desired_flow:
            return NetworkResult(
                status='infeasible',
                message=f'Невозможно отправить требуемый поток {desired_flow}. Достигнут поток {total_flow}.',
                problem_type='min_cost_flow',
                total_value=total_cost,
                flows=flows,
            )

        self._write_table(
            title='Итоговый поток наименьшей стоимости',
            headers=['Показатель', 'Значение'],
            rows=[
                ['Итоговый поток', total_flow],
                ['Минимальная стоимость', total_cost],
            ],
        )

        return NetworkResult(
            status='optimal',
            message='Поток наименьшей стоимости найден методом последовательного выбора кратчайших увеличивающих путей.',
            problem_type='min_cost_flow',
            total_value=total_cost,
            flows=flows,
        )

    def _best_tictactoe_line_after_move(
        self,
        board: List[List[str]],
        row_index: int,
        column_index: int,
        player_symbol: str,
    ) -> Tuple[str, int, List[Tuple[int, int]]]:
        directions = [
            ('горизонталь', 0, 1),
            ('вертикаль', 1, 0),
            ('главная диагональ', 1, 1),
            ('побочная диагональ', 1, -1),
        ]
        best_direction = '—'
        best_count = 0
        best_cells: List[Tuple[int, int]] = []

        for direction_name, row_delta, column_delta in directions:
            cells = [(row_index, column_index)]
            cells.extend(
                self._collect_same_symbol_cells(
                    board=board,
                    row_index=row_index,
                    column_index=column_index,
                    row_delta=row_delta,
                    column_delta=column_delta,
                    player_symbol=player_symbol,
                )
            )
            cells.extend(
                self._collect_same_symbol_cells(
                    board=board,
                    row_index=row_index,
                    column_index=column_index,
                    row_delta=-row_delta,
                    column_delta=-column_delta,
                    player_symbol=player_symbol,
                )
            )
            cells.sort()
            if len(cells) > best_count:
                best_direction = direction_name
                best_count = len(cells)
                best_cells = cells

        return best_direction, best_count, best_cells

    def _collect_same_symbol_cells(
        self,
        board: List[List[str]],
        row_index: int,
        column_index: int,
        row_delta: int,
        column_delta: int,
        player_symbol: str,
    ) -> List[Tuple[int, int]]:
        cells: List[Tuple[int, int]] = []
        current_row = row_index + row_delta
        current_column = column_index + column_delta
        while 0 <= current_row < len(board) and 0 <= current_column < len(board[current_row]):
            if board[current_row][current_column] != player_symbol:
                break
            cells.append((current_row, current_column))
            current_row += row_delta
            current_column += column_delta
        return cells

    def _copy_board(self, board: List[List[str]]) -> List[List[str]]:
        return [row[:] for row in board]

    def _snapshot_board(self, title: str, board: List[List[str]], note: str = '') -> None:
        rows = []
        for row_index, row in enumerate(board, start=1):
            rows.append([row_index] + row)
        headers = ['№'] + [str(column_index) for column_index in range(1, len(board[0]) + 1)]
        self._write_table(title=title, headers=headers, rows=rows, note=note)

    def _format_cells(self, cells: object) -> str:
        if not isinstance(cells, list):
            return str(cells)
        return ', '.join(f'({row}; {column})' for row, column in cells)

    def _build_weight_adjacency(self) -> Dict[str, List[Tuple[str, Number]]]:
        adjacency: Dict[str, List[Tuple[str, Number]]] = {node: [] for node in self.problem.nodes}
        for edge in self.problem.edges:
            adjacency[edge.start].append((edge.end, edge.weight))
            if not self.problem.directed and not edge.directed:
                adjacency[edge.end].append((edge.start, edge.weight))
        return adjacency

    def _build_capacity_residual(self) -> Dict[str, List[ResidualArc]]:
        residual: Dict[str, List[ResidualArc]] = {node: [] for node in self.problem.nodes}
        for edge in self.problem.edges:
            self._add_residual_arc(residual, edge.start, edge.end, edge.capacity, 0, True)
        return residual

    def _build_cost_residual(self) -> Dict[str, List[ResidualArc]]:
        residual: Dict[str, List[ResidualArc]] = {node: [] for node in self.problem.nodes}
        for edge in self.problem.edges:
            self._add_residual_arc(residual, edge.start, edge.end, edge.capacity, edge.cost, True)
        return residual

    def _add_residual_arc(
        self,
        residual: Dict[str, List[ResidualArc]],
        start: str,
        end: str,
        capacity: Number,
        cost: Number,
        original: bool,
    ) -> None:
        if capacity < 0:
            raise ValueError('Пропускная способность дуги не может быть отрицательной.')
        forward_index = len(residual[start])
        reverse_index = len(residual[end])
        forward = ResidualArc(start=start, end=end, capacity=capacity, cost=cost, reverse_index=reverse_index, original=original)
        reverse = ResidualArc(start=end, end=start, capacity=0, cost=-cost, reverse_index=forward_index, original=False)
        residual[start].append(forward)
        residual[end].append(reverse)

    def _find_augmenting_path_bfs(
        self,
        residual: Dict[str, List[ResidualArc]],
        source: str,
        target: str,
    ) -> Dict[str, Tuple[str, int]]:
        parent: Dict[str, Tuple[str, int]] = {}
        visited = {source}
        queue = deque([source])

        while queue:
            current = queue.popleft()
            for index, edge in enumerate(residual[current]):
                if edge.capacity <= EPS or edge.end in visited:
                    continue
                visited.add(edge.end)
                parent[edge.end] = (current, index)
                if edge.end == target:
                    return parent
                queue.append(edge.end)
        return parent

    def _find_min_cost_path_spfa(
        self,
        residual: Dict[str, List[ResidualArc]],
        source: str,
    ) -> Tuple[Dict[str, Tuple[str, int]], Dict[str, Number]]:
        distance = {node: INF for node in self.problem.nodes}
        in_queue = {node: False for node in self.problem.nodes}
        parent: Dict[str, Tuple[str, int]] = {}
        distance[source] = 0
        queue = deque([source])
        in_queue[source] = True

        while queue:
            current = queue.popleft()
            in_queue[current] = False
            for index, edge in enumerate(residual[current]):
                if edge.capacity <= EPS:
                    continue
                candidate = distance[current] + edge.cost
                if candidate < distance[edge.end]:
                    distance[edge.end] = candidate
                    parent[edge.end] = (current, index)
                    if not in_queue[edge.end]:
                        queue.append(edge.end)
                        in_queue[edge.end] = True
        return parent, distance

    def _extract_residual_path(
        self,
        residual: Dict[str, List[ResidualArc]],
        parent: Dict[str, Tuple[str, int]],
        source: str,
        target: str,
    ) -> List[ResidualArc]:
        edges: List[ResidualArc] = []
        current = target
        while current != source:
            if current not in parent:
                raise RuntimeError('Невозможно восстановить увеличивающий путь: отсутствует родительская вершина.')
            previous_node, edge_index = parent[current]
            edge = residual[previous_node][edge_index]
            edges.append(edge)
            current = previous_node
        edges.reverse()
        return edges

    def _restore_path(self, previous: Dict[str, Optional[str]], source: str, target: str) -> List[str]:
        path: List[str] = []
        current: Optional[str] = target
        while current is not None:
            path.append(current)
            if current == source:
                break
            current = previous[current]
        path.reverse()
        return path

    def _required_source(self) -> str:
        if self.problem.source is None:
            raise ValueError('Не задана исходная вершина source.')
        return self.problem.source

    def _required_target(self) -> str:
        if self.problem.target is None:
            raise ValueError('Не задана конечная вершина target.')
        return self.problem.target

    def _ensure_nonnegative_weights(self) -> None:
        for edge in self.problem.edges:
            if edge.weight < 0:
                raise ValueError('Алгоритм Дейкстры допускает только неотрицательные веса дуг.')

    def _snapshot_graph(self, title: str, value_kind: str, note: str, directed: bool) -> None:
        if self.snapshot_writer is None:
            return
        values: Dict[Tuple[str, str], object] = {}
        for edge in self.problem.edges:
            value = getattr(edge, value_kind)
            values[(edge.start, edge.end)] = value
            if not directed and not edge.directed:
                values[(edge.end, edge.start)] = value
        self.snapshot_writer.write_matrix(title=title, nodes=self.problem.nodes, values=values, note=note)

    def _snapshot_distances(
        self,
        title: str,
        distances: Dict[str, Number],
        previous: Dict[str, Optional[str]],
        visited: Dict[str, bool],
    ) -> None:
        rows = []
        for node in self.problem.nodes:
            rows.append([
                node,
                self._format_number(distances[node]),
                previous[node] if previous[node] is not None else '—',
                'да' if visited[node] else 'нет',
            ])
        self._write_table(title=title, headers=['Вершина', 'Метка', 'Предыдущая вершина', 'Обработана'], rows=rows)

    def _snapshot_flow_matrix(self, title: str, flows: Dict[Tuple[str, str], Number]) -> None:
        if self.snapshot_writer is None:
            return
        self.snapshot_writer.write_matrix(title=title, nodes=self.problem.nodes, values=flows, empty='0', diagonal='0')

    def _snapshot_residual_capacity(self, title: str, residual: Dict[str, List[ResidualArc]]) -> None:
        if self.snapshot_writer is None:
            return
        values: Dict[Tuple[str, str], Number] = {}
        for start, edges in residual.items():
            for edge in edges:
                if edge.capacity > EPS:
                    values[(start, edge.end)] = values.get((start, edge.end), 0) + edge.capacity
        self.snapshot_writer.write_matrix(title=title, nodes=self.problem.nodes, values=values, empty='0', diagonal='0')

    def _write_table(self, title: str, headers: Sequence[str], rows: Sequence[Sequence[object]], note: str = '') -> None:
        if self.snapshot_writer is not None:
            self.snapshot_writer.write_table(title=title, headers=headers, rows=rows, note=note)

    def _format_number(self, value: Number) -> str:
        if value >= INF / 2:
            return '∞'
        if isinstance(value, float):
            if value.is_integer():
                return str(int(value))
            return f'{value:.6g}'
        return str(value)
