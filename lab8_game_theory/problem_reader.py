from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fraction_tools import to_fraction
from game_models import BimatrixGameProblem, DecisionProblem, MatrixGameProblem, PreventiveMaintenanceProblem


class ProblemReader:
    @staticmethod
    def read(file_path: str) -> tuple[str, MatrixGameProblem | DecisionProblem | BimatrixGameProblem | PreventiveMaintenanceProblem]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f'Файл с условием не найден: {file_path}')
        if path.suffix.lower() != '.json':
            raise ValueError('Поддерживается только формат JSON.')

        data = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            raise ValueError('Корневой элемент JSON должен быть объектом.')

        task_type = str(data.get('task_type', '')).strip().lower()
        if task_type == 'matrix_game':
            return task_type, ProblemReader._read_matrix_game(data)
        if task_type == 'decision':
            return task_type, ProblemReader._read_decision_problem(data)
        if task_type == 'bimatrix':
            return task_type, ProblemReader._read_bimatrix_game(data)
        if task_type == 'preventive_maintenance_decision_tree':
            return task_type, ProblemReader._read_preventive_maintenance_problem(data)

        raise ValueError("Поле task_type должно быть одним из значений: 'matrix_game', 'decision', 'bimatrix', 'preventive_maintenance_decision_tree'.")

    @staticmethod
    def _read_matrix_game(data: Dict[str, Any]) -> MatrixGameProblem:
        matrix = ProblemReader._read_fraction_matrix(data, 'payoff_matrix')
        row_strategy_names = ProblemReader._read_names(data, 'row_strategy_names', len(matrix), 'A')
        column_strategy_names = ProblemReader._read_names(data, 'column_strategy_names', len(matrix[0]), 'B')
        return MatrixGameProblem(
            payoff_matrix=matrix,
            row_strategy_names=row_strategy_names,
            column_strategy_names=column_strategy_names,
        )

    @staticmethod
    def _read_decision_problem(data: Dict[str, Any]) -> DecisionProblem:
        matrix = ProblemReader._read_fraction_matrix(data, 'payoff_matrix')
        alternative_names = ProblemReader._read_names(data, 'alternatives', len(matrix), 'A')
        state_names = ProblemReader._read_names(data, 'states', len(matrix[0]), 'S')

        objective = str(data.get('objective', 'max')).strip().lower()
        if objective not in {'max', 'min'}:
            raise ValueError("Поле objective должно быть 'max' или 'min'.")

        raw_probabilities = data.get('probabilities')
        probabilities = None
        if raw_probabilities is not None:
            if not isinstance(raw_probabilities, list):
                raise ValueError('Поле probabilities должно быть списком чисел.')
            probabilities = [to_fraction(value) for value in raw_probabilities]

        hurwicz_alpha = to_fraction(data.get('hurwicz_alpha', data.get('alpha', '1/2')))

        return DecisionProblem(
            objective=objective,
            payoff_matrix=matrix,
            alternative_names=alternative_names,
            state_names=state_names,
            probabilities=probabilities,
            hurwicz_alpha=hurwicz_alpha,
        )

    @staticmethod
    def _read_bimatrix_game(data: Dict[str, Any]) -> BimatrixGameProblem:
        row_player_matrix = ProblemReader._read_fraction_matrix(data, 'row_player_matrix')
        column_player_matrix = ProblemReader._read_fraction_matrix(data, 'column_player_matrix')
        row_strategy_names = ProblemReader._read_names(data, 'row_strategy_names', len(row_player_matrix), 'A')
        column_strategy_names = ProblemReader._read_names(data, 'column_strategy_names', len(row_player_matrix[0]), 'B')
        return BimatrixGameProblem(
            row_player_matrix=row_player_matrix,
            column_player_matrix=column_player_matrix,
            row_strategy_names=row_strategy_names,
            column_strategy_names=column_strategy_names,
        )


    @staticmethod
    def _read_preventive_maintenance_problem(data: Dict[str, Any]) -> PreventiveMaintenanceProblem:
        fleet_size = int(data.get('fleet_size', 1))
        if fleet_size <= 0:
            raise ValueError('Поле fleet_size должно быть положительным целым числом.')

        raw_probabilities = data.get('failure_probability_by_month')
        if raw_probabilities is None:
            raise ValueError('Для задачи preventive_maintenance_decision_tree нужно поле failure_probability_by_month.')

        probabilities: Dict[int, Any] = {}
        later_probability = None

        if isinstance(raw_probabilities, dict):
            for raw_key, raw_value in raw_probabilities.items():
                key = str(raw_key).strip().lower()
                if key in {'later', 'and_later', '11_and_later', '11+', 'after_10'}:
                    later_probability = to_fraction(raw_value)
                else:
                    try:
                        month = int(key)
                    except ValueError as exception:
                        raise ValueError(f'Недопустимый ключ месяца в failure_probability_by_month: {raw_key}') from exception
                    probabilities[month] = to_fraction(raw_value)
        elif isinstance(raw_probabilities, list):
            for index, raw_value in enumerate(raw_probabilities, start=1):
                probabilities[index] = to_fraction(raw_value)
        else:
            raise ValueError('Поле failure_probability_by_month должно быть объектом или списком.')

        if len(probabilities) == 0:
            raise ValueError('Должна быть задана хотя бы одна вероятность поломки по месяцам.')

        if later_probability is None:
            last_month = max(probabilities)
            later_probability = probabilities[last_month]

        for month, probability in probabilities.items():
            ProblemReader._validate_probability(probability, f'вероятность для месяца {month}')
        ProblemReader._validate_probability(later_probability, 'вероятность для последующих месяцев')

        random_failure_cost = to_fraction(data.get('random_failure_cost'))
        preventive_repair_cost = to_fraction(data.get('preventive_repair_cost'))
        if random_failure_cost < 0:
            raise ValueError('Стоимость случайной поломки не может быть отрицательной.')
        if preventive_repair_cost < 0:
            raise ValueError('Стоимость профилактического ремонта не может быть отрицательной.')

        max_cycle_months = int(data.get('max_cycle_months', 60))
        if max_cycle_months <= 0:
            raise ValueError('Поле max_cycle_months должно быть положительным целым числом.')

        return PreventiveMaintenanceProblem(
            fleet_size=fleet_size,
            failure_probability_by_month=probabilities,
            later_failure_probability=later_probability,
            random_failure_cost=random_failure_cost,
            preventive_repair_cost=preventive_repair_cost,
            max_cycle_months=max_cycle_months,
            source=str(data.get('source')) if data.get('source') is not None else None,
            condition_summary=str(data.get('condition_summary')) if data.get('condition_summary') is not None else None,
        )

    @staticmethod
    def _validate_probability(probability, field_name: str) -> None:
        if probability < 0 or probability > 1:
            raise ValueError(f'{field_name} должна быть в диапазоне от 0 до 1.')

    @staticmethod
    def _read_fraction_matrix(data: Dict[str, Any], field_name: str) -> List[List]:
        raw_matrix = data.get(field_name)
        if not isinstance(raw_matrix, list) or len(raw_matrix) == 0:
            raise ValueError(f'Поле {field_name} должно быть непустой матрицей.')

        matrix: List[List] = []
        for row_index, raw_row in enumerate(raw_matrix, start=1):
            if not isinstance(raw_row, list) or len(raw_row) == 0:
                raise ValueError(f'Строка {row_index} матрицы {field_name} должна быть непустым списком.')
            matrix.append([to_fraction(value) for value in raw_row])

        column_count = len(matrix[0])
        for row_index, row in enumerate(matrix, start=1):
            if len(row) != column_count:
                raise ValueError(f'Строка {row_index} матрицы {field_name} имеет неверную длину.')

        return matrix

    @staticmethod
    def _read_names(data: Dict[str, Any], field_name: str, count: int, prefix: str) -> List[str]:
        raw_names = data.get(field_name)
        if raw_names is None:
            return [f'{prefix}{index + 1}' for index in range(count)]
        if not isinstance(raw_names, list):
            raise ValueError(f'Поле {field_name} должно быть списком строк.')
        if len(raw_names) != count:
            raise ValueError(f'Количество элементов {field_name} должно быть равно {count}.')
        return [str(value) for value in raw_names]
