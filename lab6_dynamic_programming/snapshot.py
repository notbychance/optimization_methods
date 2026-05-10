from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Union

Number = Union[int, float]


class SnapshotWriter:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if self.file_path.parent != Path('.'):
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text('# Снимки алгоритма динамического программирования\n\n', encoding='utf-8')

    def write_text(self, title: str, lines: Iterable[str]) -> None:
        content: List[str] = [f'## {title}', '']
        content.extend(lines)
        content.append('')
        content.append('')
        with self.file_path.open('a', encoding='utf-8') as file:
            file.write('\n'.join(content))

    def write_table(self, title: str, headers: Sequence[str], rows: Sequence[Sequence[object]], notes: str = '') -> None:
        content: List[str] = [f'## {title}', '']
        if notes:
            content.append(notes)
            content.append('')
        content.append(self._markdown_row([str(header) for header in headers]))
        content.append(self._markdown_separator(len(headers)))
        for row in rows:
            content.append(self._markdown_row([self._format_cell(value) for value in row]))
        content.append('')
        content.append('')
        with self.file_path.open('a', encoding='utf-8') as file:
            file.write('\n'.join(content))

    def write_knapsack_stage(
        self,
        stage_index: int,
        item_name: str,
        capacities: Sequence[int],
        objective_values: Dict[int, Number],
        decisions: Dict[int, int],
        alternatives: Dict[int, str],
        optimization: str,
    ) -> None:
        headers = ['Вместимость W'] + [str(capacity) for capacity in capacities]
        value_row = [f'F{stage_index}(W)'] + [self._format_number(objective_values[capacity]) for capacity in capacities]
        decision_row = [f'm{stage_index} ({item_name})'] + [str(decisions[capacity]) for capacity in capacities]
        alternatives_row = ['Проверенные варианты'] + [alternatives[capacity] for capacity in capacities]
        self.write_table(
            title=f'Этап {stage_index}. Предмет {item_name}',
            headers=headers,
            rows=[value_row, decision_row, alternatives_row],
            notes=f'На этапе выбирается количество предметов данного наименования. Критерий оптимизации: {optimization}.',
        )

    def write_finite_stage(
        self,
        stage_name: str,
        rows: Sequence[Sequence[object]],
        optimization: str,
    ) -> None:
        self.write_table(
            title=f'Этап {stage_name}',
            headers=['Состояние', 'Альтернативы', 'Оптимальное значение', 'Оптимальное решение'],
            rows=rows,
            notes=f'Для каждого состояния вычисляется оптимальное значение функции Беллмана. Критерий оптимизации: {optimization}.',
        )

    def write_terminal_values(self, terminal_values: Dict[str, Number]) -> None:
        rows = [[state, self._format_number(value)] for state, value in sorted(terminal_values.items())]
        self.write_table(
            title='Граничные значения последнего этапа',
            headers=['Состояние', 'Значение'],
            rows=rows,
            notes='Эти значения используются как база обратной прогонки.',
        )

    def _markdown_row(self, values: Sequence[str]) -> str:
        return '| ' + ' | '.join(values) + ' |'

    def _markdown_separator(self, size: int) -> str:
        return '| ' + ' | '.join(['---' for _ in range(size)]) + ' |'

    def _format_cell(self, value: object) -> str:
        if isinstance(value, float) or isinstance(value, int):
            return self._format_number(value)
        return str(value)

    def _format_number(self, value: Number) -> str:
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)
