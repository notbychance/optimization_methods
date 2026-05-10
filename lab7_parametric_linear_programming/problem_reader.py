from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from linear_problem import ParametricConstraint, ParametricLinearProblem, ParametricVector


class ProblemReader:
    @staticmethod
    def read(file_path: str) -> ParametricLinearProblem:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл с условием не найден: {file_path}")
        if path.suffix.lower() != ".json":
            raise ValueError("Поддерживается только формат JSON.")
        data = json.loads(path.read_text(encoding="utf-8"))
        return ProblemReader._from_json(data)

    @staticmethod
    def _from_json(data: Dict[str, Any]) -> ParametricLinearProblem:
        parameter_name = str(data.get("parameter_name", "lambda"))
        parameter_interval = ProblemReader._read_interval(data.get("parameter_interval", [None, None]))

        objective_data = data.get("objective")
        if not isinstance(objective_data, dict):
            raise ValueError("В JSON должен быть объект objective.")

        objective_type = str(objective_data.get("type", objective_data.get("sense", "max"))).lower()
        objective_base = ProblemReader._read_fraction_list(objective_data.get("base", objective_data.get("coefficients")), "objective.base")
        objective_parameter = ProblemReader._read_fraction_list(
            objective_data.get("parameter", [0 for _ in objective_base]),
            "objective.parameter",
        )

        if len(objective_base) != len(objective_parameter):
            raise ValueError("objective.base и objective.parameter должны иметь одинаковую длину.")

        raw_constraints = data.get("constraints")
        if not isinstance(raw_constraints, list) or len(raw_constraints) == 0:
            raise ValueError("В JSON должен быть непустой список constraints.")

        constraints: List[ParametricConstraint] = []
        for constraint_index, raw_constraint in enumerate(raw_constraints, start=1):
            if not isinstance(raw_constraint, dict):
                raise ValueError(f"Ограничение {constraint_index} должно быть объектом.")

            coefficients = ProblemReader._read_fraction_list(
                raw_constraint.get("coefficients", raw_constraint.get("a")),
                f"constraints[{constraint_index}].coefficients",
            )
            if len(coefficients) != len(objective_base):
                raise ValueError(f"В ограничении {constraint_index} количество коэффициентов не совпадает с целевой функцией.")

            sign = ProblemReader._normalize_sign(str(raw_constraint.get("sign", raw_constraint.get("operator", "<="))))
            rhs_value = raw_constraint.get("rhs", raw_constraint.get("b"))
            if isinstance(rhs_value, dict):
                rhs_base = ProblemReader._to_fraction(rhs_value.get("base", 0))
                rhs_parameter = ProblemReader._to_fraction(rhs_value.get("parameter", 0))
            else:
                rhs_base = ProblemReader._to_fraction(rhs_value)
                rhs_parameter = ProblemReader._to_fraction(raw_constraint.get("rhs_parameter", 0))

            constraints.append(
                ParametricConstraint(
                    coefficients=coefficients,
                    sign=sign,
                    rhs_base=rhs_base,
                    rhs_parameter=rhs_parameter,
                )
            )

        variable_names = data.get("variable_names")
        if variable_names is not None:
            if not isinstance(variable_names, list):
                raise ValueError("Поле variable_names должно быть списком строк.")
            variable_names = [str(value) for value in variable_names]
            if len(variable_names) != len(objective_base):
                raise ValueError("Количество имен переменных должно совпадать с количеством коэффициентов целевой функции.")

        return ParametricLinearProblem(
            objective_type=objective_type,
            objective=ParametricVector(base=objective_base, parameter=objective_parameter),
            constraints=constraints,
            parameter_name=parameter_name,
            parameter_interval=parameter_interval,
            variable_names=variable_names,
        )

    @staticmethod
    def _read_fraction_list(raw_value: Any, field_name: str) -> List[Fraction]:
        if not isinstance(raw_value, list):
            raise ValueError(f"Поле {field_name} должно быть списком чисел.")
        return [ProblemReader._to_fraction(value) for value in raw_value]

    @staticmethod
    def _read_interval(raw_value: Any) -> Tuple[Optional[Fraction], Optional[Fraction]]:
        if raw_value is None:
            return None, None
        if not isinstance(raw_value, list) or len(raw_value) != 2:
            raise ValueError("parameter_interval должен быть списком из двух значений: [min, max].")
        left = None if raw_value[0] is None else ProblemReader._to_fraction(raw_value[0])
        right = None if raw_value[1] is None else ProblemReader._to_fraction(raw_value[1])
        if left is not None and right is not None and left > right:
            raise ValueError("Левая граница parameter_interval не может быть больше правой.")
        return left, right

    @staticmethod
    def _normalize_sign(sign: str) -> str:
        normalized = sign.strip()
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
        if normalized not in aliases:
            raise ValueError(f"Недопустимый знак ограничения: {sign}")
        return aliases[normalized]

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
            prepared = value.strip().replace(",", ".")
            if prepared == "":
                raise ValueError("Пустая строка не может быть преобразована в число.")
            return Fraction(prepared)
        raise ValueError(f"Невозможно преобразовать значение в число: {value}")
