from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Optional, Set, Tuple

from snapshot import SnapshotWriter


Cell = Tuple[int, int]
Node = Tuple[str, int]


@dataclass
class TransportationProblem:
    costs: List[List[Fraction]]
    supply: List[Fraction]
    demand: List[Fraction]
    source_names: Optional[List[str]] = None
    destination_names: Optional[List[str]] = None
    initial_method: str = "north_west"


@dataclass
class TransportationResult:
    status: str
    total_cost: Optional[Fraction]
    allocations: List[List[Fraction]]
    iterations: int
    message: str
    source_names: List[str]
    destination_names: List[str]
    original_source_count: int
    original_destination_count: int


class TransportationSolver:
    def __init__(self, problem: TransportationProblem, snapshot_writer: Optional[SnapshotWriter] = None):
        self.problem = problem
        self.snapshot_writer = snapshot_writer
        self.iterations = 0
        self.original_source_count = len(problem.supply)
        self.original_destination_count = len(problem.demand)

    def solve(self) -> TransportationResult:
        self._validate_problem()

        costs, supply, demand, source_names, destination_names = self._balanced_problem()

        self._snapshot_problem(
            title="Исходная сбалансированная транспортная задача",
            costs=costs,
            supply=supply,
            demand=demand,
            source_names=source_names,
            destination_names=destination_names,
            notes="Если суммарное предложение и суммарный спрос отличались, добавлен фиктивный пункт с нулевыми тарифами.",
        )

        allocations, basis = self._build_initial_solution(
            costs=costs,
            supply=supply,
            demand=demand,
            method=self.problem.initial_method,
        )
        self._complete_degenerate_basis(basis=basis, row_count=len(supply), column_count=len(demand))

        self._snapshot_solution(
            title="Начальный опорный план",
            costs=costs,
            allocations=allocations,
            basis=basis,
            source_names=source_names,
            destination_names=destination_names,
            notes=f"Начальный план построен методом: {self._method_title(self.problem.initial_method)}.",
            potentials=None,
            deltas=None,
            cycle=None,
            theta=None,
        )

        while True:
            potentials = self._calculate_potentials(costs=costs, basis=basis)
            deltas = self._calculate_reduced_costs(costs=costs, basis=basis, potentials=potentials)
            entering_cell = self._choose_entering_cell(deltas=deltas, basis=basis)

            self._snapshot_solution(
                title=f"Проверка оптимальности. Итерация {self.iterations}",
                costs=costs,
                allocations=allocations,
                basis=basis,
                source_names=source_names,
                destination_names=destination_names,
                notes=(
                    "Построены потенциалы u_i и v_j. Для свободных клеток рассчитаны оценки "
                    "delta_ij = c_ij - u_i - v_j."
                ),
                potentials=potentials,
                deltas=deltas,
                cycle=None,
                theta=None,
            )

            if entering_cell is None:
                total_cost = self._calculate_total_cost(costs=costs, allocations=allocations)
                self._snapshot_solution(
                    title="Итоговый оптимальный план",
                    costs=costs,
                    allocations=allocations,
                    basis=basis,
                    source_names=source_names,
                    destination_names=destination_names,
                    notes=f"Все оценки свободных клеток неотрицательны. Минимальная стоимость: {self.format_fraction(total_cost)}.",
                    potentials=potentials,
                    deltas=deltas,
                    cycle=None,
                    theta=None,
                )
                return TransportationResult(
                    status="optimal",
                    total_cost=total_cost,
                    allocations=allocations,
                    iterations=self.iterations,
                    message="Оптимальный транспортный план найден методом потенциалов.",
                    source_names=source_names,
                    destination_names=destination_names,
                    original_source_count=self.original_source_count,
                    original_destination_count=self.original_destination_count,
                )

            cycle = self._find_cycle(basis=basis, entering_cell=entering_cell)
            theta = self._calculate_theta(allocations=allocations, cycle=cycle)

            self._snapshot_solution(
                title=f"Выбор свободной клетки и построение цикла. Итерация {self.iterations + 1}",
                costs=costs,
                allocations=allocations,
                basis=basis,
                source_names=source_names,
                destination_names=destination_names,
                notes=(
                    f"В план вводится клетка {self._cell_name(entering_cell, source_names, destination_names)}. "
                    f"По отрицательным вершинам цикла найдено theta = {self.format_fraction(theta)}."
                ),
                potentials=potentials,
                deltas=deltas,
                cycle=cycle,
                theta=theta,
            )

            self._apply_cycle_shift(allocations=allocations, basis=basis, entering_cell=entering_cell, cycle=cycle, theta=theta)
            self.iterations += 1

            self._snapshot_solution(
                title=f"План после перераспределения. Итерация {self.iterations}",
                costs=costs,
                allocations=allocations,
                basis=basis,
                source_names=source_names,
                destination_names=destination_names,
                notes="Количество theta прибавлено в положительных вершинах цикла и вычтено в отрицательных вершинах.",
                potentials=None,
                deltas=None,
                cycle=None,
                theta=None,
            )

    def _validate_problem(self) -> None:
        if len(self.problem.costs) == 0:
            raise ValueError("Матрица тарифов не должна быть пустой.")

        row_length = len(self.problem.costs[0])
        if row_length == 0:
            raise ValueError("Матрица тарифов должна содержать хотя бы один столбец.")

        for row_index, row in enumerate(self.problem.costs, start=1):
            if len(row) != row_length:
                raise ValueError(f"Строка {row_index} матрицы тарифов имеет некорректную длину.")

        if len(self.problem.supply) != len(self.problem.costs):
            raise ValueError("Количество запасов должно совпадать с количеством строк матрицы тарифов.")

        if len(self.problem.demand) != row_length:
            raise ValueError("Количество потребностей должно совпадать с количеством столбцов матрицы тарифов.")

        for index, value in enumerate(self.problem.supply, start=1):
            if value < 0:
                raise ValueError(f"Запас поставщика {index} не может быть отрицательным.")

        for index, value in enumerate(self.problem.demand, start=1):
            if value < 0:
                raise ValueError(f"Потребность потребителя {index} не может быть отрицательной.")

        if sum(self.problem.supply) == 0 or sum(self.problem.demand) == 0:
            raise ValueError("Суммарный запас и суммарная потребность должны быть положительными.")

        if self.problem.source_names is not None and len(self.problem.source_names) != len(self.problem.supply):
            raise ValueError("Количество имен поставщиков должно совпадать с количеством запасов.")

        if self.problem.destination_names is not None and len(self.problem.destination_names) != len(self.problem.demand):
            raise ValueError("Количество имен потребителей должно совпадать с количеством потребностей.")

        if self.problem.initial_method.lower() not in {"north_west", "least_cost", "vogel"}:
            raise ValueError("Метод начального плана должен быть north_west, least_cost или vogel.")

    def _balanced_problem(self) -> Tuple[List[List[Fraction]], List[Fraction], List[Fraction], List[str], List[str]]:
        costs = [row[:] for row in self.problem.costs]
        supply = self.problem.supply[:]
        demand = self.problem.demand[:]
        source_names = (
            self.problem.source_names[:]
            if self.problem.source_names is not None
            else [f"A{i + 1}" for i in range(len(supply))]
        )
        destination_names = (
            self.problem.destination_names[:]
            if self.problem.destination_names is not None
            else [f"B{j + 1}" for j in range(len(demand))]
        )

        total_supply = sum(supply)
        total_demand = sum(demand)

        if total_supply > total_demand:
            additional_demand = total_supply - total_demand
            demand.append(additional_demand)
            destination_names.append("Фиктивный потребитель")
            for row in costs:
                row.append(Fraction(0))
        elif total_demand > total_supply:
            additional_supply = total_demand - total_supply
            supply.append(additional_supply)
            source_names.append("Фиктивный поставщик")
            costs.append([Fraction(0) for _ in demand])

        return costs, supply, demand, source_names, destination_names

    def _build_initial_solution(
        self,
        costs: List[List[Fraction]],
        supply: List[Fraction],
        demand: List[Fraction],
        method: str,
    ) -> Tuple[List[List[Fraction]], Set[Cell]]:
        normalized_method = method.lower()

        if normalized_method == "north_west":
            return self._north_west_solution(supply=supply, demand=demand)
        if normalized_method == "least_cost":
            return self._least_cost_solution(costs=costs, supply=supply, demand=demand)
        if normalized_method == "vogel":
            return self._vogel_solution(costs=costs, supply=supply, demand=demand)

        raise ValueError(f"Неизвестный метод построения начального плана: {method}")

    def _north_west_solution(self, supply: List[Fraction], demand: List[Fraction]) -> Tuple[List[List[Fraction]], Set[Cell]]:
        row_count = len(supply)
        column_count = len(demand)
        allocations = self._empty_allocations(row_count=row_count, column_count=column_count)
        basis: Set[Cell] = set()
        supply_left = supply[:]
        demand_left = demand[:]

        row_index = 0
        column_index = 0

        while row_index < row_count and column_index < column_count:
            value = min(supply_left[row_index], demand_left[column_index])
            allocations[row_index][column_index] = value
            basis.add((row_index, column_index))
            supply_left[row_index] -= value
            demand_left[column_index] -= value

            if supply_left[row_index] == 0 and demand_left[column_index] == 0:
                row_index += 1
                column_index += 1
            elif supply_left[row_index] == 0:
                row_index += 1
            else:
                column_index += 1

        return allocations, basis

    def _least_cost_solution(
        self,
        costs: List[List[Fraction]],
        supply: List[Fraction],
        demand: List[Fraction],
    ) -> Tuple[List[List[Fraction]], Set[Cell]]:
        row_count = len(supply)
        column_count = len(demand)
        allocations = self._empty_allocations(row_count=row_count, column_count=column_count)
        basis: Set[Cell] = set()
        supply_left = supply[:]
        demand_left = demand[:]
        active_rows = {row_index for row_index in range(row_count) if supply_left[row_index] > 0}
        active_columns = {column_index for column_index in range(column_count) if demand_left[column_index] > 0}

        while len(active_rows) > 0 and len(active_columns) > 0:
            best_cell: Optional[Cell] = None
            best_cost: Optional[Fraction] = None

            for row_index in active_rows:
                for column_index in active_columns:
                    current_cost = costs[row_index][column_index]
                    if best_cost is None or current_cost < best_cost:
                        best_cost = current_cost
                        best_cell = (row_index, column_index)

            if best_cell is None:
                break

            row_index, column_index = best_cell
            value = min(supply_left[row_index], demand_left[column_index])
            allocations[row_index][column_index] = value
            basis.add((row_index, column_index))
            supply_left[row_index] -= value
            demand_left[column_index] -= value

            if supply_left[row_index] == 0:
                active_rows.discard(row_index)
            if demand_left[column_index] == 0:
                active_columns.discard(column_index)

        return allocations, basis

    def _vogel_solution(
        self,
        costs: List[List[Fraction]],
        supply: List[Fraction],
        demand: List[Fraction],
    ) -> Tuple[List[List[Fraction]], Set[Cell]]:
        row_count = len(supply)
        column_count = len(demand)
        allocations = self._empty_allocations(row_count=row_count, column_count=column_count)
        basis: Set[Cell] = set()
        supply_left = supply[:]
        demand_left = demand[:]
        active_rows = {row_index for row_index in range(row_count) if supply_left[row_index] > 0}
        active_columns = {column_index for column_index in range(column_count) if demand_left[column_index] > 0}

        while len(active_rows) > 0 and len(active_columns) > 0:
            best_penalty: Optional[Fraction] = None
            best_type: Optional[str] = None
            best_index: Optional[int] = None

            for row_index in active_rows:
                row_costs = [costs[row_index][column_index] for column_index in active_columns]
                penalty = self._penalty(row_costs)
                if best_penalty is None or penalty > best_penalty:
                    best_penalty = penalty
                    best_type = "row"
                    best_index = row_index

            for column_index in active_columns:
                column_costs = [costs[row_index][column_index] for row_index in active_rows]
                penalty = self._penalty(column_costs)
                if best_penalty is None or penalty > best_penalty:
                    best_penalty = penalty
                    best_type = "column"
                    best_index = column_index

            if best_type is None or best_index is None:
                break

            if best_type == "row":
                row_index = best_index
                column_index = min(active_columns, key=lambda current_column: costs[row_index][current_column])
            else:
                column_index = best_index
                row_index = min(active_rows, key=lambda current_row: costs[current_row][column_index])

            value = min(supply_left[row_index], demand_left[column_index])
            allocations[row_index][column_index] = value
            basis.add((row_index, column_index))
            supply_left[row_index] -= value
            demand_left[column_index] -= value

            if supply_left[row_index] == 0:
                active_rows.discard(row_index)
            if demand_left[column_index] == 0:
                active_columns.discard(column_index)

        return allocations, basis

    def _penalty(self, values: List[Fraction]) -> Fraction:
        if len(values) == 0:
            return Fraction(0)
        if len(values) == 1:
            return values[0]
        sorted_values = sorted(values)
        return sorted_values[1] - sorted_values[0]

    def _complete_degenerate_basis(self, basis: Set[Cell], row_count: int, column_count: int) -> None:
        required_basis_size = row_count + column_count - 1

        while len(basis) < required_basis_size:
            added = False
            for row_index in range(row_count):
                if added:
                    break
                for column_index in range(column_count):
                    cell = (row_index, column_index)
                    if cell in basis:
                        continue
                    if not self._basis_has_cycle_with_added_cell(basis=basis, new_cell=cell):
                        basis.add(cell)
                        added = True
                        break

            if not added:
                raise ValueError("Не удалось дополнить вырожденный план нулевыми базисными клетками.")

    def _basis_has_cycle_with_added_cell(self, basis: Set[Cell], new_cell: Cell) -> bool:
        graph = self._build_graph(basis)
        start_node: Node = ("r", new_cell[0])
        finish_node: Node = ("c", new_cell[1])
        return self._path_exists(graph=graph, start_node=start_node, finish_node=finish_node)

    def _path_exists(self, graph: Dict[Node, List[Node]], start_node: Node, finish_node: Node) -> bool:
        stack = [start_node]
        visited: Set[Node] = set()

        while stack:
            node = stack.pop()
            if node == finish_node:
                return True
            if node in visited:
                continue
            visited.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    stack.append(neighbor)

        return False

    def _calculate_potentials(self, costs: List[List[Fraction]], basis: Set[Cell]) -> Tuple[List[Fraction], List[Fraction]]:
        row_count = len(costs)
        column_count = len(costs[0])
        u: List[Optional[Fraction]] = [None for _ in range(row_count)]
        v: List[Optional[Fraction]] = [None for _ in range(column_count)]
        u[0] = Fraction(0)

        changed = True
        while changed:
            changed = False
            for row_index, column_index in basis:
                if u[row_index] is not None and v[column_index] is None:
                    v[column_index] = costs[row_index][column_index] - u[row_index]
                    changed = True
                elif v[column_index] is not None and u[row_index] is None:
                    u[row_index] = costs[row_index][column_index] - v[column_index]
                    changed = True

        if any(value is None for value in u) or any(value is None for value in v):
            raise ValueError("Не удалось вычислить потенциалы: базис не образует связное дерево.")

        return [value for value in u if value is not None], [value for value in v if value is not None]

    def _calculate_reduced_costs(
        self,
        costs: List[List[Fraction]],
        basis: Set[Cell],
        potentials: Tuple[List[Fraction], List[Fraction]],
    ) -> List[List[Optional[Fraction]]]:
        u, v = potentials
        deltas: List[List[Optional[Fraction]]] = []

        for row_index, row in enumerate(costs):
            delta_row: List[Optional[Fraction]] = []
            for column_index, cost in enumerate(row):
                if (row_index, column_index) in basis:
                    delta_row.append(None)
                else:
                    delta_row.append(cost - u[row_index] - v[column_index])
            deltas.append(delta_row)

        return deltas

    def _choose_entering_cell(self, deltas: List[List[Optional[Fraction]]], basis: Set[Cell]) -> Optional[Cell]:
        best_cell: Optional[Cell] = None
        best_delta = Fraction(0)

        for row_index, row in enumerate(deltas):
            for column_index, delta in enumerate(row):
                if (row_index, column_index) in basis or delta is None:
                    continue
                if delta < best_delta:
                    best_delta = delta
                    best_cell = (row_index, column_index)

        return best_cell

    def _find_cycle(self, basis: Set[Cell], entering_cell: Cell) -> List[Cell]:
        graph = self._build_graph(basis)
        start_node: Node = ("c", entering_cell[1])
        finish_node: Node = ("r", entering_cell[0])
        path_nodes = self._find_path(graph=graph, start_node=start_node, finish_node=finish_node)

        if path_nodes is None:
            raise ValueError("Не удалось построить цикл перераспределения.")

        cycle = [entering_cell]
        for node_index in range(len(path_nodes) - 1):
            first_node = path_nodes[node_index]
            second_node = path_nodes[node_index + 1]
            cycle.append(self._nodes_to_cell(first_node, second_node))

        if len(cycle) < 4 or len(cycle) % 2 != 0:
            raise ValueError("Построенный цикл имеет некорректную структуру.")

        return cycle

    def _find_path(self, graph: Dict[Node, List[Node]], start_node: Node, finish_node: Node) -> Optional[List[Node]]:
        stack: List[Tuple[Node, List[Node]]] = [(start_node, [start_node])]
        visited: Set[Node] = set()

        while stack:
            node, path = stack.pop()
            if node == finish_node:
                return path
            if node in visited:
                continue
            visited.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    stack.append((neighbor, path + [neighbor]))

        return None

    def _nodes_to_cell(self, first_node: Node, second_node: Node) -> Cell:
        if first_node[0] == "r" and second_node[0] == "c":
            return first_node[1], second_node[1]
        if first_node[0] == "c" and second_node[0] == "r":
            return second_node[1], first_node[1]
        raise ValueError("Соседние узлы цикла не соответствуют транспортной клетке.")

    def _calculate_theta(self, allocations: List[List[Fraction]], cycle: List[Cell]) -> Fraction:
        negative_cells = [cycle[index] for index in range(1, len(cycle), 2)]
        values = [allocations[row_index][column_index] for row_index, column_index in negative_cells]
        return min(values)

    def _apply_cycle_shift(
        self,
        allocations: List[List[Fraction]],
        basis: Set[Cell],
        entering_cell: Cell,
        cycle: List[Cell],
        theta: Fraction,
    ) -> None:
        basis.add(entering_cell)
        leaving_cell: Optional[Cell] = None

        for index, (row_index, column_index) in enumerate(cycle):
            if index % 2 == 0:
                allocations[row_index][column_index] += theta
            else:
                allocations[row_index][column_index] -= theta
                if allocations[row_index][column_index] == 0 and leaving_cell is None:
                    leaving_cell = (row_index, column_index)

        if leaving_cell is None:
            raise ValueError("Не удалось выбрать клетку, выводимую из базиса.")

        basis.remove(leaving_cell)

    def _build_graph(self, basis: Set[Cell]) -> Dict[Node, List[Node]]:
        graph: Dict[Node, List[Node]] = {}

        for row_index, column_index in basis:
            row_node: Node = ("r", row_index)
            column_node: Node = ("c", column_index)
            graph.setdefault(row_node, []).append(column_node)
            graph.setdefault(column_node, []).append(row_node)

        return graph

    def _calculate_total_cost(self, costs: List[List[Fraction]], allocations: List[List[Fraction]]) -> Fraction:
        total = Fraction(0)
        for row_index, row in enumerate(costs):
            for column_index, cost in enumerate(row):
                total += cost * allocations[row_index][column_index]
        return total

    def _empty_allocations(self, row_count: int, column_count: int) -> List[List[Fraction]]:
        return [[Fraction(0) for _ in range(column_count)] for _ in range(row_count)]

    def _snapshot_problem(
        self,
        title: str,
        costs: List[List[Fraction]],
        supply: List[Fraction],
        demand: List[Fraction],
        source_names: List[str],
        destination_names: List[str],
        notes: str,
    ) -> None:
        if self.snapshot_writer is None:
            return
        self.snapshot_writer.write_problem(
            title=title,
            costs=costs,
            supply=supply,
            demand=demand,
            source_names=source_names,
            destination_names=destination_names,
            notes=notes,
        )

    def _snapshot_solution(
        self,
        title: str,
        costs: List[List[Fraction]],
        allocations: List[List[Fraction]],
        basis: Set[Cell],
        source_names: List[str],
        destination_names: List[str],
        notes: str,
        potentials: Optional[Tuple[List[Fraction], List[Fraction]]],
        deltas: Optional[List[List[Optional[Fraction]]]],
        cycle: Optional[List[Cell]],
        theta: Optional[Fraction],
    ) -> None:
        if self.snapshot_writer is None:
            return
        self.snapshot_writer.write_solution(
            title=title,
            costs=costs,
            allocations=allocations,
            basis=basis,
            source_names=source_names,
            destination_names=destination_names,
            notes=notes,
            potentials=potentials,
            deltas=deltas,
            cycle=cycle,
            theta=theta,
            total_cost=self._calculate_total_cost(costs=costs, allocations=allocations),
        )

    def _method_title(self, method: str) -> str:
        titles = {
            "north_west": "северо-западного угла",
            "least_cost": "наименьшей стоимости",
            "vogel": "Фогеля",
        }
        return titles.get(method.lower(), method)

    def _cell_name(self, cell: Cell, source_names: List[str], destination_names: List[str]) -> str:
        row_index, column_index = cell
        return f"({source_names[row_index]}, {destination_names[column_index]})"

    @staticmethod
    def format_fraction(value: Fraction) -> str:
        if value.denominator == 1:
            return str(value.numerator)
        return f"{value.numerator}/{value.denominator}"
