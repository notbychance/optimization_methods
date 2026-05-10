from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Tuple

from linear_problem import Constraint, LinearProblem


class ProblemReader:
    @staticmethod
    def read(file_path: str) -> Tuple[str, LinearProblem | Dict[str, Any]]:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Файл с условием не найден: {file_path}")

        if path.suffix.lower() != ".json":
            raise ValueError("Поддерживается входной файл в формате JSON.")

        data = json.loads(path.read_text(encoding="utf-8"))
        mode = str(data.get("mode", "model")).strip().lower()

        if mode == "model":
            return mode, ProblemReader._read_model(data)

        if mode == "tableau":
            return mode, ProblemReader._read_tableau(data)

        raise ValueError("Поле mode должно иметь значение 'model' или 'tableau'.")

    @staticmethod
    def _read_model(data: Dict[str, Any]) -> LinearProblem:
        objective_data = data.get("objective")
        if not isinstance(objective_data, dict):
            raise ValueError("В JSON должен быть объект objective.")

        objective_type = str(objective_data.get("type", objective_data.get("sense", "min"))).strip().lower()
        coefficients = objective_data.get("coefficients", objective_data.get("c"))

        if not isinstance(coefficients, list):
            raise ValueError("В objective должен быть список coefficients.")

        objective = [ProblemReader._to_fraction(value) for value in coefficients]

        raw_constraints = data.get("constraints")
        if not isinstance(raw_constraints, list):
            raise ValueError("В JSON должен быть список constraints.")

        constraints: List[Constraint] = []
        for index, raw_constraint in enumerate(raw_constraints, start=1):
            if not isinstance(raw_constraint, dict):
                raise ValueError(f"Ограничение {index} должно быть объектом.")

            raw_coefficients = raw_constraint.get("coefficients", raw_constraint.get("a"))
            sign = raw_constraint.get("sign", raw_constraint.get("operator"))
            rhs = raw_constraint.get("rhs", raw_constraint.get("b"))

            if not isinstance(raw_coefficients, list):
                raise ValueError(f"В ограничении {index} должен быть список coefficients.")

            constraints.append(
                Constraint(
                    coefficients=[ProblemReader._to_fraction(value) for value in raw_coefficients],
                    sign=ProblemReader._normalize_sign(str(sign)),
                    rhs=ProblemReader._to_fraction(rhs),
                )
            )

        variable_names = data.get("variable_names")
        if variable_names is not None:
            if not isinstance(variable_names, list):
                raise ValueError("Поле variable_names должно быть списком строк.")
            variable_names = [str(value) for value in variable_names]

        return LinearProblem(
            objective_type=objective_type,
            objective=objective,
            constraints=constraints,
            variable_names=variable_names,
        )

    @staticmethod
    def _read_tableau(data: Dict[str, Any]) -> Dict[str, Any]:
        column_names = data.get("column_names", data.get("columns"))
        basis = data.get("basis")
        rows = data.get("rows", data.get("constraints"))
        objective_row = data.get("objective_row")
        max_costs = data.get("max_costs", data.get("costs"))
        original_variable_count = data.get("original_variable_count")
        original_objective = data.get("original_objective")
        objective_type = str(data.get("objective_type", "max")).strip().lower()

        if not isinstance(column_names, list):
            raise ValueError("Для режима tableau нужно задать список column_names.")
        if not isinstance(basis, list):
            raise ValueError("Для режима tableau нужно задать список basis.")
        if not isinstance(rows, list):
            raise ValueError("Для режима tableau нужно задать список rows.")
        if not isinstance(objective_row, list):
            raise ValueError("Для режима tableau нужно задать список objective_row.")
        if not isinstance(max_costs, list):
            raise ValueError("Для режима tableau нужно задать список max_costs.")

        if original_variable_count is None:
            original_variable_count = len(column_names)

        if original_objective is None:
            original_objective = max_costs[:original_variable_count]

        return {
            "column_names": [str(value) for value in column_names],
            "basis": [str(value) for value in basis],
            "rows": [[ProblemReader._to_fraction(value) for value in row] for row in rows],
            "objective_row": [ProblemReader._to_fraction(value) for value in objective_row],
            "max_costs": [ProblemReader._to_fraction(value) for value in max_costs],
            "original_variable_count": int(original_variable_count),
            "original_objective": [ProblemReader._to_fraction(value) for value in original_objective],
            "objective_type": objective_type,
        }

    @staticmethod
    def _normalize_sign(sign: str) -> str:
        prepared_sign = sign.strip()
        aliases = {
            "<": "<=",
            "<=": "<=",
            "≤": "<=",
            ">": ">=",
            ">=": ">=",
            "≥": ">=",
            "=": "=",
            "==": "=",
        }

        if prepared_sign not in aliases:
            raise ValueError(f"Недопустимый знак ограничения: {sign}")

        return aliases[prepared_sign]

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
