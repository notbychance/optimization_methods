from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from dp_models import (
    FiniteHorizonProblem,
    KnapsackItem,
    KnapsackProblem,
    MultiplicativeConstraintProblem,
    Stage,
    Transition,
)

Number = Union[int, float]


class ProblemReader:
    @staticmethod
    def read(file_path: str) -> Union[KnapsackProblem, FiniteHorizonProblem, MultiplicativeConstraintProblem]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f'Файл с условием не найден: {file_path}')
        if path.suffix.lower() != '.json':
            raise ValueError('Поддерживается только формат JSON.')

        data = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            raise ValueError('Корневой элемент JSON должен быть объектом.')

        problem_type = str(data.get('problem_type', '')).strip().lower()
        if problem_type == 'knapsack':
            return ProblemReader._read_knapsack(data)
        if problem_type == 'finite_horizon':
            return ProblemReader._read_finite_horizon(data)
        if problem_type == 'multiplicative_constraint_dynamic_programming':
            return ProblemReader._read_multiplicative_constraint(data)

        raise ValueError(
            "Поле problem_type должно быть равно 'knapsack', 'finite_horizon' "
            "или 'multiplicative_constraint_dynamic_programming'."
        )

    @staticmethod
    def _read_knapsack(data: Dict[str, Any]) -> KnapsackProblem:
        optimization = ProblemReader._read_optimization(data)
        capacity = ProblemReader._to_int(data.get('capacity'), 'capacity')
        raw_items = data.get('items')

        if not isinstance(raw_items, list) or len(raw_items) == 0:
            raise ValueError('Поле items должно быть непустым списком.')

        items: List[KnapsackItem] = []
        for index, raw_item in enumerate(raw_items, start=1):
            if not isinstance(raw_item, dict):
                raise ValueError(f'Предмет {index} должен быть объектом.')

            name = str(raw_item.get('name', f'x{index}'))
            weight = ProblemReader._to_int(raw_item.get('weight'), f'items[{index}].weight')
            profit = ProblemReader._to_number(raw_item.get('profit', raw_item.get('value')), f'items[{index}].profit')
            max_count_value = raw_item.get('max_count')
            max_count = None if max_count_value is None else ProblemReader._to_int(max_count_value, f'items[{index}].max_count')

            items.append(KnapsackItem(name=name, weight=weight, profit=profit, max_count=max_count))

        return KnapsackProblem(optimization=optimization, capacity=capacity, items=items)

    @staticmethod
    def _read_finite_horizon(data: Dict[str, Any]) -> FiniteHorizonProblem:
        optimization = ProblemReader._read_optimization(data)
        initial_state = str(data.get('initial_state', '')).strip()
        if not initial_state:
            raise ValueError('Поле initial_state обязательно для finite_horizon.')

        raw_terminal_values = data.get('terminal_values', data.get('terminal_value'))
        if not isinstance(raw_terminal_values, dict):
            raise ValueError('Поле terminal_values должно быть объектом.')

        terminal_values = {
            str(state): ProblemReader._to_number(value, f'terminal_values[{state}]')
            for state, value in raw_terminal_values.items()
        }

        raw_stages = data.get('stages')
        if not isinstance(raw_stages, list) or len(raw_stages) == 0:
            raise ValueError('Поле stages должно быть непустым списком.')

        stages: List[Stage] = []
        for stage_index, raw_stage in enumerate(raw_stages, start=1):
            if not isinstance(raw_stage, dict):
                raise ValueError(f'Этап {stage_index} должен быть объектом.')

            stage_name = str(raw_stage.get('name', stage_index))
            raw_states = raw_stage.get('states')
            if not isinstance(raw_states, list) or len(raw_states) == 0:
                raise ValueError(f'На этапе {stage_name} должен быть непустой список states.')
            states = [str(state) for state in raw_states]

            raw_transitions = raw_stage.get('transitions')
            if not isinstance(raw_transitions, list) or len(raw_transitions) == 0:
                raise ValueError(f'На этапе {stage_name} должен быть непустой список transitions.')

            transitions: List[Transition] = []
            for transition_index, raw_transition in enumerate(raw_transitions, start=1):
                if not isinstance(raw_transition, dict):
                    raise ValueError(f'Переход {transition_index} на этапе {stage_name} должен быть объектом.')

                transitions.append(
                    Transition(
                        state=str(raw_transition.get('state')),
                        decision=str(raw_transition.get('decision')),
                        next_state=str(raw_transition.get('next_state')),
                        value=ProblemReader._to_number(raw_transition.get('value', raw_transition.get('cost')), f'transitions[{transition_index}].value'),
                    )
                )

            stages.append(Stage(name=stage_name, states=states, transitions=transitions))

        return FiniteHorizonProblem(
            optimization=optimization,
            initial_state=initial_state,
            stages=stages,
            terminal_values=terminal_values,
        )

    @staticmethod
    def _read_multiplicative_constraint(data: Dict[str, Any]) -> MultiplicativeConstraintProblem:
        optimization = ProblemReader._read_optimization(data)
        parameters = data.get('parameters')
        if not isinstance(parameters, dict):
            parameters = {}

        raw_n = data.get('n', parameters.get('n'))
        raw_c = data.get('c', parameters.get('c'))

        n = ProblemReader._try_to_int(raw_n)
        c = ProblemReader._try_to_number(raw_c)

        condition_summary = str(
            data.get(
                'condition_summary',
                'Максимизировать z = y1^2 + y2^2 + ... + yn^2 при условии y1*y2*...*yn = c, yi >= 0.',
            )
        )

        return MultiplicativeConstraintProblem(
            optimization=optimization,
            n=n,
            c=c,
            raw_n=raw_n,
            raw_c=raw_c,
            condition_summary=condition_summary,
        )

    @staticmethod
    def _read_optimization(data: Dict[str, Any]) -> str:
        optimization = str(data.get('optimization', data.get('sense', 'max'))).strip().lower()
        if optimization not in {'max', 'min'}:
            raise ValueError("Критерий optimization должен быть 'max' или 'min'.")
        return optimization

    @staticmethod
    def _to_int(value: Any, field_name: str) -> int:
        if isinstance(value, bool):
            raise ValueError(f'Поле {field_name} должно быть целым числом.')
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, str):
            prepared = value.strip().replace(',', '.')
            parsed = float(prepared)
            if parsed.is_integer():
                return int(parsed)
        raise ValueError(f'Поле {field_name} должно быть целым числом.')

    @staticmethod
    def _to_number(value: Any, field_name: str) -> Number:
        if isinstance(value, bool) or value is None:
            raise ValueError(f'Поле {field_name} должно быть числом.')
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return value
        if isinstance(value, str):
            prepared = value.strip().replace(',', '.')
            parsed = float(prepared)
            if parsed.is_integer():
                return int(parsed)
            return parsed
        raise ValueError(f'Поле {field_name} должно быть числом.')

    @staticmethod
    def _try_to_int(value: Any) -> Optional[int]:
        try:
            return ProblemReader._to_int(value, 'n')
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _try_to_number(value: Any) -> Optional[Number]:
        try:
            return ProblemReader._to_number(value, 'c')
        except (TypeError, ValueError):
            return None
