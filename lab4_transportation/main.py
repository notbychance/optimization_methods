from __future__ import annotations

import argparse
from fractions import Fraction
from typing import List

from problem_reader import ProblemReader
from snapshot import SnapshotWriter
from transportation import TransportationSolver


def run(input_path: str, snapshot_path: str) -> None:
    problem = ProblemReader.read(input_path)
    snapshot_writer = SnapshotWriter(snapshot_path)
    solver = TransportationSolver(problem=problem, snapshot_writer=snapshot_writer)
    result = solver.solve()

    print("Статус:", result.status)
    print("Сообщение:", result.message)
    print("Количество итераций:", result.iterations)

    if result.status == "optimal":
        print("Минимальная стоимость перевозок:", format_fraction(result.total_cost))
        print("План перевозок:")
        print_allocations(
            allocations=result.allocations,
            source_names=result.source_names,
            destination_names=result.destination_names,
        )

    print("Файл со снимками:", snapshot_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Лабораторная работа №4: решение транспортной задачи."
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Путь к входному JSON-файлу с транспортной задачей.",
    )
    parser.add_argument(
        "--snapshot",
        "-s",
        required=True,
        help="Путь к Markdown-файлу для сохранения снимков решения.",
    )
    return parser.parse_args()


def print_allocations(
    allocations: List[List[Fraction]],
    source_names: List[str],
    destination_names: List[str],
) -> None:
    header = ["Поставщик/потребитель"] + destination_names
    widths = [max(20, len(value)) for value in header]

    for row_index, row in enumerate(allocations):
        widths[0] = max(widths[0], len(source_names[row_index]))
        for column_index, value in enumerate(row):
            widths[column_index + 1] = max(
                widths[column_index + 1], len(format_fraction(value))
            )

    print(
        "  "
        + " | ".join(header[index].ljust(widths[index]) for index in range(len(header)))
    )
    print("  " + "-+-".join("-" * width for width in widths))

    for row_index, row in enumerate(allocations):
        values = [source_names[row_index]] + [format_fraction(value) for value in row]
        print(
            "  "
            + " | ".join(
                values[index].ljust(widths[index]) for index in range(len(values))
            )
        )


def format_fraction(value: Fraction | None) -> str:
    if value is None:
        return "-"
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


if __name__ == "__main__":
    arguments = parse_args()
    run(input_path=arguments.input, snapshot_path=arguments.snapshot)
