# ЛР7. Параметрическое линейное программирование

Модуль анализирует линейные задачи с параметром в целевой функции или правых частях ограничений. Алгоритм перебирает базисы, строит матрицы базиса, вычисляет интервалы допустимости и оптимальности, затем сохраняет подробный Markdown-протокол.

## Возможности

- параметр в коэффициентах целевой функции `c(lambda) = c0 + c1 * lambda`;
- параметр в правых частях ограничений `b(lambda) = b0 + b1 * lambda`;
- ограничения `<=`, `>=`, `=`;
- корректное построение стандартной формы без лишних столбцов для ограничений `=`;
- перебор базисов;
- вычисление `B^(-1)`, `X_B(lambda)` и оценок небазисных переменных;
- определение интервалов параметра, на которых базис допустим и оптимален;
- точные вычисления через `fractions.Fraction`;
- Markdown-снимки матриц и итоговых интервалов.

## Структура

```text
lab7_parametric_linear_programming/
├── main.py
├── linear_problem.py
├── matrix_tools.py
├── parametric_simplex.py
├── problem_reader.py
├── snapshot.py
├── README.md
└── examples/
    ├── lab7_example.json
    ├── lab7_objective_parameter_example.json
    └── lab7_rhs_parameter_example.json
```

## Запуск

Из корня проекта:

```bash
python main.py -n 7 -i lab7_example.json -o results/lab7.md
```

Дополнительные примеры:

```bash
python main.py -n 7 -i lab7_objective_parameter_example.json -o results/lab7_objective_parameter.md
python main.py -n 7 -i lab7_rhs_parameter_example.json -o results/lab7_rhs_parameter.md
```

Из каталога модуля:

```bash
python main.py -i examples/lab7_example.json -s parametric_lp_snapshot.md
```

## Формат JSON

```json
{
  "parameter_name": "lambda",
  "parameter_interval": [null, null],
  "objective": {
    "type": "max",
    "base": [1, 2, -1, 0],
    "parameter": [0, 0, 0, 0]
  },
  "variable_names": ["x1", "x2", "x3", "x4"],
  "constraints": [
    {
      "coefficients": [1, 7, 9, 0],
      "sign": "=",
      "rhs_base": 8,
      "rhs_parameter": 5
    }
  ]
}
```

Поля `base` и `rhs_base` задают постоянную часть, поля `parameter` и `rhs_parameter` — коэффициент при параметре.

## Вариант 17

Модель варианта:

```text
L = x1 + 2x2 - x3 -> max

x1 + 7x2 + 9x3 = 8 + 5lambda
x1 + 3x2 + 5x3 = 4 + lambda
x1, x2, x3, x4 >= 0
```

Переменная `x4` оставлена во входном файле с нулевыми коэффициентами, потому что она указана в условии, но фактически не влияет на ограничения и целевую функцию.

Результат программы:

```text
Базис: x1, x2
Интервал: -1 <= lambda <= 1/2
x1 = 1 - 2lambda
x2 = 1 + lambda
x3 = 0
x4 = 0
Lmax = 3
```

Контрольная точка, которую выводит программа:

```text
lambda = -1/4
x1 = 3/2
x2 = 3/4
x3 = 0
x4 = 0
L = 3
```

## Статусы

| Статус | Смысл |
|---|---|
| `optimal_intervals` | найдены интервалы параметра, где базисы оптимальны |
| `no_optimal_interval` | допустимые/оптимальные интервалы не найдены |
| `infeasible` | задача несовместна на рассматриваемом интервале параметра |
