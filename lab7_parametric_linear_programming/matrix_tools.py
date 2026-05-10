from __future__ import annotations

from fractions import Fraction
from typing import List, Sequence


Matrix = List[List[Fraction]]
Vector = List[Fraction]


def identity_matrix(size: int) -> Matrix:
    return [
        [Fraction(1) if row_index == column_index else Fraction(0) for column_index in range(size)]
        for row_index in range(size)
    ]


def transpose(matrix: Matrix) -> Matrix:
    if not matrix:
        return []
    return [[matrix[row_index][column_index] for row_index in range(len(matrix))] for column_index in range(len(matrix[0]))]


def get_column(matrix: Matrix, column_index: int) -> Vector:
    return [row[column_index] for row in matrix]


def select_columns(matrix: Matrix, column_indices: Sequence[int]) -> Matrix:
    return [[row[column_index] for column_index in column_indices] for row in matrix]


def multiply_matrix_vector(matrix: Matrix, vector: Vector) -> Vector:
    return [sum(row[index] * vector[index] for index in range(len(vector))) for row in matrix]


def multiply_row_matrix(row: Vector, matrix: Matrix) -> Vector:
    if not matrix:
        return []
    column_count = len(matrix[0])
    return [sum(row[index] * matrix[index][column_index] for index in range(len(row))) for column_index in range(column_count)]


def dot(left: Vector, right: Vector) -> Fraction:
    return sum(left[index] * right[index] for index in range(len(left)))


def inverse_matrix(matrix: Matrix) -> Matrix:
    size = len(matrix)
    if size == 0:
        raise ValueError("Нельзя обратить пустую матрицу.")

    if any(len(row) != size for row in matrix):
        raise ValueError("Обратная матрица существует только для квадратной матрицы.")

    augmented = [matrix[row_index][:] + identity_matrix(size)[row_index] for row_index in range(size)]

    for column_index in range(size):
        pivot_row = None
        for candidate_row in range(column_index, size):
            if augmented[candidate_row][column_index] != 0:
                pivot_row = candidate_row
                break

        if pivot_row is None:
            raise ValueError("Матрица вырождена, обратная матрица не существует.")

        if pivot_row != column_index:
            augmented[column_index], augmented[pivot_row] = augmented[pivot_row], augmented[column_index]

        pivot_value = augmented[column_index][column_index]
        augmented[column_index] = [value / pivot_value for value in augmented[column_index]]

        for row_index in range(size):
            if row_index == column_index:
                continue
            factor = augmented[row_index][column_index]
            if factor == 0:
                continue
            augmented[row_index] = [
                augmented[row_index][value_index] - factor * augmented[column_index][value_index]
                for value_index in range(2 * size)
            ]

    return [row[size:] for row in augmented]


def matrix_to_text(matrix: Matrix) -> List[List[str]]:
    return [[format_fraction(value) for value in row] for row in matrix]


def vector_to_text(vector: Vector) -> List[str]:
    return [format_fraction(value) for value in vector]


def format_fraction(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"
