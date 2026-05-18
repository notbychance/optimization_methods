from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

from graphical_lp import GraphicalLinearProgrammingSolver
from problem_reader import ProblemReader
from snapshot import SnapshotWriter


def run(input_path: str, snapshot_path: str) -> None:
    problem = ProblemReader.read(input_path)
    plot_path = str(Path(snapshot_path).with_suffix(".png"))

    solver = GraphicalLinearProgrammingSolver(problem=problem)
    solution = solver.solve(plot_path=plot_path)

    snapshot_writer = SnapshotWriter(snapshot_path)
    snapshot_writer.write_solution(problem=problem, solution=solution)

    print("Статус:", solution.status)
    print("Сообщение:", solution.message)

    if solution.optimal_point is not None:
        print("Значение целевой функции:", SnapshotWriter.format_fraction(solution.optimal_point.objective_value))
        print("Значения переменных:")
        values: Dict[str, object] = {
            problem.variable_names[0]: solution.optimal_point.x,
            problem.variable_names[1]: solution.optimal_point.y,
            **solution.derived_values,
        }
        for name, value in values.items():
            print(f"  {name} = {SnapshotWriter.format_fraction(value)}")

    print("Файл отчета:", snapshot_path)
    print("Файл графика:", plot_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Лабораторная работа №1: графическое решение задачи линейного программирования."
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
        help="Путь к Markdown-файлу для сохранения результата решения.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    run(input_path=arguments.input, snapshot_path=arguments.snapshot)
