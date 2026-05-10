from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fraction_tools import to_fraction
from linear_problem import Constraint, IntegerLinearProblem


class ProblemReader:
    @staticmethod
    def read(file_path: str) -> IntegerLinearProblem:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Файл с условием не найден: {file_path}")

        if path.suffix.lower() != ".json":
            raise ValueError("Поддерживается формат входного файла JSON.")

        data = json.loads(path.read_text(encoding="utf-8"))
        return ProblemReader._from_json(data)

    @staticmethod
    def _from_json(data: Dict[str, Any]) -> IntegerLinearProblem:
        objective_data = data.get("objective")
        if not isinstance(objective_data, dict):
            raise ValueError("В JSON должен быть объект objective.")

        objective_type = str(objective_data.get("type", objective_data.get("sense", "max"))).lower()
        objective_coefficients = objective_data.get("coefficients", objective_data.get("c"))
        if not isinstance(objective_coefficients, list):
            raise ValueError("В objective должен быть список coefficients.")

        objective = [to_fraction(value) for value in objective_coefficients]
        variable_count = len(objective)

        variable_names = data.get("variable_names")
        if variable_names is None:
            variable_names = [f"x{index + 1}" for index in range(variable_count)]
        if not isinstance(variable_names, list):
            raise ValueError("Поле variable_names должно быть списком строк.")
        variable_names = [str(value) for value in variable_names]

        variable_types = data.get("variable_types")
        if variable_types is None:
            variable_types = ["integer" for _ in range(variable_count)]
        if not isinstance(variable_types, list):
            raise ValueError("Поле variable_types должно быть списком строк.")
        variable_types = [ProblemReader._normalize_variable_type(value) for value in variable_types]

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
            name = str(raw_constraint.get("name", f"constraint_{index}"))

            if not isinstance(coefficients, list):
                raise ValueError(f"В ограничении {index} должен быть список coefficients.")

            constraints.append(
                Constraint(
                    coefficients=[to_fraction(value) for value in coefficients],
                    sign=ProblemReader._normalize_sign(str(sign)),
                    rhs=to_fraction(rhs),
                    name=name,
                )
            )

        max_nodes = int(data.get("max_nodes", 1000))
        if max_nodes <= 0:
            raise ValueError("max_nodes должен быть положительным целым числом.")

        return IntegerLinearProblem(
            objective_type=objective_type,
            objective=objective,
            constraints=constraints,
            variable_names=variable_names,
            variable_types=variable_types,
            max_nodes=max_nodes,
        )

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
    def _normalize_variable_type(value: Any) -> str:
        prepared_value = str(value).strip().lower()
        aliases = {
            "integer": "integer",
            "int": "integer",
            "целая": "integer",
            "целочисленная": "integer",
            "binary": "binary",
            "bin": "binary",
            "bool": "binary",
            "двоичная": "binary",
            "continuous": "continuous",
            "real": "continuous",
            "float": "continuous",
            "непрерывная": "continuous",
        }

        if prepared_value not in aliases:
            raise ValueError(f"Недопустимый тип переменной: {value}")

        return aliases[prepared_value]
