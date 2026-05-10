from __future__ import annotations

from fractions import Fraction
from typing import List


Matrix = List[List[Fraction]]
Vector = List[Fraction]


def identity_matrix(size: int) -> Matrix:
    return [
        [Fraction(1) if row_index == column_index else Fraction(0) for column_index in range(size)]
        for row_index in range(size)
    ]


def transpose(matrix: Matrix) -> Matrix:
    if len(matrix) == 0:
        return []
    return [[matrix[row_index][column_index] for row_index in range(len(matrix))] for column_index in range(len(matrix[0]))]


def matrix_multiply(left: Matrix, right: Matrix) -> Matrix:
    if len(left) == 0 or len(right) == 0:
        return []

    left_columns = len(left[0])
    right_rows = len(right)

    if left_columns != right_rows:
        raise ValueError("Количество столбцов первой матрицы должно совпадать с количеством строк второй матрицы.")

    result: Matrix = []
    for row_index in range(len(left)):
        result_row: List[Fraction] = []
        for column_index in range(len(right[0])):
            value = Fraction(0)
            for inner_index in range(left_columns):
                value += left[row_index][inner_index] * right[inner_index][column_index]
            result_row.append(value)
        result.append(result_row)
    return result


def matrix_vector_multiply(matrix: Matrix, vector: Vector) -> Vector:
    if len(matrix) == 0:
        return []

    if len(matrix[0]) != len(vector):
        raise ValueError("Количество столбцов матрицы должно совпадать с длиной вектора.")

    result: Vector = []
    for row in matrix:
        value = Fraction(0)
        for column_index, coefficient in enumerate(row):
            value += coefficient * vector[column_index]
        result.append(value)
    return result


def vector_matrix_multiply(vector: Vector, matrix: Matrix) -> Vector:
    if len(matrix) == 0:
        return []

    if len(vector) != len(matrix):
        raise ValueError("Длина вектора должна совпадать с количеством строк матрицы.")

    result: Vector = []
    for column_index in range(len(matrix[0])):
        value = Fraction(0)
        for row_index, vector_value in enumerate(vector):
            value += vector_value * matrix[row_index][column_index]
        result.append(value)
    return result


def select_columns(matrix: Matrix, column_indices: List[int]) -> Matrix:
    return [[row[column_index] for column_index in column_indices] for row in matrix]


def invert_matrix(matrix: Matrix) -> Matrix:
    size = len(matrix)

    if size == 0:
        return []

    for row in matrix:
        if len(row) != size:
            raise ValueError("Обратная матрица определяется только для квадратной матрицы.")

    augmented: Matrix = []
    identity = identity_matrix(size)
    for row_index in range(size):
        augmented.append(matrix[row_index][:] + identity[row_index][:])

    for pivot_index in range(size):
        pivot_row = None
        for candidate_row in range(pivot_index, size):
            if augmented[candidate_row][pivot_index] != 0:
                pivot_row = candidate_row
                break

        if pivot_row is None:
            raise ValueError("Матрица базиса вырождена, обратная матрица не существует.")

        if pivot_row != pivot_index:
            augmented[pivot_index], augmented[pivot_row] = augmented[pivot_row], augmented[pivot_index]

        pivot_value = augmented[pivot_index][pivot_index]
        augmented[pivot_index] = [value / pivot_value for value in augmented[pivot_index]]

        for row_index in range(size):
            if row_index == pivot_index:
                continue

            factor = augmented[row_index][pivot_index]
            if factor == 0:
                continue

            augmented[row_index] = [
                augmented[row_index][column_index] - factor * augmented[pivot_index][column_index]
                for column_index in range(size * 2)
            ]

    return [row[size:] for row in augmented]


def format_fraction(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def format_matrix(matrix: Matrix) -> List[List[str]]:
    return [[format_fraction(value) for value in row] for row in matrix]


def format_vector(vector: Vector) -> List[str]:
    return [format_fraction(value) for value in vector]
