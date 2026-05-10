from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List

from simplex import Constraint, LinearProblem


class ProblemReader:
    @staticmethod
    def read(file_path: str) -> LinearProblem:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Файл с условием не найден: {file_path}")

        if path.suffix.lower() != ".json":
            raise ValueError("Сейчас поддерживается формат входного файла JSON.")

        data = json.loads(path.read_text(encoding="utf-8"))
        return ProblemReader._from_json(data)

    @staticmethod
    def _from_json(data: Dict[str, Any]) -> LinearProblem:
        objective_data = data.get("objective")
        if not isinstance(objective_data, dict):
            raise ValueError("В JSON должен быть объект objective.")

        objective_type = objective_data.get("type", objective_data.get("sense", "max"))
        objective_type = str(objective_type).lower()

        objective_coefficients = objective_data.get(
            "coefficients", objective_data.get("c")
        )
        if not isinstance(objective_coefficients, list):
            raise ValueError("В objective должен быть список coefficients.")

        objective = [
            ProblemReader._to_fraction(value) for value in objective_coefficients
        ]

        raw_constraints = data.get("constraints")
        if not isinstance(raw_constraints, list):
            raise ValueError("В JSON должен быть список constraints.")

        constraints: List[Constraint] = []
        for index, raw_constraint in enumerate(raw_constraints, start=1):
            if not isinstance(raw_constraint, dict):
                raise ValueError(f"Ограничение {index} должно быть объектом.")

            coefficients = raw_constraint.get("coefficients", raw_constraint.get("a"))
            sign = raw_constraint.get("sign", raw_constraint.get("operator"))
            rhs = raw_constraint.get("rhs", raw_constraint.get("b"))

            if not isinstance(coefficients, list):
                raise ValueError(
                    f"В ограничении {index} должен быть список coefficients."
                )

            normalized_sign = ProblemReader._normalize_sign(str(sign))

            constraints.append(
                Constraint(
                    coefficients=[
                        ProblemReader._to_fraction(value) for value in coefficients
                    ],
                    sign=normalized_sign,
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
    def _normalize_sign(sign: str) -> str:
        sign = sign.strip()

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

        if sign not in aliases:
            raise ValueError(f"Недопустимый знак ограничения: {sign}")

        return aliases[sign]

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
