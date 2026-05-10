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
    MultiplicativeConstraintProblem,
    MultiplicativeConstraintResult,
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


    def solve_multiplicative_constraint(self, problem: MultiplicativeConstraintProblem) -> MultiplicativeConstraintResult:
        """Решение 17-го варианта ЛР 6 без изменения условия.

        Условие из варианта: max sum(y_i^2), product(y_i)=c, y_i >= 0.
        Для n >= 2 задача не имеет конечного максимума: значение целевой
        функции можно неограниченно увеличивать, сохраняя произведение.
        """
        optimization = problem.optimization.lower()

        if self.snapshot_writer is not None:
            self.snapshot_writer.write_text(
                title='Исходное условие варианта 17',
                lines=[
                    problem.condition_summary,
                    '',
                    f'Критерий оптимизации: {optimization}.',
                    f'Параметр n во входном файле: {problem.raw_n}.',
                    f'Параметр c во входном файле: {problem.raw_c}.',
                ],
            )
            self.snapshot_writer.write_text(
                title='Декомпозиция динамического программирования',
                lines=[
                    'Этап i соответствует выбору переменной y_i.',
                    'Состояние p_i — произведение, которое должно быть обеспечено переменными y_i, y_{i+1}, ..., y_n.',
                    'Рекуррентная форма для задачи максимизации:',
                    'F_i(p) = sup { y_i^2 + F_{i+1}(p / y_i) }, y_i > 0.',
                    'Граничный этап: F_n(p) = p^2.',
                    'Если p = 0, допустимы решения с хотя бы одной нулевой переменной на оставшихся этапах.',
                ],
            )

        if problem.n is None or problem.c is None:
            if self.snapshot_writer is not None:
                self.snapshot_writer.write_text(
                    title='Недостаточно числовых данных',
                    lines=[
                        'В методичке для 17-го варианта указаны параметры n и c символически.',
                        'Программа не подставляет искусственные значения, поэтому расчет завершен штатным статусом input_required.',
                        'Для численной проверки можно задать, например:',
                        '{',
                        '  "problem_type": "multiplicative_constraint_dynamic_programming",',
                        '  "optimization": "max",',
                        '  "parameters": {"n": 3, "c": 10}',
                        '}',
                    ],
                )
            return MultiplicativeConstraintResult(
                status='input_required',
                objective_value=None,
                n=problem.n,
                c=problem.c,
                variables={},
                message='Для 17-го варианта в условии не заданы конкретные числовые значения n и c.',
            )

        if problem.n <= 0:
            raise ValueError('Параметр n должен быть положительным целым числом.')

        if problem.c < 0:
            if self.snapshot_writer is not None:
                self.snapshot_writer.write_text(
                    title='Проверка допустимости',
                    lines=[
                        'Все переменные y_i должны быть неотрицательными.',
                        f'Произведение неотрицательных переменных не может быть равно c = {self._format_number(problem.c)} < 0.',
                        'Следовательно, допустимых решений нет.',
                    ],
                )
            return MultiplicativeConstraintResult(
                status='infeasible',
                objective_value=None,
                n=problem.n,
                c=problem.c,
                variables={},
                message='Допустимых решений нет: произведение неотрицательных переменных не может быть отрицательным.',
            )

        if optimization == 'max':
            return self._solve_multiplicative_max(problem)

        return self._solve_multiplicative_min(problem)

    def _solve_multiplicative_max(self, problem: MultiplicativeConstraintProblem) -> MultiplicativeConstraintResult:
        if problem.n == 1:
            value = problem.c * problem.c
            variables = {'y1': problem.c}
            if self.snapshot_writer is not None:
                self.snapshot_writer.write_table(
                    title='Частный случай n = 1',
                    headers=['Переменная', 'Значение'],
                    rows=[['y1', problem.c]],
                    notes='При n = 1 ограничение y1 = c однозначно задает решение.',
                )
            return MultiplicativeConstraintResult(
                status='optimal',
                objective_value=value,
                n=problem.n,
                c=problem.c,
                variables=variables,
                message='Оптимальное решение найдено: при n = 1 допустимое решение единственно.',
            )

        rows: List[List[object]] = []
        for t in [10, 100, 1000]:
            if problem.c == 0:
                y1 = 0
                y2 = t
                other_value = 1
                objective = y1 * y1 + y2 * y2 + max(problem.n - 2, 0) * other_value * other_value
                product_expression = '0'
            else:
                y1 = t
                y2 = problem.c / t
                other_value = 1
                objective = y1 * y1 + y2 * y2 + max(problem.n - 2, 0) * other_value * other_value
                product_expression = self._format_number(problem.c)

            rows.append([
                t,
                self._format_number(y1),
                self._format_number(y2),
                self._format_number(other_value) if problem.n > 2 else '-',
                product_expression,
                self._format_number(objective),
            ])

        if self.snapshot_writer is not None:
            self.snapshot_writer.write_table(
                title='Проверка ограниченности целевой функции',
                headers=['t', 'y1', 'y2', 'y3..yn', 'Произведение', 'z(t)'],
                rows=rows,
                notes=(
                    'Построена допустимая последовательность решений. При t -> бесконечность '
                    'значение z(t) также стремится к бесконечности, а произведение остается равным c.'
                ),
            )
            self.snapshot_writer.write_text(
                title='Вывод',
                lines=[
                    'Для n >= 2 задача максимизации не имеет конечного оптимального решения.',
                    'Это не ошибка программы: условие варианта сохранено без исправления.',
                    'Статус решения: unbounded.',
                ],
            )

        return MultiplicativeConstraintResult(
            status='unbounded',
            objective_value=None,
            n=problem.n,
            c=problem.c,
            variables={},
            message='Задача не ограничена сверху: конечного максимума не существует при n >= 2.',
        )

    def _solve_multiplicative_min(self, problem: MultiplicativeConstraintProblem) -> MultiplicativeConstraintResult:
        if problem.c == 0:
            variables = {f'y{index}': 0 for index in range(1, problem.n + 1)}
            if self.snapshot_writer is not None:
                self.snapshot_writer.write_table(
                    title='Частный случай c = 0 для минимизации',
                    headers=['Переменная', 'Значение'],
                    rows=[[name, value] for name, value in variables.items()],
                    notes='Все переменные равны нулю: произведение равно 0, сумма квадратов минимальна и равна 0.',
                )
            return MultiplicativeConstraintResult(
                status='optimal',
                objective_value=0,
                n=problem.n,
                c=problem.c,
                variables=variables,
                message='Минимум равен 0 при всех y_i = 0.',
            )

        equal_value = problem.c ** (1 / problem.n)
        objective_value = problem.n * (equal_value ** 2)
        variables = {f'y{index}': equal_value for index in range(1, problem.n + 1)}

        if self.snapshot_writer is not None:
            self.snapshot_writer.write_table(
                title='Решение родственной задачи минимизации',
                headers=['Переменная', 'Значение'],
                rows=[[name, value] for name, value in variables.items()],
                notes=(
                    'Этот блок используется только если во входном файле явно указан optimization = min. '
                    'Для исходного 17-го варианта стоит optimization = max.'
                ),
            )

        return MultiplicativeConstraintResult(
            status='optimal',
            objective_value=objective_value,
            n=problem.n,
            c=problem.c,
            variables=variables,
            message='Минимум найден в точке равных переменных.',
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
