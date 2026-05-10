# Модуль 3: двойственный симплекс-метод

Консольная программа для решения задач линейного программирования двойственным симплекс-методом. Модуль поддерживает ввод полной математической модели или готовой симплекс-таблицы и сохраняет пошаговый протокол с матричным представлением текущего базиса.

## Возможности

- ввод задачи как модели (`mode = model`);
- ввод готовой таблицы (`mode = tableau`);
- двойственный симплекс-метод с пересчётом таблицы методом Гаусса-Жордана;
- проверка двойственной допустимости;
- вывод матриц `B`, `B^(-1)`, `B^(-1)A`, базисного решения `X_B` и оценок;
- точные вычисления через `fractions.Fraction`;
- Markdown-снимки каждой итерации;
- статусы `optimal`, `not_dual_feasible`, `infeasible`, `unbounded`.

## Структура

```text
lab3_dual_simplex/
├── main.py
├── dual_simplex.py
├── linear_problem.py
├── matrix_tools.py
├── problem_reader.py
├── snapshot.py
├── README.md
└── examples/
    ├── lab3_dual_example.json
    └── lab3_tableau_example.json
```

| Файл | Назначение |
|---|---|
| `main.py` | Точка входа |
| `problem_reader.py` | Чтение режима `model` или `tableau` из JSON |
| `dual_simplex.py` | Алгоритм двойственного симплекс-метода |
| `matrix_tools.py` | Матричные операции и обращение матрицы |
| `linear_problem.py` | Классы данных задачи и результата |
| `snapshot.py` | Экспорт таблиц и матриц в Markdown |

## Запуск

Из каталога модуля:

```bash
python main.py -i examples/lab3_dual_example.json -s dual_simplex_snapshot.md
```

Запуск с готовой таблицей:

```bash
python main.py -i examples/lab3_tableau_example.json -s dual_tableau_snapshot.md
```

Из корня проекта:

```bash
python main.py -n 3 -i lab3_dual_example.json -o results/lab3_dual_simplex.md
```

## Формат JSON: режим `model`

```json
{
  "mode": "model",
  "objective": {
    "type": "max",
    "coefficients": [1, -4, 6, 3]
  },
  "variable_names": ["x1", "x2", "x3", "x4"],
  "constraints": [
    {
      "coefficients": [3, 2, 1, 1],
      "sign": ">=",
      "rhs": 6
    }
  ]
}
```

## Формат JSON: режим `tableau`

```json
{
  "mode": "tableau",
  "objective_type": "max",
  "column_names": ["x1", "x2", "s1"],
  "basis": ["s1"],
  "rows": [[-3, -2, 1, -6]],
  "objective_row": [-1, 4, 0, 0],
  "max_costs": [1, -4, 0],
  "original_objective": [1, -4],
  "original_variable_count": 2
}
```

В строках таблицы последний элемент является свободным членом.

## Результат

В консоль выводятся статус, сообщение, число итераций, значение целевой функции и значения исходных переменных. Markdown-файл содержит исходную таблицу, выбранные ведущие элементы, пересчитанные таблицы и матричное представление базиса на каждом шаге.
