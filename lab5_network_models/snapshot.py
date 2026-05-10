from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

Number = Union[int, float]


class SnapshotWriter:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if self.file_path.parent != Path('.'):
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text('# Снимки работы алгоритмов сетевых моделей\n\n', encoding='utf-8')

    def write_section(self, title: str, lines: Optional[Iterable[str]] = None) -> None:
        output: List[str] = [f'## {title}', '']
        if lines is not None:
            output.extend(lines)
            output.append('')
        output.append('')
        self._append(output)

    def write_table(self, title: str, headers: Sequence[str], rows: Sequence[Sequence[object]], note: str = '') -> None:
        output: List[str] = [f'## {title}', '']
        if note:
            output.append(note)
            output.append('')
        output.append(self._row(headers))
        output.append(self._separator(len(headers)))
        for row in rows:
            output.append(self._row([self._format_value(value) for value in row]))
        output.append('')
        output.append('')
        self._append(output)

    def write_matrix(
        self,
        title: str,
        nodes: Sequence[str],
        values: Dict[Tuple[str, str], object],
        empty: str = '—',
        diagonal: str = '0',
        note: str = '',
    ) -> None:
        headers = [''] + list(nodes)
        rows: List[List[object]] = []
        for start in nodes:
            row: List[object] = [start]
            for end in nodes:
                if start == end:
                    row.append(diagonal)
                else:
                    row.append(values.get((start, end), empty))
            rows.append(row)
        self.write_table(title=title, headers=headers, rows=rows, note=note)

    def write_key_value_table(self, title: str, values: Dict[str, object], note: str = '') -> None:
        rows = [[key, self._format_value(value)] for key, value in values.items()]
        self.write_table(title=title, headers=['Параметр', 'Значение'], rows=rows, note=note)

    def _append(self, lines: Sequence[str]) -> None:
        with self.file_path.open('a', encoding='utf-8') as file:
            file.write('\n'.join(lines))

    def _row(self, values: Sequence[object]) -> str:
        return '| ' + ' | '.join(str(value) for value in values) + ' |'

    def _separator(self, size: int) -> str:
        return '| ' + ' | '.join('---' for _ in range(size)) + ' |'

    def _format_value(self, value: object) -> str:
        if isinstance(value, float):
            if value.is_integer():
                return str(int(value))
            return f'{value:.6g}'
        return str(value)
