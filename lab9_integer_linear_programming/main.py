from __future__ import annotations

import argparse
from fractions import Fraction
from typing import Dict

from branch_and_bound import BranchAndBoundSolver
from fraction_tools import format_fraction
from problem_reader import ProblemReader
from snapshot import SnapshotWriter


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Решение задачи целочисленного линейного программирования методом ветвей и границ."
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Путь к JSON-файлу с условием задачи.",
    )
    parser.add_argument(
        "--snapshot",
        "-s",
        default="integer_lp_snapshot.md",
        help="Путь к Markdown-файлу, в который будут записаны снимки алгоритма.",
    )

    args = parser.parse_args()

    problem = ProblemReader.read(args.input)
    snapshot_writer = SnapshotWriter(args.snapshot)
    solver = BranchAndBoundSolver(problem=problem, snapshot_writer=snapshot_writer)

    result = solver.solve()

    print("Статус:", result.status)
    print("Сообщение:", result.message)
    print("Количество рассмотренных узлов:", result.explored_nodes)

    if result.objective_value is not None:
        print("Значение целевой функции:", format_fraction(result.objective_value))

    if len(result.variables) > 0:
        print("Значения переменных:")
        print_variables(result.variables)

    print("Файл со снимками:", args.snapshot)


def print_variables(variables: Dict[str, Fraction]) -> None:
    for name, value in variables.items():
        print(f"  {name} = {format_fraction(value)}")


if __name__ == "__main__":
    main()
