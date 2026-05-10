# Модуль 7: параметрическое линейное программирование

Консольная программа для анализа линейной задачи с параметром в целевой функции или правых частях ограничений. Алгоритм перебирает допустимые базисы, строит матрицы базиса, вычисляет интервалы допустимости и оптимальности, затем сохраняет подробный протокол в Markdown.

## Возможности

- параметр в коэффициентах целевой функции `c(lambda) = c0 + c1 * lambda`;
- параметр в правых частях ограничений `b(lambda) = b0 + b1 * lambda`;
- ограничения `<=`, `>=`, `=`;
- построение стандартной формы;
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
    ├── lab7_objective_parameter_example.json
    └── lab7_rhs_parameter_example.json
```

| Файл | Назначение |
|---|---|
| `main.py` | Запуск программы |
| `linear_problem.py` | Классы данных параметрической модели |
| `matrix_tools.py` | Матричные операции и обращение матриц |
| `parametric_simplex.py` | Анализ базисов и интервалов параметра |
| `problem_reader.py` | Чтение JSON |
| `snapshot.py` | Экспорт матриц и интервалов в Markdown |
| `examples/` | Примеры входных файлов |

## Запуск

Из каталога модуля:

```bash
python main.py -i examples/lab7_rhs_parameter_example.json -s parametric_lp_snapshot.md
```

Из корня проекта:

```bash
python main.py -n 7 -i lab7_rhs_parameter_example.json -o results/lab7_parametric_lp.md
```

## Формат JSON

```json
{
  "parameter_name": "lambda",
  "parameter_interval": [null, null],
  "objective": {
    "type": "max",
    "base": [1, 2, -1],
    "parameter": [0, 0, 0]
  },
  "variable_names": ["x1", "x2", "x3"],
  "constraints": [
    {
      "coefficients": [1, 7, 9],
      "sign": "=",
      "rhs": {"base": 8, "parameter": 5}
    }
  ]
}
```

Поля:

| Поле | Описание |
|---|---|
| `parameter_name` | имя параметра для вывода |
| `parameter_interval` | допустимый внешний интервал параметра; `null` означает бесконечную границу |
| `objective.type` | `max` или `min` |
| `objective.base` | базовые коэффициенты целевой функции |
| `objective.parameter` | коэффициенты при параметре в целевой функции |
| `constraints[].coefficients` | коэффициенты левой части |
| `constraints[].sign` | `<=`, `>=` или `=` |
| `constraints[].rhs.base` | базовая правая часть |
| `constraints[].rhs.parameter` | коэффициент при параметре в правой части |

Если параметр присутствует только в правых частях, в `objective.parameter` можно указать нули. Если параметр присутствует только в целевой функции, в `rhs.parameter` можно указать ноль.

## Результат

В консоль выводятся статус, число проанализированных базисов, найденные интервалы, контрольные значения параметра, значения переменных и целевой функции. Markdown-файл содержит стандартную форму, матрицы базисов, обратные матрицы, выражения базисного решения и итоговую таблицу интервалов.

## Возможные статусы

| Статус | Смысл |
|---|---|
| `optimal_intervals` | найдены интервалы оптимальности |
| `no_optimal_interval` | подходящие интервалы не найдены |
