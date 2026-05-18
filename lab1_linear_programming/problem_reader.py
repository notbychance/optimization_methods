from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Optional

from linear_problem import Constraint, DerivedVariable, LinearProblem2D


class ProblemReader:
    @staticmethod
    def read(file_path: str) -> LinearProblem2D:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Файл с условием не найден: {file_path}")

        if path.suffix.lower() != ".json":
            raise ValueError("Сейчас поддерживается формат входного файла JSON.")

        data = json.loads(path.read_text(encoding="utf-8"))
        return ProblemReader._from_json(data)

    @staticmethod
    def _from_json(data: Dict[str, Any]) -> LinearProblem2D:
        objective_data = data.get("objective")
        if not isinstance(objective_data, dict):
            raise ValueError("В JSON должен быть объект objective.")

        objective_type = str(objective_data.get("type", objective_data.get("sense", "max"))).lower()
        if objective_type not in {"max", "min"}:
            raise ValueError("objective.type должен быть max или min.")

        objective_coefficients = objective_data.get("coefficients", objective_data.get("c"))
        if not isinstance(objective_coefficients, list):
            raise ValueError("В objective должен быть список coefficients.")
        if len(objective_coefficients) != 2:
            raise ValueError("Графический метод в этой программе поддерживает ровно 2 основные переменные.")

        objective = [ProblemReader._to_fraction(value) for value in objective_coefficients]

        variable_names = data.get("variable_names", ["x1", "x2"])
        if not isinstance(variable_names, list) or len(variable_names) != 2:
            raise ValueError("Поле variable_names должно содержать ровно 2 переменные.")
        variable_names = [str(value) for value in variable_names]

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

            if not isinstance(coefficients, list) or len(coefficients) != 2:
                raise ValueError(
                    f"В ограничении {index} должен быть список coefficients из 2 чисел."
                )

            constraints.append(
                Constraint(
                    name=str(raw_constraint.get("name", f"Ограничение {index}")),
                    coefficients=[ProblemReader._to_fraction(value) for value in coefficients],
                    sign=ProblemReader._normalize_sign(str(sign)),
                    rhs=ProblemReader._to_fraction(rhs),
                    description=str(raw_constraint.get("description", "")),
                )
            )

        variable_descriptions = data.get("variable_descriptions", {})
        if variable_descriptions is None:
            variable_descriptions = {}
        if not isinstance(variable_descriptions, dict):
            raise ValueError("Поле variable_descriptions должно быть объектом.")
        variable_descriptions = {
            str(name): str(description)
            for name, description in variable_descriptions.items()
        }

        derived_variables = ProblemReader._read_derived_variables(data.get("derived_variables", []))

        return LinearProblem2D(
            title=str(data.get("title", "Лабораторная работа №1")),
            variant=ProblemReader._read_optional_int(data.get("variant")),
            objective_type=objective_type,
            objective=objective,
            constraints=constraints,
            variable_names=variable_names,
            variable_descriptions=variable_descriptions,
            derived_variables=derived_variables,
            x_axis_label=str(data.get("x_axis_label", variable_names[0])),
            y_axis_label=str(data.get("y_axis_label", variable_names[1])),
            objective_description=str(objective_data.get("description", "")),
            note=str(data.get("note", "")),
        )

    @staticmethod
    def _read_derived_variables(raw_values: Any) -> List[DerivedVariable]:
        if raw_values is None:
            return []
        if not isinstance(raw_values, list):
            raise ValueError("Поле derived_variables должно быть списком.")

        derived_variables: List[DerivedVariable] = []
        for index, raw_value in enumerate(raw_values, start=1):
            if not isinstance(raw_value, dict):
                raise ValueError(f"Производная переменная {index} должна быть объектом.")

            coefficients = raw_value.get("coefficients", raw_value.get("a", [0, 0]))
            if not isinstance(coefficients, list) or len(coefficients) != 2:
                raise ValueError(
                    f"У производной переменной {index} должен быть список coefficients из 2 чисел."
                )

            derived_variables.append(
                DerivedVariable(
                    name=str(raw_value.get("name", f"d{index}")),
                    coefficients=[ProblemReader._to_fraction(value) for value in coefficients],
                    constant=ProblemReader._to_fraction(raw_value.get("constant", 0)),
                    description=str(raw_value.get("description", "")),
                    expression=str(raw_value.get("expression", "")),
                )
            )

        return derived_variables

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
    def _read_optional_int(value: Any) -> Optional[int]:
        if value is None:
            return None
        return int(value)

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
