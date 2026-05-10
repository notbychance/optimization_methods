from __future__ import annotations

from fractions import Fraction
from typing import Any


def to_fraction(value: Any) -> Fraction:
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


def format_fraction(value: Fraction | None) -> str:
    if value is None:
        return "-"
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def format_decimal(value: Fraction | None, digits: int = 6) -> str:
    if value is None:
        return "-"
    return f"{float(value):.{digits}f}"


def is_integer(value: Fraction) -> bool:
    return value.denominator == 1


def floor_fraction(value: Fraction) -> Fraction:
    return Fraction(value.numerator // value.denominator, 1)


def ceil_fraction(value: Fraction) -> Fraction:
    return Fraction(-((-value.numerator) // value.denominator), 1)
