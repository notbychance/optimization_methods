from __future__ import annotations

import argparse
from fractions import Fraction
from typing import Dict

from problem_reader import ProblemReader
from simplex import SimplexSolver
from snapshot import SnapshotWriter


def run(input_path: str, snapshot_path: str) -> None:
    problem = ProblemReader.read(input_path)
    snapshot_writer = SnapshotWriter(snapshot_path)
    solver = SimplexSolver(problem=problem, snapshot_writer=snapshot_writer)

    result = solver.solve()

    print("Статус:", result.status)
    print("Сообщение:", result.message)
    print("Количество итераций:", result.iterations)

    if result.status == "optimal":
        print("Значение целевой функции:", format_fraction(result.objective_value))
        print("Значения переменных:")
        print_variables(result.variables)

    print("Файл со снимками симплекс-таблиц:", snapshot_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Лабораторная работа №2: решение задачи линейного программирования симплекс-методом."
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Путь к входному JSON-файлу с формулировкой задачи.",
    )
    parser.add_argument(
        "--snapshot",
        "-s",
        required=True,
        help="Путь к Markdown-файлу для сохранения снимков симплекс-таблиц.",
    )
    return parser.parse_args()


def print_variables(variables: Dict[str, Fraction]) -> None:
    for name, value in variables.items():
        print(f"  {name} = {format_fraction(value)}")


def format_fraction(value: Fraction | None) -> str:
    if value is None:
        return "-"

    if value.denominator == 1:
        return str(value.numerator)

    return f"{value.numerator}/{value.denominator}"


if __name__ == "__main__":
    arguments = parse_args()
    run(input_path=arguments.input, snapshot_path=arguments.snapshot)
