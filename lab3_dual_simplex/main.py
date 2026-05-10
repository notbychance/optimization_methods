from __future__ import annotations

import argparse
from fractions import Fraction
from typing import Dict

from dual_simplex import DualSimplexSolver
from linear_problem import LinearProblem
from matrix_tools import format_fraction
from problem_reader import ProblemReader
from snapshot import SnapshotWriter


def run(input_path: str, snapshot_path: str) -> None:
    mode, problem_data = ProblemReader.read(input_path)
    snapshot_writer = SnapshotWriter(snapshot_path)
    solver = DualSimplexSolver(snapshot_writer=snapshot_writer)

    if mode == "model":
        if not isinstance(problem_data, LinearProblem):
            raise TypeError("Для режима model ожидался объект LinearProblem.")
        result = solver.solve_model(problem_data)
    else:
        if not isinstance(problem_data, dict):
            raise TypeError("Для режима tableau ожидался словарь с симплекс-таблицей.")
        result = solver.solve_tableau(problem_data)

    print("Статус:", result.status)
    print("Сообщение:", result.message)
    print("Количество итераций:", result.iterations)

    if result.status == "optimal":
        print(
            "Значение целевой функции:", format_result_fraction(result.objective_value)
        )
        print("Значения исходных переменных:")
        print_variables(result.variables)

    print("Файл со снимками:", snapshot_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Лабораторная работа №3: решение задачи двойственным симплекс-методом."
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Путь к входному JSON-файлу с формулировкой задачи или готовой таблицей.",
    )
    parser.add_argument(
        "--snapshot",
        "-s",
        required=True,
        help="Путь к Markdown-файлу для сохранения снимков алгоритма.",
    )
    return parser.parse_args()


def print_variables(variables: Dict[str, Fraction]) -> None:
    for name, value in variables.items():
        print(f"  {name} = {format_fraction(value)}")


def format_result_fraction(value: Fraction | None) -> str:
    if value is None:
        return "-"
    return format_fraction(value)


if __name__ == "__main__":
    arguments = parse_args()
    run(input_path=arguments.input, snapshot_path=arguments.snapshot)
