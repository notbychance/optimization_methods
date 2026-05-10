from __future__ import annotations

import argparse
from typing import Union

from dp_models import FiniteHorizonProblem, KnapsackProblem, MultiplicativeConstraintProblem
from dynamic_programming import DynamicProgrammingSolver
from problem_reader import ProblemReader
from snapshot import SnapshotWriter


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Решение детерминированной задачи динамического программирования.'
    )
    parser.add_argument(
        '--input',
        '-i',
        required=True,
        help='Путь к JSON-файлу с условием задачи.',
    )
    parser.add_argument(
        '--snapshot',
        '-s',
        default='dynamic_programming_snapshot.md',
        help='Путь к Markdown-файлу со снимками алгоритма.',
    )

    args = parser.parse_args()

    problem = ProblemReader.read(args.input)
    snapshot_writer = SnapshotWriter(args.snapshot)
    solver = DynamicProgrammingSolver(snapshot_writer=snapshot_writer)

    if isinstance(problem, KnapsackProblem):
        result = solver.solve_knapsack(problem)
        print('Статус:', result.status)
        print('Сообщение:', result.message)
        print('Значение целевой функции:', format_number(result.objective_value))
        print('Использованная вместимость:', result.used_capacity)
        print('Количество предметов:')
        for item_name, count in result.item_counts.items():
            print(f'  {item_name} = {count}')
    elif isinstance(problem, FiniteHorizonProblem):
        result = solver.solve_finite_horizon(problem)
        print('Статус:', result.status)
        print('Сообщение:', result.message)
        print('Начальное состояние:', result.initial_state)
        print('Значение целевой функции:', format_number(result.objective_value))
        print('Оптимальная стратегия:')
        for step in result.path:
            print(
                f"  Этап {step['stage']}: {step['state']} --{step['decision']} "
                f"({format_number(step['value'])})--> {step['next_state']}"
            )
    elif isinstance(problem, MultiplicativeConstraintProblem):
        result = solver.solve_multiplicative_constraint(problem)
        print('Статус:', result.status)
        print('Сообщение:', result.message)
        print('n:', '-' if result.n is None else result.n)
        print('c:', '-' if result.c is None else format_number(result.c))
        print('Значение целевой функции:', format_number(result.objective_value))
        if result.variables:
            print('Значения переменных:')
            for variable_name, value in result.variables.items():
                print(f'  {variable_name} = {format_number(value)}')
    else:
        raise TypeError('Неизвестный тип задачи.')

    print('Файл со снимками:', args.snapshot)


def format_number(value: Union[int, float, None]) -> str:
    if value is None:
        return '-'
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


if __name__ == '__main__':
    main()
