from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fraction_tools import to_fraction
from game_models import BimatrixGameProblem, DecisionProblem, MatrixGameProblem


class ProblemReader:
    @staticmethod
    def read(file_path: str) -> tuple[str, MatrixGameProblem | DecisionProblem | BimatrixGameProblem]:
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

        raise ValueError("Поле task_type должно быть одним из значений: 'matrix_game', 'decision', 'bimatrix'.")

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
