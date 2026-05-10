from __future__ import annotations

import argparse
from fractions import Fraction
from typing import Dict

from fraction_tools import format_fraction
from game_models import BimatrixGameProblem, DecisionProblem, MatrixGameProblem, PreventiveMaintenanceResult
from game_theory import BimatrixGameSolver, DecisionCriteriaSolver, MatrixGameSolver, PreventiveMaintenanceDecisionTreeSolver
from problem_reader import ProblemReader
from snapshot import SnapshotWriter


def main() -> None:
    parser = argparse.ArgumentParser(
        description='ЛР 8. Теория игр и принятия решений: матричные игры, критерии решений, биматричные игры, дерево решений профилактического ремонта.'
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
        default='game_theory_snapshot.md',
        help='Путь к Markdown-файлу для поэтапного вывода таблиц.',
    )

    args = parser.parse_args()

    task_type, problem = ProblemReader.read(args.input)
    snapshot_writer = SnapshotWriter(args.snapshot)

    if task_type == 'matrix_game':
        result = MatrixGameSolver(problem=problem, snapshot_writer=snapshot_writer).solve()
        print_matrix_game_result(result)
    elif task_type == 'decision':
        result = DecisionCriteriaSolver(problem=problem, snapshot_writer=snapshot_writer).solve()
        print_decision_result(result)
    elif task_type == 'bimatrix':
        result = BimatrixGameSolver(problem=problem, snapshot_writer=snapshot_writer).solve()
        print_bimatrix_result(result)
    elif task_type == 'preventive_maintenance_decision_tree':
        result = PreventiveMaintenanceDecisionTreeSolver(problem=problem, snapshot_writer=snapshot_writer).solve()
        print_preventive_maintenance_result(result)
    else:
        raise ValueError(f'Неизвестный тип задачи: {task_type}')

    print('Файл со снимками:', args.snapshot)


def print_matrix_game_result(result) -> None:
    print('Статус:', result.status)
    print('Сообщение:', result.message)
    print('Цена игры:', format_fraction(result.game_value))

    if result.saddle_points:
        print('Седловые точки:')
        for row_name, column_name, value in result.saddle_points:
            print(f'  ({row_name}, {column_name}) = {format_fraction(value)}')

    print('Стратегия первого игрока:')
    print_probability_dictionary(result.row_strategy_probabilities)
    print('Стратегия второго игрока:')
    print_probability_dictionary(result.column_strategy_probabilities)


def print_decision_result(result) -> None:
    print('Статус:', result.status)
    print('Сообщение:', result.message)
    print('Результаты критериев:')
    for criterion in result.criteria:
        alternatives = ', '.join(criterion.best_alternatives)
        print(f'  {criterion.criterion_name}: {alternatives}; значение = {format_fraction(criterion.best_value)}')


def print_bimatrix_result(result) -> None:
    print('Статус:', result.status)
    print('Сообщение:', result.message)
    if len(result.pure_equilibria) == 0:
        print('Равновесия Нэша в чистых стратегиях не найдены.')
        return
    print('Равновесия Нэша в чистых стратегиях:')
    for equilibrium in result.pure_equilibria:
        print(
            f'  ({equilibrium.row_strategy}, {equilibrium.column_strategy}) -> '
            f'({format_fraction(equilibrium.row_player_payoff)}, {format_fraction(equilibrium.column_player_payoff)})'
        )


def print_preventive_maintenance_result(result: PreventiveMaintenanceResult) -> None:
    print('Статус:', result.status)
    print('Сообщение:', result.message)
    print('Оптимальная длина цикла профилактического ремонта:', result.optimal_cycle_months, 'мес.')
    print('Минимальная средняя стоимость на 1 автомобиль в месяц:', format_decimal(result.minimal_average_cost_per_vehicle_per_month))
    print('Минимальная средняя стоимость для всего парка в месяц:', format_decimal(result.minimal_average_cost_for_fleet_per_month))


def format_decimal(value: Fraction | None, digits: int = 6) -> str:
    if value is None:
        return '-'
    return f'{float(value):.{digits}f}'


def print_probability_dictionary(probabilities: Dict[str, Fraction]) -> None:
    for name, probability in probabilities.items():
        print(f'  {name} = {format_fraction(probability)}')


if __name__ == '__main__':
    main()
