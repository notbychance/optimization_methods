from __future__ import annotations

import argparse

from graph_models import NetworkResult, Number
from network_algorithms import NetworkSolver
from problem_reader import ProblemReader
from snapshot import SnapshotWriter


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Решение задач сетевых моделей, проверки предвыигрышной конфигурации и сетевого планирования.'
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
        if result.problem_type == 'project_scheduling':
            print('Продолжительность комплекса работ:', format_number(result.total_value))
        else:
            print('Итоговое значение:', format_number(result.total_value))

    if result.details:
        if 'total_cost' in result.details:
            print('Суммарная стоимость работ:', format_number(result.details['total_cost']))
        if 'finish_event' in result.details:
            print('Завершающее событие:', result.details['finish_event'])

    if result.path is not None:
        print('Путь:', ' -> '.join(result.path))

    if result.selected_edges is not None:
        if result.problem_type == 'project_scheduling':
            print('Критические работы:')
            for edge in result.selected_edges:
                print(
                    f'  ({edge.start}; {edge.end}); продолжительность = {format_number(edge.weight)}; стоимость = {format_number(edge.cost)}'
                )
        else:
            print('Выбранные ребра:')
            for edge in result.selected_edges:
                print(f'  {edge.start} - {edge.end}; вес = {format_number(edge.weight)}')

    if result.event_early_times is not None and result.event_late_times is not None:
        print('Временные характеристики событий:')
        for node in sorted(result.event_early_times.keys(), key=node_sort_key):
            early = result.event_early_times[node]
            late = result.event_late_times[node]
            reserve = late - early
            print(
                f'  событие {node}: ранний срок = {format_number(early)}, поздний срок = {format_number(late)}, резерв = {format_number(reserve)}'
            )

    if result.work_reserves is not None:
        print('Полные резервы работ:')
        for start, end in sorted(result.work_reserves.keys(), key=lambda pair: (node_sort_key(pair[0]), node_sort_key(pair[1]))):
            print(f'  ({start}; {end}): {format_number(result.work_reserves[(start, end)])}')

    if result.flows is not None:
        print('Ненулевые потоки:')
        for (start, end), flow in sorted(result.flows.items()):
            if abs(flow) > 1e-12:
                print(f'  {start} -> {end}: {format_number(flow)}')

    if result.winning_moves is not None:
        print('Предвыигрышные ходы:')
        if len(result.winning_moves) == 0:
            print('  не найдены')
        else:
            for move in result.winning_moves:
                print(
                    '  символ {symbol}: строка {row}, столбец {column}, направление: {direction}, длина цепочки: {line_length}'.format(
                        symbol=move.get('symbol'),
                        row=move.get('row'),
                        column=move.get('column'),
                        direction=move.get('direction'),
                        line_length=move.get('line_length'),
                    )
                )


def format_number(value: object) -> str:
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f'{value:.6g}'
    return str(value)


def node_sort_key(node: str) -> tuple[int, object]:
    text = str(node)
    if text.isdigit():
        return 0, int(text)
    return 1, text


if __name__ == '__main__':
    main()
