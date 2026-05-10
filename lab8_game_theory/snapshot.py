from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Iterable, List, Sequence


class SnapshotWriter:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if self.file_path.parent != Path('.'):
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text('# Снимки алгоритма для ЛР 8\n\n', encoding='utf-8')

    def write_text(self, title: str, text: str) -> None:
        lines = [f'## {title}', '', text, '', '']
        self._append_lines(lines)

    def write_matrix(
        self,
        title: str,
        matrix: Sequence[Sequence[Fraction]],
        row_names: Sequence[str] | None = None,
        column_names: Sequence[str] | None = None,
        notes: str | None = None,
    ) -> None:
        if len(matrix) == 0:
            self.write_text(title, 'Матрица не содержит строк.')
            return

        column_count = len(matrix[0])
        effective_row_names = list(row_names) if row_names is not None else [f'R{i + 1}' for i in range(len(matrix))]
        effective_column_names = list(column_names) if column_names is not None else [f'C{j + 1}' for j in range(column_count)]

        lines: List[str] = [f'## {title}', '']
        if notes:
            lines.extend([notes, ''])

        header = [''] + effective_column_names
        lines.append(self._markdown_row(header))
        lines.append(self._markdown_separator(len(header)))

        for row_index, row in enumerate(matrix):
            values = [effective_row_names[row_index]] + [self.format_number(value) for value in row]
            lines.append(self._markdown_row(values))

        lines.extend(['', ''])
        self._append_lines(lines)

    def write_table(self, title: str, headers: Sequence[str], rows: Sequence[Sequence[object]], notes: str | None = None) -> None:
        lines: List[str] = [f'## {title}', '']
        if notes:
            lines.extend([notes, ''])

        lines.append(self._markdown_row([str(value) for value in headers]))
        lines.append(self._markdown_separator(len(headers)))

        for row in rows:
            lines.append(self._markdown_row([self.format_object(value) for value in row]))

        lines.extend(['', ''])
        self._append_lines(lines)

    def _append_lines(self, lines: Iterable[str]) -> None:
        with self.file_path.open('a', encoding='utf-8') as file:
            file.write('\n'.join(lines))

    def _markdown_row(self, values: Sequence[str]) -> str:
        return '| ' + ' | '.join(values) + ' |'

    def _markdown_separator(self, size: int) -> str:
        return '| ' + ' | '.join(['---' for _ in range(size)]) + ' |'

    @staticmethod
    def format_object(value: object) -> str:
        if isinstance(value, Fraction):
            return SnapshotWriter.format_number(value)
        if isinstance(value, float):
            return f'{value:.6g}'
        if isinstance(value, list):
            return '[' + ', '.join(SnapshotWriter.format_object(item) for item in value) + ']'
        if isinstance(value, tuple):
            return '(' + ', '.join(SnapshotWriter.format_object(item) for item in value) + ')'
        return str(value)

    @staticmethod
    def format_number(value: Fraction) -> str:
        if value.denominator == 1:
            return str(value.numerator)
        return f'{value.numerator}/{value.denominator}'
