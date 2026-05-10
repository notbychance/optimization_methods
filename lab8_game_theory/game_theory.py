from __future__ import annotations

from fractions import Fraction
from itertools import combinations
from typing import Dict, List, Optional, Sequence, Tuple

from game_models import (
    BimatrixGameProblem,
    BimatrixGameResult,
    CriterionResult,
    DecisionProblem,
    DecisionResult,
    MatrixGameProblem,
    MatrixGameResult,
    NashEquilibrium,
)
from matrix_tools import MatrixTools
from snapshot import SnapshotWriter


class MatrixGameSolver:
    def __init__(self, problem: MatrixGameProblem, snapshot_writer: Optional[SnapshotWriter] = None):
        self.problem = problem
        self.snapshot_writer = snapshot_writer

    def solve(self) -> MatrixGameResult:
        self._validate()
        matrix = self.problem.payoff_matrix
        row_names = self.problem.row_strategy_names
        column_names = self.problem.column_strategy_names

        self._snapshot_matrix(
            title='Исходная платежная матрица матричной игры',
            matrix=matrix,
            notes='Строки соответствуют стратегиям первого игрока, столбцы — стратегиям второго игрока. Значение — выигрыш первого игрока.',
        )

        saddle_points = self._find_saddle_points()
        if saddle_points:
            value = saddle_points[0][2]
            row_strategy = {name: Fraction(0) for name in row_names}
            column_strategy = {name: Fraction(0) for name in column_names}
            row_strategy[saddle_points[0][0]] = Fraction(1)
            column_strategy[saddle_points[0][1]] = Fraction(1)

            self._snapshot_saddle_point(saddle_points=saddle_points, value=value)

            return MatrixGameResult(
                status='optimal_pure',
                game_value=value,
                row_strategy_probabilities=row_strategy,
                column_strategy_probabilities=column_strategy,
                row_support=[saddle_points[0][0]],
                column_support=[saddle_points[0][1]],
                saddle_points=saddle_points,
                message='Найдена седловая точка. Оптимальные стратегии являются чистыми.',
            )

        self._snapshot_saddle_absence()
        mixed_result = self._solve_mixed_by_support_enumeration()
        return mixed_result

    def _validate(self) -> None:
        matrix = self.problem.payoff_matrix
        if len(matrix) == 0 or len(matrix[0]) == 0:
            raise ValueError('Платежная матрица не должна быть пустой.')

        column_count = len(matrix[0])
        for row in matrix:
            if len(row) != column_count:
                raise ValueError('Все строки платежной матрицы должны иметь одинаковую длину.')

        if len(self.problem.row_strategy_names) != len(matrix):
            raise ValueError('Количество названий строковых стратегий не совпадает с числом строк матрицы.')

        if len(self.problem.column_strategy_names) != column_count:
            raise ValueError('Количество названий столбцовых стратегий не совпадает с числом столбцов матрицы.')

    def _find_saddle_points(self) -> List[Tuple[str, str, Fraction]]:
        matrix = self.problem.payoff_matrix
        row_names = self.problem.row_strategy_names
        column_names = self.problem.column_strategy_names

        row_minima = [min(row) for row in matrix]
        column_maxima = [max(matrix[row_index][column_index] for row_index in range(len(matrix))) for column_index in range(len(matrix[0]))]
        lower_price = max(row_minima)
        upper_price = min(column_maxima)

        table_rows: List[List[object]] = []
        for row_index, row in enumerate(matrix):
            table_rows.append([row_names[row_index], row, row_minima[row_index]])

        if self.snapshot_writer is not None:
            self.snapshot_writer.write_table(
                title='Проверка нижней цены игры',
                headers=['Стратегия первого игрока', 'Выигрыши по состояниям второго игрока', 'Минимальный выигрыш строки'],
                rows=table_rows,
                notes=f'Нижняя цена игры: max(min строк) = {self.snapshot_writer.format_number(lower_price)}.',
            )
            self.snapshot_writer.write_table(
                title='Проверка верхней цены игры',
                headers=['Стратегия второго игрока', 'Максимальный выигрыш в столбце'],
                rows=[[column_names[column_index], column_maxima[column_index]] for column_index in range(len(column_names))],
                notes=f'Верхняя цена игры: min(max столбцов) = {self.snapshot_writer.format_number(upper_price)}.',
            )

        if lower_price != upper_price:
            return []

        saddle_points: List[Tuple[str, str, Fraction]] = []
        for row_index in range(len(matrix)):
            for column_index in range(len(matrix[0])):
                if matrix[row_index][column_index] == lower_price:
                    if row_minima[row_index] == lower_price and column_maxima[column_index] == lower_price:
                        saddle_points.append((row_names[row_index], column_names[column_index], lower_price))

        return saddle_points

    def _solve_mixed_by_support_enumeration(self) -> MatrixGameResult:
        matrix = self.problem.payoff_matrix
        row_count = len(matrix)
        column_count = len(matrix[0])
        max_support_size = min(row_count, column_count)

        if self.snapshot_writer is not None:
            self.snapshot_writer.write_text(
                title='Переход к смешанным стратегиям',
                text='Седловая точка отсутствует, поэтому выполняется перебор равновесных носителей смешанных стратегий. Для каждого носителя решаются системы без использования библиотек оптимизации.',
            )

        for support_size in range(1, max_support_size + 1):
            for row_support in combinations(range(row_count), support_size):
                for column_support in combinations(range(column_count), support_size):
                    solution = self._try_support(row_support=list(row_support), column_support=list(column_support))
                    if solution is None:
                        continue

                    row_probabilities, column_probabilities, game_value = solution
                    row_strategy = {
                        self.problem.row_strategy_names[index]: row_probabilities[index]
                        for index in range(row_count)
                    }
                    column_strategy = {
                        self.problem.column_strategy_names[index]: column_probabilities[index]
                        for index in range(column_count)
                    }

                    if self.snapshot_writer is not None:
                        self.snapshot_writer.write_table(
                            title='Найден допустимый носитель смешанных стратегий',
                            headers=['Параметр', 'Значение'],
                            rows=[
                                ['Носитель первого игрока', [self.problem.row_strategy_names[index] for index in row_support]],
                                ['Носитель второго игрока', [self.problem.column_strategy_names[index] for index in column_support]],
                                ['Цена игры', game_value],
                                ['Смешанная стратегия первого игрока', [row_strategy[name] for name in self.problem.row_strategy_names]],
                                ['Смешанная стратегия второго игрока', [column_strategy[name] for name in self.problem.column_strategy_names]],
                            ],
                            notes='Носитель удовлетворяет условиям равновесия: активные стратегии дают цену игры, неактивные стратегии не дают выгодного отклонения.',
                        )

                    return MatrixGameResult(
                        status='optimal_mixed',
                        game_value=game_value,
                        row_strategy_probabilities=row_strategy,
                        column_strategy_probabilities=column_strategy,
                        row_support=[self.problem.row_strategy_names[index] for index in row_support],
                        column_support=[self.problem.column_strategy_names[index] for index in column_support],
                        saddle_points=[],
                        message='Седловая точка отсутствует. Найдено решение в смешанных стратегиях.',
                    )

        return MatrixGameResult(
            status='not_found',
            game_value=None,
            row_strategy_probabilities={name: Fraction(0) for name in self.problem.row_strategy_names},
            column_strategy_probabilities={name: Fraction(0) for name in self.problem.column_strategy_names},
            row_support=[],
            column_support=[],
            saddle_points=[],
            message='Не удалось найти смешанное решение перебором носителей. Проверьте корректность платежной матрицы.',
        )

    def _try_support(
        self,
        row_support: List[int],
        column_support: List[int],
    ) -> Optional[Tuple[List[Fraction], List[Fraction], Fraction]]:
        matrix = self.problem.payoff_matrix
        row_count = len(matrix)
        column_count = len(matrix[0])
        support_size = len(row_support)

        column_strategy_solution = self._solve_column_player_mixture(row_support=row_support, column_support=column_support)
        if column_strategy_solution is None:
            self._snapshot_rejected_support(row_support, column_support, 'Система для стратегии второго игрока вырождена.')
            return None
        column_support_probabilities, value_from_columns = column_strategy_solution

        row_strategy_solution = self._solve_row_player_mixture(row_support=row_support, column_support=column_support)
        if row_strategy_solution is None:
            self._snapshot_rejected_support(row_support, column_support, 'Система для стратегии первого игрока вырождена.')
            return None
        row_support_probabilities, value_from_rows = row_strategy_solution

        if value_from_columns != value_from_rows:
            self._snapshot_rejected_support(row_support, column_support, 'Цена игры из двух систем не совпала.')
            return None

        if any(probability < 0 for probability in column_support_probabilities):
            self._snapshot_rejected_support(row_support, column_support, 'Стратегия второго игрока содержит отрицательную вероятность.')
            return None

        if any(probability < 0 for probability in row_support_probabilities):
            self._snapshot_rejected_support(row_support, column_support, 'Стратегия первого игрока содержит отрицательную вероятность.')
            return None

        full_column_probabilities = [Fraction(0) for _ in range(column_count)]
        for local_index, column_index in enumerate(column_support):
            full_column_probabilities[column_index] = column_support_probabilities[local_index]

        full_row_probabilities = [Fraction(0) for _ in range(row_count)]
        for local_index, row_index in enumerate(row_support):
            full_row_probabilities[row_index] = row_support_probabilities[local_index]

        game_value = value_from_columns

        expected_by_rows = [
            sum(matrix[row_index][column_index] * full_column_probabilities[column_index] for column_index in range(column_count))
            for row_index in range(row_count)
        ]
        expected_by_columns = [
            sum(full_row_probabilities[row_index] * matrix[row_index][column_index] for row_index in range(row_count))
            for column_index in range(column_count)
        ]

        if any(expected_value > game_value for expected_value in expected_by_rows):
            self._snapshot_rejected_support(row_support, column_support, 'У первого игрока есть строка, дающая выигрыш выше цены игры.')
            return None

        if any(expected_value < game_value for expected_value in expected_by_columns):
            self._snapshot_rejected_support(row_support, column_support, 'У второго игрока есть столбец, уменьшающий выигрыш первого игрока ниже цены игры.')
            return None

        self._snapshot_checked_support(
            row_support=row_support,
            column_support=column_support,
            full_row_probabilities=full_row_probabilities,
            full_column_probabilities=full_column_probabilities,
            game_value=game_value,
            expected_by_rows=expected_by_rows,
            expected_by_columns=expected_by_columns,
        )

        return full_row_probabilities, full_column_probabilities, game_value

    def _solve_column_player_mixture(self, row_support: List[int], column_support: List[int]) -> Optional[Tuple[List[Fraction], Fraction]]:
        matrix = self.problem.payoff_matrix
        support_size = len(row_support)
        coefficients: List[List[Fraction]] = []
        right_side: List[Fraction] = []

        for row_index in row_support:
            coefficients.append([matrix[row_index][column_index] for column_index in column_support] + [Fraction(-1)])
            right_side.append(Fraction(0))

        coefficients.append([Fraction(1) for _ in range(support_size)] + [Fraction(0)])
        right_side.append(Fraction(1))

        solution = MatrixTools.solve_linear_system(coefficients, right_side)
        if solution is None:
            return None
        probabilities = solution[:-1]
        game_value = solution[-1]
        return probabilities, game_value

    def _solve_row_player_mixture(self, row_support: List[int], column_support: List[int]) -> Optional[Tuple[List[Fraction], Fraction]]:
        matrix = self.problem.payoff_matrix
        support_size = len(row_support)
        coefficients: List[List[Fraction]] = []
        right_side: List[Fraction] = []

        for column_index in column_support:
            coefficients.append([matrix[row_index][column_index] for row_index in row_support] + [Fraction(-1)])
            right_side.append(Fraction(0))

        coefficients.append([Fraction(1) for _ in range(support_size)] + [Fraction(0)])
        right_side.append(Fraction(1))

        solution = MatrixTools.solve_linear_system(coefficients, right_side)
        if solution is None:
            return None
        probabilities = solution[:-1]
        game_value = solution[-1]
        return probabilities, game_value

    def _snapshot_matrix(self, title: str, matrix: List[List[Fraction]], notes: str) -> None:
        if self.snapshot_writer is None:
            return
        self.snapshot_writer.write_matrix(
            title=title,
            matrix=matrix,
            row_names=self.problem.row_strategy_names,
            column_names=self.problem.column_strategy_names,
            notes=notes,
        )

    def _snapshot_saddle_point(self, saddle_points: List[Tuple[str, str, Fraction]], value: Fraction) -> None:
        if self.snapshot_writer is None:
            return
        self.snapshot_writer.write_table(
            title='Седловая точка найдена',
            headers=['Стратегия первого игрока', 'Стратегия второго игрока', 'Цена игры'],
            rows=saddle_points,
            notes=f'Нижняя и верхняя цена игры совпадают: {self.snapshot_writer.format_number(value)}.',
        )

    def _snapshot_saddle_absence(self) -> None:
        if self.snapshot_writer is None:
            return
        self.snapshot_writer.write_text(
            title='Седловая точка отсутствует',
            text='Нижняя и верхняя цена игры не совпали. Требуется поиск решения в смешанных стратегиях.',
        )

    def _snapshot_rejected_support(self, row_support: List[int], column_support: List[int], reason: str) -> None:
        if self.snapshot_writer is None:
            return
        self.snapshot_writer.write_table(
            title='Проверка носителя смешанных стратегий',
            headers=['Параметр', 'Значение'],
            rows=[
                ['Носитель первого игрока', [self.problem.row_strategy_names[index] for index in row_support]],
                ['Носитель второго игрока', [self.problem.column_strategy_names[index] for index in column_support]],
                ['Результат проверки', reason],
            ],
        )

    def _snapshot_checked_support(
        self,
        row_support: List[int],
        column_support: List[int],
        full_row_probabilities: List[Fraction],
        full_column_probabilities: List[Fraction],
        game_value: Fraction,
        expected_by_rows: List[Fraction],
        expected_by_columns: List[Fraction],
    ) -> None:
        if self.snapshot_writer is None:
            return
        self.snapshot_writer.write_table(
            title='Подробная проверка допустимого носителя',
            headers=['Параметр', 'Значение'],
            rows=[
                ['Носитель первого игрока', [self.problem.row_strategy_names[index] for index in row_support]],
                ['Носитель второго игрока', [self.problem.column_strategy_names[index] for index in column_support]],
                ['Вероятности первого игрока', full_row_probabilities],
                ['Вероятности второго игрока', full_column_probabilities],
                ['Цена игры', game_value],
                ['Ожидаемые выигрыши строк против стратегии второго игрока', expected_by_rows],
                ['Ожидаемые выигрыши столбцов против стратегии первого игрока', expected_by_columns],
            ],
        )


class DecisionCriteriaSolver:
    def __init__(self, problem: DecisionProblem, snapshot_writer: Optional[SnapshotWriter] = None):
        self.problem = problem
        self.snapshot_writer = snapshot_writer

    def solve(self) -> DecisionResult:
        self._validate()
        utility_matrix = self._build_utility_matrix()

        if self.snapshot_writer is not None:
            self.snapshot_writer.write_matrix(
                title='Исходная матрица решений',
                matrix=self.problem.payoff_matrix,
                row_names=self.problem.alternative_names,
                column_names=self.problem.state_names,
                notes='Строки — альтернативы лица, принимающего решение; столбцы — возможные состояния среды.',
            )
            if self.problem.objective == 'min':
                self.snapshot_writer.write_matrix(
                    title='Преобразованная матрица полезности',
                    matrix=utility_matrix,
                    row_names=self.problem.alternative_names,
                    column_names=self.problem.state_names,
                    notes='Задача минимизации преобразована к максимизации полезности путем смены знака элементов.',
                )

        results: List[CriterionResult] = []
        results.append(self._wald(utility_matrix))
        results.append(self._maximax(utility_matrix))
        results.append(self._laplace(utility_matrix))
        results.append(self._hurwicz(utility_matrix))
        results.append(self._savage(utility_matrix))

        if self.problem.probabilities is not None:
            results.append(self._bayes(utility_matrix))

        if self.snapshot_writer is not None:
            self._write_decision_summary(results)

        return DecisionResult(
            status='calculated',
            criteria=results,
            message='Критерии принятия решений рассчитаны.',
        )

    def _validate(self) -> None:
        matrix = self.problem.payoff_matrix
        if self.problem.objective not in {'max', 'min'}:
            raise ValueError("Поле objective должно быть 'max' или 'min'.")
        if len(matrix) == 0 or len(matrix[0]) == 0:
            raise ValueError('Матрица решений не должна быть пустой.')
        column_count = len(matrix[0])
        for row in matrix:
            if len(row) != column_count:
                raise ValueError('Все строки матрицы решений должны иметь одинаковую длину.')
        if len(self.problem.alternative_names) != len(matrix):
            raise ValueError('Количество альтернатив не совпадает с числом строк матрицы.')
        if len(self.problem.state_names) != column_count:
            raise ValueError('Количество состояний среды не совпадает с числом столбцов матрицы.')
        if self.problem.probabilities is not None:
            if len(self.problem.probabilities) != column_count:
                raise ValueError('Количество вероятностей должно совпадать с числом состояний среды.')
            if sum(self.problem.probabilities) != Fraction(1):
                raise ValueError('Сумма вероятностей состояний должна быть равна 1.')
        if self.problem.hurwicz_alpha < 0 or self.problem.hurwicz_alpha > 1:
            raise ValueError('Коэффициент Гурвица должен находиться в диапазоне [0; 1].')

    def _build_utility_matrix(self) -> List[List[Fraction]]:
        if self.problem.objective == 'max':
            return [row[:] for row in self.problem.payoff_matrix]
        return [[-value for value in row] for row in self.problem.payoff_matrix]

    def _wald(self, utility_matrix: List[List[Fraction]]) -> CriterionResult:
        values = {self.problem.alternative_names[index]: min(row) for index, row in enumerate(utility_matrix)}
        result = self._select_maximum('Критерий Вальда', values)
        self._snapshot_criterion(result, 'Для каждой альтернативы берется худшее значение, затем выбирается максимум из худших исходов.')
        return result

    def _maximax(self, utility_matrix: List[List[Fraction]]) -> CriterionResult:
        values = {self.problem.alternative_names[index]: max(row) for index, row in enumerate(utility_matrix)}
        result = self._select_maximum('Критерий максимакса', values)
        self._snapshot_criterion(result, 'Для каждой альтернативы берется лучший исход, затем выбирается максимум.')
        return result

    def _laplace(self, utility_matrix: List[List[Fraction]]) -> CriterionResult:
        values = {
            self.problem.alternative_names[index]: sum(row) / len(row)
            for index, row in enumerate(utility_matrix)
        }
        result = self._select_maximum('Критерий Лапласа', values)
        self._snapshot_criterion(result, 'Состояния среды считаются равновероятными; выбирается максимум среднего выигрыша.')
        return result

    def _hurwicz(self, utility_matrix: List[List[Fraction]]) -> CriterionResult:
        alpha = self.problem.hurwicz_alpha
        values = {
            self.problem.alternative_names[index]: alpha * max(row) + (Fraction(1) - alpha) * min(row)
            for index, row in enumerate(utility_matrix)
        }
        result = self._select_maximum('Критерий Гурвица', values)
        self._snapshot_criterion(
            result,
            f'Коэффициент оптимизма alpha = {SnapshotWriter.format_number(alpha)}. Значение: alpha * лучший исход + (1 - alpha) * худший исход.',
        )
        return result

    def _savage(self, utility_matrix: List[List[Fraction]]) -> CriterionResult:
        column_maxima = [max(utility_matrix[row_index][column_index] for row_index in range(len(utility_matrix))) for column_index in range(len(utility_matrix[0]))]
        regret_matrix = [
            [column_maxima[column_index] - utility_matrix[row_index][column_index] for column_index in range(len(column_maxima))]
            for row_index in range(len(utility_matrix))
        ]

        if self.snapshot_writer is not None:
            self.snapshot_writer.write_matrix(
                title='Матрица сожалений для критерия Сэвиджа',
                matrix=regret_matrix,
                row_names=self.problem.alternative_names,
                column_names=self.problem.state_names,
                notes='Элемент матрицы сожалений показывает потерю относительно лучшей альтернативы в данном состоянии среды.',
            )

        values = {
            self.problem.alternative_names[index]: max(row)
            for index, row in enumerate(regret_matrix)
        }
        best_value = min(values.values())
        best_alternatives = [name for name, value in values.items() if value == best_value]
        result = CriterionResult(
            criterion_name='Критерий Сэвиджа',
            values_by_alternative=values,
            best_value=best_value,
            best_alternatives=best_alternatives,
        )
        self._snapshot_criterion(result, 'Выбирается альтернатива с минимальным максимальным сожалением.')
        return result

    def _bayes(self, utility_matrix: List[List[Fraction]]) -> CriterionResult:
        if self.problem.probabilities is None:
            raise ValueError('Для критерия Байеса не заданы вероятности состояний.')
        values = {
            self.problem.alternative_names[row_index]: sum(
                utility_matrix[row_index][column_index] * self.problem.probabilities[column_index]
                for column_index in range(len(self.problem.probabilities))
            )
            for row_index in range(len(utility_matrix))
        }
        result = self._select_maximum('Критерий Байеса', values)
        self._snapshot_criterion(result, 'Выбирается максимум математического ожидания полезности с учетом заданных вероятностей состояний.')
        return result

    def _select_maximum(self, criterion_name: str, values: Dict[str, Fraction]) -> CriterionResult:
        best_value = max(values.values())
        best_alternatives = [name for name, value in values.items() if value == best_value]
        return CriterionResult(
            criterion_name=criterion_name,
            values_by_alternative=values,
            best_value=best_value,
            best_alternatives=best_alternatives,
        )

    def _snapshot_criterion(self, result: CriterionResult, notes: str) -> None:
        if self.snapshot_writer is None:
            return
        self.snapshot_writer.write_table(
            title=result.criterion_name,
            headers=['Альтернатива', 'Значение критерия'],
            rows=[[name, value] for name, value in result.values_by_alternative.items()],
            notes=f'{notes} Лучшее значение: {SnapshotWriter.format_number(result.best_value)}. Лучшие альтернативы: {", ".join(result.best_alternatives)}.',
        )

    def _write_decision_summary(self, results: List[CriterionResult]) -> None:
        if self.snapshot_writer is None:
            return
        self.snapshot_writer.write_table(
            title='Итоговая таблица критериев принятия решений',
            headers=['Критерий', 'Лучшее значение', 'Рекомендуемые альтернативы'],
            rows=[
                [result.criterion_name, result.best_value, ', '.join(result.best_alternatives)]
                for result in results
            ],
        )


class BimatrixGameSolver:
    def __init__(self, problem: BimatrixGameProblem, snapshot_writer: Optional[SnapshotWriter] = None):
        self.problem = problem
        self.snapshot_writer = snapshot_writer

    def solve(self) -> BimatrixGameResult:
        self._validate()

        if self.snapshot_writer is not None:
            self.snapshot_writer.write_matrix(
                title='Матрица выигрышей первого игрока',
                matrix=self.problem.row_player_matrix,
                row_names=self.problem.row_strategy_names,
                column_names=self.problem.column_strategy_names,
            )
            self.snapshot_writer.write_matrix(
                title='Матрица выигрышей второго игрока',
                matrix=self.problem.column_player_matrix,
                row_names=self.problem.row_strategy_names,
                column_names=self.problem.column_strategy_names,
            )

        equilibria: List[NashEquilibrium] = []
        row_count = len(self.problem.row_player_matrix)
        column_count = len(self.problem.row_player_matrix[0])

        for row_index in range(row_count):
            for column_index in range(column_count):
                row_payoff = self.problem.row_player_matrix[row_index][column_index]
                column_payoff = self.problem.column_player_matrix[row_index][column_index]

                row_player_best_response_value = max(
                    self.problem.row_player_matrix[alternative_row][column_index]
                    for alternative_row in range(row_count)
                )
                column_player_best_response_value = max(
                    self.problem.column_player_matrix[row_index][alternative_column]
                    for alternative_column in range(column_count)
                )

                is_row_player_best_response = row_payoff == row_player_best_response_value
                is_column_player_best_response = column_payoff == column_player_best_response_value

                if self.snapshot_writer is not None:
                    self.snapshot_writer.write_table(
                        title='Проверка клетки биматричной игры',
                        headers=['Параметр', 'Значение'],
                        rows=[
                            ['Стратегия первого игрока', self.problem.row_strategy_names[row_index]],
                            ['Стратегия второго игрока', self.problem.column_strategy_names[column_index]],
                            ['Выигрыш первого игрока', row_payoff],
                            ['Лучший ответ первого игрока на выбранный столбец', is_row_player_best_response],
                            ['Выигрыш второго игрока', column_payoff],
                            ['Лучший ответ второго игрока на выбранную строку', is_column_player_best_response],
                        ],
                    )

                if is_row_player_best_response and is_column_player_best_response:
                    equilibria.append(
                        NashEquilibrium(
                            row_strategy=self.problem.row_strategy_names[row_index],
                            column_strategy=self.problem.column_strategy_names[column_index],
                            row_player_payoff=row_payoff,
                            column_player_payoff=column_payoff,
                        )
                    )

        if self.snapshot_writer is not None:
            self.snapshot_writer.write_table(
                title='Итоговые равновесия Нэша в чистых стратегиях',
                headers=['Стратегия первого игрока', 'Стратегия второго игрока', 'Выигрыш первого игрока', 'Выигрыш второго игрока'],
                rows=[
                    [equilibrium.row_strategy, equilibrium.column_strategy, equilibrium.row_player_payoff, equilibrium.column_player_payoff]
                    for equilibrium in equilibria
                ] or [['-', '-', '-', '-']],
            )

        return BimatrixGameResult(
            status='calculated',
            pure_equilibria=equilibria,
            message='Равновесия Нэша в чистых стратегиях рассчитаны.' if equilibria else 'Равновесия Нэша в чистых стратегиях не найдены.',
        )

    def _validate(self) -> None:
        first = self.problem.row_player_matrix
        second = self.problem.column_player_matrix
        if len(first) == 0 or len(first[0]) == 0:
            raise ValueError('Матрица выигрышей первого игрока не должна быть пустой.')
        if len(first) != len(second) or len(first[0]) != len(second[0]):
            raise ValueError('Матрицы выигрышей игроков должны иметь одинаковый размер.')
        column_count = len(first[0])
        for row in first + second:
            if len(row) != column_count:
                raise ValueError('Все строки матриц должны иметь одинаковую длину.')
        if len(self.problem.row_strategy_names) != len(first):
            raise ValueError('Количество стратегий первого игрока не совпадает с числом строк.')
        if len(self.problem.column_strategy_names) != column_count:
            raise ValueError('Количество стратегий второго игрока не совпадает с числом столбцов.')
