from __future__ import annotations

import argparse
from typing import Dict, Tuple

from graph_models import Edge, NetworkResult, Number
from network_algorithms import NetworkSolver
from problem_reader import ProblemReader
from snapshot import SnapshotWriter


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Решение задач сетевых моделей: минимальное остовное дерево, кратчайший путь, максимальный поток, поток наименьшей стоимости.'
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
        default='network_snapshot.md',
        help='Путь к Markdown-файлу для записи снимков алгоритма.',
    )

    args = parser.parse_args()

    problem = ProblemReader.read(args.input)
    snapshot_writer = SnapshotWriter(args.snapshot)
    solver = NetworkSolver(problem=problem, snapshot_writer=snapshot_writer)
    result = solver.solve()

    print_result(result)
    print('Файл со снимками:', args.snapshot)


def print_result(result: NetworkResult) -> None:
    print('Тип задачи:', result.problem_type)
    print('Статус:', result.status)
    print('Сообщение:', result.message)

    if result.total_value is not None:
        print('Итоговое значение:', format_number(result.total_value))

    if result.path is not None:
        print('Путь:', ' -> '.join(result.path))

    if result.selected_edges is not None:
        print('Выбранные ребра:')
        for edge in result.selected_edges:
            print(f'  {edge.start} - {edge.end}; вес = {format_number(edge.weight)}')

    if result.flows is not None:
        print('Ненулевые потоки:')
        for (start, end), flow in sorted(result.flows.items()):
            if abs(flow) > 1e-12:
                print(f'  {start} -> {end}: {format_number(flow)}')


def format_number(value: Number) -> str:
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f'{value:.6g}'
    return str(value)


if __name__ == '__main__':
    main()
