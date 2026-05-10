from __future__ import annotations

from fractions import Fraction
from typing import List, Optional


class MatrixTools:
    @staticmethod
    def solve_linear_system(coefficients: List[List[Fraction]], right_side: List[Fraction]) -> Optional[List[Fraction]]:
        row_count = len(coefficients)
        if row_count == 0:
            return []
        column_count = len(coefficients[0])
        if row_count != column_count:
            raise ValueError('Система должна быть квадратной.')
        if len(right_side) != row_count:
            raise ValueError('Размер правой части не совпадает с числом уравнений.')

        matrix = [coefficients[row_index][:] + [right_side[row_index]] for row_index in range(row_count)]

        for pivot_column in range(column_count):
            pivot_row = None
            for candidate_row in range(pivot_column, row_count):
                if matrix[candidate_row][pivot_column] != 0:
                    pivot_row = candidate_row
                    break

            if pivot_row is None:
                return None

            if pivot_row != pivot_column:
                matrix[pivot_column], matrix[pivot_row] = matrix[pivot_row], matrix[pivot_column]

            pivot_value = matrix[pivot_column][pivot_column]
            matrix[pivot_column] = [value / pivot_value for value in matrix[pivot_column]]

            for row_index in range(row_count):
                if row_index == pivot_column:
                    continue
                factor = matrix[row_index][pivot_column]
                if factor == 0:
                    continue
                matrix[row_index] = [
                    matrix[row_index][column_index] - factor * matrix[pivot_column][column_index]
                    for column_index in range(column_count + 1)
                ]

        return [matrix[row_index][-1] for row_index in range(row_count)]
