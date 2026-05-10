from __future__ import annotations

import argparse
from fractions import Fraction
from typing import Optional, Tuple

from linear_problem import BasisAnalysis, format_fraction, format_interval
from parametric_simplex import ParametricSimplexSolver
from problem_reader import ProblemReader
from snapshot import SnapshotWriter


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Решение задачи параметрического линейного программирования собственным алгоритмом."
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
        default="parametric_lp_snapshot.md",
        help="Путь к Markdown-файлу со снимками алгоритма.",
    )
    args = parser.parse_args()

    problem = ProblemReader.read(args.input)
    snapshot_writer = SnapshotWriter(args.snapshot)
    solver = ParametricSimplexSolver(problem=problem, snapshot_writer=snapshot_writer)
    result = solver.solve()

    print("Статус:", result.status)
    print("Сообщение:", result.message)
    print("Количество проанализированных базисов:", len(result.basis_analyses))
    print("Количество оптимальных интервалов:", len(result.valid_intervals))

    if result.valid_intervals:
        print("Интервалы оптимальности:")
        for interval_number, analysis in enumerate(result.valid_intervals, start=1):
            print(f"  {interval_number}. Базис: {', '.join(analysis.basis_names)}")
            print(f"     Интервал: {format_interval(analysis.valid_interval, result.parameter_name)}")
            if analysis.sample_parameter_value is not None:
                print(f"     Контрольное значение параметра: {format_fraction(analysis.sample_parameter_value)}")
                if analysis.sample_objective_value is not None:
                    print(f"     Значение целевой функции: {format_fraction(analysis.sample_objective_value)}")
                print("     Значения исходных переменных:")
                for variable_name, value in analysis.sample_solution.items():
                    print(f"       {variable_name} = {format_fraction(value)}")

    print("Файл со снимками:", args.snapshot)


if __name__ == "__main__":
    main()
