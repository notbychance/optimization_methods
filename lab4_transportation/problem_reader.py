from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List

from transportation import TransportationProblem


class ProblemReader:
    @staticmethod
    def read(file_path: str) -> TransportationProblem:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл с условием не найден: {file_path}")
        if path.suffix.lower() != ".json":
            raise ValueError("Поддерживается только формат входного файла JSON.")

        data = json.loads(path.read_text(encoding="utf-8"))
        return ProblemReader._from_json(data)

    @staticmethod
    def _from_json(data: Dict[str, Any]) -> TransportationProblem:
        costs_data = data.get("costs")
        supply_data = data.get("supply")
        demand_data = data.get("demand")

        if not isinstance(costs_data, list) or len(costs_data) == 0:
            raise ValueError("Поле costs должно быть непустой матрицей.")
        if not isinstance(supply_data, list) or len(supply_data) == 0:
            raise ValueError("Поле supply должно быть непустым списком.")
        if not isinstance(demand_data, list) or len(demand_data) == 0:
            raise ValueError("Поле demand должно быть непустым списком.")

        costs: List[List[Fraction]] = []
        for row_index, row in enumerate(costs_data, start=1):
            if not isinstance(row, list) or len(row) == 0:
                raise ValueError(f"Строка {row_index} поля costs должна быть непустым списком.")
            costs.append([ProblemReader._to_fraction(value) for value in row])

        supply = [ProblemReader._to_fraction(value) for value in supply_data]
        demand = [ProblemReader._to_fraction(value) for value in demand_data]

        source_names = data.get("source_names")
        if source_names is not None:
            if not isinstance(source_names, list):
                raise ValueError("Поле source_names должно быть списком строк.")
            source_names = [str(value) for value in source_names]

        destination_names = data.get("destination_names")
        if destination_names is not None:
            if not isinstance(destination_names, list):
                raise ValueError("Поле destination_names должно быть списком строк.")
            destination_names = [str(value) for value in destination_names]

        initial_method = str(data.get("initial_method", "north_west"))

        return TransportationProblem(
            costs=costs,
            supply=supply,
            demand=demand,
            source_names=source_names,
            destination_names=destination_names,
            initial_method=initial_method,
        )

    @staticmethod
    def _to_fraction(value: Any) -> Fraction:
        if value is None:
            raise ValueError("Числовое значение не может быть null.")
        if isinstance(value, Fraction):
            return value
        if isinstance(value, int):
            return Fraction(value)
        if isinstance(value, float):
            return Fraction(str(value))
        if isinstance(value, str):
            prepared_value = value.strip().replace(",", ".")
            if prepared_value == "":
                raise ValueError("Пустая строка не может быть преобразована в число.")
            return Fraction(prepared_value)
        raise ValueError(f"Невозможно преобразовать значение в число: {value}")
