# ЛР3. Двойственный симплекс-метод

Модуль решает задачи линейного программирования двойственным симплекс-методом и выводит матричное представление текущего базиса.

## Возможности

- ввод задачи как полной модели (`mode = model`);
- ввод готовой симплекс-таблицы (`mode = tableau`);
- двойственный симплекс-метод с пересчетом таблицы методом Гаусса-Жордана;
- проверка двойственной допустимости стартовой таблицы;
- дополнительная диагностика обычным двухфазным симплекс-методом, если стартовая таблица не является двойственно допустимой;
- вывод матриц `B`, `B^(-1)`, `B^(-1)A`, базисного решения `X_B` и оценок;
- точные вычисления через `fractions.Fraction`;
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
    ├── lab3_example.json
    ├── lab3_dual_example.json
    └── lab3_tableau_example.json
```

## Запуск

Из корня проекта:

```bash
python main.py -n 3 -i lab3_example.json -o results/lab3.md
```

Запуск готовой таблицы:

```bash
python main.py -n 3 -i lab3_tableau_example.json -o results/lab3_tableau.md
```

Из каталога модуля:

```bash
python main.py -i examples/lab3_example.json -s dual_simplex_snapshot.md
```

## Формат JSON: модель

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

## Формат JSON: готовая таблица

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

## Вариант 17

Для варианта 17 стартовая таблица, построенная напрямую из модели, не является двойственно допустимой. Программа фиксирует это и запускает дополнительную двухфазную диагностику.

Итоговый математический статус:

```text
Статус: unbounded
Целевая функция не ограничена сверху на множестве допустимых решений.
```

Такой вывод согласуется с допустимым направлением роста, поэтому отсутствие конечного оптимума является результатом задачи, а не ошибкой программы.
