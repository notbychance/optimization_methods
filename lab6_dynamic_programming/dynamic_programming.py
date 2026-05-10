from __future__ import annotations

from collections import defaultdict
from math import inf
from typing import Dict, List, Optional, Tuple, Union

from dp_models import (
    FiniteHorizonProblem,
    FiniteHorizonResult,
    KnapsackItem,
    KnapsackProblem,
    KnapsackResult,
    Stage,
    Transition,
)
from snapshot import SnapshotWriter

Number = Union[int, float]


class DynamicProgrammingSolver:
    def __init__(self, snapshot_writer: Optional[SnapshotWriter] = None):
        self.snapshot_writer = snapshot_writer

    def solve_knapsack(self, problem: KnapsackProblem) -> KnapsackResult:
        self._validate_knapsack_problem(problem)
        optimization = problem.optimization.lower()
        is_maximization = optimization == 'max'
        capacity_values = list(range(problem.capacity + 1))

        next_values: Dict[int, Number] = {capacity: 0 for capacity in capacity_values}
        stage_values: List[Dict[int, Number]] = []
        stage_decisions: List[Dict[int, int]] = []

        if self.snapshot_writer is not None:
            self.snapshot_writer.write_table(
                title='Исходные данные задачи о загрузке',
                headers=['Предмет', 'Вес', 'Прибыль', 'Максимальное количество'],
                rows=[
                    [
                        item.name,
                        item.weight,
                        item.profit,
                        'не ограничено' if item.max_count is None else item.max_count,
                    ]
                    for item in problem.items
                ],
                notes=f'Грузоподъемность: {problem.capacity}. Критерий оптимизации: {optimization}.',
            )

        for reversed_index, item in enumerate(reversed(problem.items), start=1):
            stage_index = len(problem.items) - reversed_index + 1
            current_values: Dict[int, Number] = {}
            current_decisions: Dict[int, int] = {}
            alternatives: Dict[int, str] = {}

            for capacity in capacity_values:
                best_value: Optional[Number] = None
                best_count = 0
                alternative_parts: List[str] = []
                max_count = self._max_item_count(item=item, capacity=capacity)

                for count in range(max_count + 1):
                    remaining_capacity = capacity - item.weight * count
                    candidate_value = item.profit * count + next_values[remaining_capacity]
                    alternative_parts.append(f'{count}: {self._format_number(candidate_value)}')

                    if best_value is None or self._is_better(candidate_value, best_value, is_maximization):
                        best_value = candidate_value
                        best_count = count

                if best_value is None:
                    raise RuntimeError('Не удалось вычислить значение динамического программирования.')

                current_values[capacity] = best_value
                current_decisions[capacity] = best_count
                alternatives[capacity] = '; '.join(alternative_parts)

            stage_values.insert(0, current_values)
            stage_decisions.insert(0, current_decisions)

            if self.snapshot_writer is not None:
                self.snapshot_writer.write_knapsack_stage(
                    stage_index=stage_index,
                    item_name=item.name,
                    capacities=capacity_values,
                    objective_values=current_values,
                    decisions=current_decisions,
                    alternatives=alternatives,
                    optimization=optimization,
                )

            next_values = current_values

        item_counts: Dict[str, int] = {}
        remaining_capacity = problem.capacity
        used_capacity = 0

        reconstruction_rows: List[List[object]] = []
        for item_index, item in enumerate(problem.items):
            count = stage_decisions[item_index][remaining_capacity]
            item_counts[item.name] = count
            before_capacity = remaining_capacity
            remaining_capacity -= item.weight * count
            used_capacity += item.weight * count
            reconstruction_rows.append([
                item_index + 1,
                item.name,
                before_capacity,
                count,
                item.weight * count,
                remaining_capacity,
            ])

        objective_value = stage_values[0][problem.capacity]

        if self.snapshot_writer is not None:
            self.snapshot_writer.write_table(
                title='Восстановление оптимального решения',
                headers=['Этап', 'Предмет', 'Вместимость до выбора', 'Выбранное количество', 'Занятая вместимость', 'Остаток вместимости'],
                rows=reconstruction_rows,
                notes='Решение восстанавливается по таблицам оптимальных решений, начиная с начальной грузоподъемности.',
            )

        return KnapsackResult(
            status='optimal',
            objective_value=objective_value,
            item_counts=item_counts,
            used_capacity=used_capacity,
            message='Оптимальное решение задачи о загрузке найдено методом динамического программирования.',
        )

    def solve_finite_horizon(self, problem: FiniteHorizonProblem) -> FiniteHorizonResult:
        self._validate_finite_horizon_problem(problem)
        optimization = problem.optimization.lower()
        is_maximization = optimization == 'max'

        value_by_next_stage: Dict[str, Number] = dict(problem.terminal_values)
        value_tables: List[Dict[str, Number]] = []
        decision_tables: List[Dict[str, Transition]] = []

        if self.snapshot_writer is not None:
            self.snapshot_writer.write_terminal_values(problem.terminal_values)

        for stage in reversed(problem.stages):
            transitions_by_state = self._group_transitions_by_state(stage.transitions)
            current_values: Dict[str, Number] = {}
            current_decisions: Dict[str, Transition] = {}
            snapshot_rows: List[List[object]] = []

            for state in stage.states:
                transitions = transitions_by_state.get(state, [])
                if len(transitions) == 0:
                    raise ValueError(f'Для состояния {state} на этапе {stage.name} не задано ни одной альтернативы.')

                best_value: Optional[Number] = None
                best_transition: Optional[Transition] = None
                alternative_parts: List[str] = []

                for transition in transitions:
                    if transition.next_state not in value_by_next_stage:
                        raise ValueError(
                            f'Переход из состояния {transition.state} по решению {transition.decision} ведет в состояние '
                            f'{transition.next_state}, для которого нет значения следующего этапа.'
                        )

                    candidate_value = transition.value + value_by_next_stage[transition.next_state]
                    alternative_parts.append(
                        f'{transition.decision}: {self._format_number(transition.value)} + '
                        f'F({transition.next_state})={self._format_number(value_by_next_stage[transition.next_state])} '
                        f'= {self._format_number(candidate_value)}'
                    )

                    if best_value is None or self._is_better(candidate_value, best_value, is_maximization):
                        best_value = candidate_value
                        best_transition = transition

                if best_value is None or best_transition is None:
                    raise RuntimeError('Не удалось вычислить функцию Беллмана.')

                current_values[state] = best_value
                current_decisions[state] = best_transition
                snapshot_rows.append([
                    state,
                    '; '.join(alternative_parts),
                    best_value,
                    f'{best_transition.decision} -> {best_transition.next_state}',
                ])

            value_tables.insert(0, current_values)
            decision_tables.insert(0, current_decisions)

            if self.snapshot_writer is not None:
                self.snapshot_writer.write_finite_stage(
                    stage_name=stage.name,
                    rows=snapshot_rows,
                    optimization=optimization,
                )

            value_by_next_stage = current_values

        if problem.initial_state not in value_tables[0]:
            raise ValueError(f'Начальное состояние {problem.initial_state} отсутствует на первом этапе.')

        path: List[Dict[str, Union[str, Number]]] = []
        current_state = problem.initial_state

        for stage_index, stage in enumerate(problem.stages):
            if current_state not in decision_tables[stage_index]:
                raise ValueError(
                    f'Для состояния {current_state} на этапе {stage.name} не найдено оптимальное решение.'
                )

            transition = decision_tables[stage_index][current_state]
            path.append({
                'stage': stage.name,
                'state': current_state,
                'decision': transition.decision,
                'value': transition.value,
                'next_state': transition.next_state,
            })
            current_state = transition.next_state

        objective_value = value_tables[0][problem.initial_state]

        if self.snapshot_writer is not None:
            self.snapshot_writer.write_table(
                title='Восстановление оптимальной стратегии',
                headers=['Этап', 'Состояние', 'Решение', 'Локальный выигрыш/затраты', 'Следующее состояние'],
                rows=[
                    [
                        item['stage'],
                        item['state'],
                        item['decision'],
                        item['value'],
                        item['next_state'],
                    ]
                    for item in path
                ],
                notes='Оптимальная стратегия восстанавливается от начального состояния по таблицам решений.',
            )

        return FiniteHorizonResult(
            status='optimal',
            objective_value=objective_value,
            initial_state=problem.initial_state,
            path=path,
            message='Оптимальная стратегия найдена методом обратной прогонки.',
        )

    def _validate_knapsack_problem(self, problem: KnapsackProblem) -> None:
        if problem.optimization.lower() not in {'max', 'min'}:
            raise ValueError("Критерий оптимизации должен быть 'max' или 'min'.")
        if problem.capacity < 0:
            raise ValueError('Грузоподъемность должна быть неотрицательной.')
        if len(problem.items) == 0:
            raise ValueError('Список предметов не должен быть пустым.')
        for item in problem.items:
            if item.weight <= 0:
                raise ValueError(f'Вес предмета {item.name} должен быть положительным целым числом.')
            if item.max_count is not None and item.max_count < 0:
                raise ValueError(f'Максимальное количество предмета {item.name} не может быть отрицательным.')

    def _validate_finite_horizon_problem(self, problem: FiniteHorizonProblem) -> None:
        if problem.optimization.lower() not in {'max', 'min'}:
            raise ValueError("Критерий оптимизации должен быть 'max' или 'min'.")
        if len(problem.stages) == 0:
            raise ValueError('Должен быть задан хотя бы один этап.')
        if len(problem.terminal_values) == 0:
            raise ValueError('Должны быть заданы граничные значения последнего этапа.')

    def _max_item_count(self, item: KnapsackItem, capacity: int) -> int:
        count_by_capacity = capacity // item.weight
        if item.max_count is None:
            return count_by_capacity
        return min(count_by_capacity, item.max_count)

    def _is_better(self, candidate: Number, current: Number, is_maximization: bool) -> bool:
        if is_maximization:
            return candidate > current
        return candidate < current

    def _group_transitions_by_state(self, transitions: List[Transition]) -> Dict[str, List[Transition]]:
        result: Dict[str, List[Transition]] = defaultdict(list)
        for transition in transitions:
            result[transition.state].append(transition)
        return result

    def _format_number(self, value: Number) -> str:
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)
