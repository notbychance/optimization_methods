from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional


TASK_DIRECTORIES: Dict[int, str] = {
    1: "lab1_linear_programming",
    2: "lab2_simplex",
    3: "lab3_dual_simplex",
    4: "lab4_transportation",
    5: "lab5_network_models",
    6: "lab6_dynamic_programming",
    7: "lab7_parametric_linear_programming",
    8: "lab8_game_theory",
    9: "lab9_integer_linear_programming",
}

TASK_TITLES: Dict[int, str] = {
    1: "Решение задач линейного программирования графическим методом",
    2: "Симплекс-метод",
    3: "Двойственный симплекс-метод",
    4: "Транспортная задача",
    5: "Сетевые модели",
    6: "Динамическое программирование",
    7: "Параметрическое линейное программирование",
    8: "Теория игр и принятие решений",
    9: "Целочисленное линейное программирование",
}


def main() -> None:
    arguments = parse_args()
    project_directory = Path(__file__).resolve().parent

    task_number = get_task_number(arguments.number)
    task_directory = get_task_directory(
        project_directory=project_directory,
        task_number=task_number,
    )

    raw_input_path = get_required_text_value(
        value=arguments.input,
        prompt="Введите путь к файлу импорта JSON: ",
        parser_error_message="нужно указать файл импорта через --input/-i или ввести его интерактивно",
    )
    raw_export_path = get_required_text_value(
        value=arguments.snapshot,
        prompt="Введите путь к файлу экспорта Markdown: ",
        parser_error_message="нужно указать файл экспорта через --snapshot/-s/--output/-o или ввести его интерактивно",
    )

    input_path = resolve_existing_input_path(
        project_directory=project_directory,
        task_directory=task_directory,
        raw_input_path=raw_input_path,
    )
    export_path = resolve_export_path(
        project_directory=project_directory,
        task_directory=task_directory,
        raw_export_path=raw_export_path,
    )

    export_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Лабораторная работа №{task_number}: {TASK_TITLES[task_number]}", flush=True)
    print(f"Файл импорта: {input_path}", flush=True)
    print(f"Файл экспорта: {export_path}", flush=True)
    print(flush=True)

    run_task_main(
        task_directory=task_directory,
        input_path=input_path,
        export_path=export_path,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Общий запуск лабораторных работ по методам оптимизации."
    )
    parser.add_argument(
        "--number",
        "-n",
        "-number",
        type=int,
        choices=sorted(TASK_DIRECTORIES.keys()),
        help="Номер лабораторной работы: от 1 до 9.",
    )
    parser.add_argument(
        "--input",
        "-i",
        "--import-file",
        dest="input",
        help="Путь к входному JSON-файлу с условием задачи.",
    )
    parser.add_argument(
        "--snapshot",
        "-s",
        "--output",
        "-o",
        "--export",
        "--export-file",
        dest="snapshot",
        help="Путь к Markdown-файлу для экспорта снимков/результатов решения.",
    )
    return parser.parse_args()


def get_task_number(argument_value: Optional[int]) -> int:
    if argument_value is not None:
        return argument_value

    print("Доступные лабораторные работы:")
    for task_number in sorted(TASK_DIRECTORIES.keys()):
        print(f"  {task_number}. {TASK_TITLES[task_number]}")

    while True:
        try:
            raw_value = input("Введите номер лабораторной работы: ").strip()
        except EOFError as exception:
            raise SystemExit(
                "Ошибка: нужно указать номер лабораторной работы через --number/-n."
            ) from exception

        try:
            task_number = int(raw_value)
        except ValueError:
            print("Введите целое число от 1 до 9.")
            continue

        if task_number in TASK_DIRECTORIES:
            return task_number

        print("Неизвестный номер лабораторной работы. Допустимые номера: 1, 2, 3, 4, 5, 6, 7, 8, 9.")


def get_required_text_value(
    value: Optional[str],
    prompt: str,
    parser_error_message: str,
) -> str:
    if value is not None and value.strip() != "":
        return value.strip()

    try:
        entered_value = input(prompt).strip()
    except EOFError as exception:
        raise SystemExit(f"Ошибка: {parser_error_message}.") from exception

    if entered_value == "":
        raise SystemExit(f"Ошибка: {parser_error_message}.")

    return entered_value


def get_task_directory(project_directory: Path, task_number: int) -> Path:
    task_directory_name = TASK_DIRECTORIES[task_number]
    task_directory = project_directory / task_directory_name

    if not task_directory.is_dir():
        raise FileNotFoundError(
            f"Не найден каталог лабораторной работы №{task_number}: {task_directory}"
        )

    return task_directory


def resolve_existing_input_path(
    project_directory: Path,
    task_directory: Path,
    raw_input_path: str,
) -> Path:
    input_path = Path(raw_input_path).expanduser()

    if input_path.is_absolute():
        resolved_input_path = input_path.resolve()
    else:
        candidates = [
            (Path.cwd() / input_path).resolve(),
            (project_directory / input_path).resolve(),
            (task_directory / input_path).resolve(),
            (task_directory / "examples" / input_path).resolve(),
        ]
        resolved_input_path = next(
            (candidate for candidate in candidates if candidate.is_file()),
            candidates[0],
        )

    if not resolved_input_path.is_file():
        raise FileNotFoundError(f"Не найден входной JSON-файл: {resolved_input_path}")

    return resolved_input_path


def resolve_export_path(
    project_directory: Path,
    task_directory: Path,
    raw_export_path: str,
) -> Path:
    export_path = Path(raw_export_path).expanduser()

    if export_path.is_absolute():
        return export_path.resolve()

    candidates = [
        (Path.cwd() / export_path).resolve(),
        (project_directory / export_path).resolve(),
        (task_directory / export_path).resolve(),
    ]

    for candidate in candidates:
        if candidate.parent.exists():
            return candidate

    return candidates[0]


def run_task_main(task_directory: Path, input_path: Path, export_path: Path) -> None:
    module_main_path = task_directory / "main.py"

    if not module_main_path.is_file():
        raise FileNotFoundError(f"Не найден модуль запуска: {module_main_path}")

    command = [
        sys.executable,
        str(module_main_path),
        "--input",
        str(input_path),
        "--snapshot",
        str(export_path),
    ]

    completed_process = subprocess.run(command, cwd=str(task_directory), check=False)

    if completed_process.returncode != 0:
        raise SystemExit(completed_process.returncode)


if __name__ == "__main__":
    main()
