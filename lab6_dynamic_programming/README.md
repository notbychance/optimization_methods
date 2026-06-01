# ЛР6. Детерминированные модели динамического программирования

Модуль реализует несколько типов задач динамического программирования и аналитическую проверку варианта 17.

## Поддерживаемые типы задач

| `problem_type` | Назначение |
|---|---|
| `knapsack` | дискретная задача загрузки / рюкзака |
| `finite_horizon` | конечная многоэтапная задача Беллмана |
| `multiplicative_constraint_dynamic_programming` | вариант 17: сумма квадратов при произведении переменных |

## Структура

```text
lab6_dynamic_programming/
├── main.py
├── dp_models.py
├── dynamic_programming.py
├── problem_reader.py
├── snapshot.py
├── README.md
└── examples/
    ├── lab6_example.json
    ├── lab6_multiplicative_concrete_example.json
    ├── lab6_knapsack_example.json
    └── lab6_finite_horizon_example.json
```

## Запуск

Из корня проекта:

```bash
python main.py -n 6 -i lab6_example.json -o results/lab6.md
```

Дополнительные примеры:

```bash
python main.py -n 6 -i lab6_multiplicative_concrete_example.json -o results/lab6_multiplicative_concrete.md
python main.py -n 6 -i lab6_knapsack_example.json -o results/lab6_knapsack.md
python main.py -n 6 -i lab6_finite_horizon_example.json -o results/lab6_finite_horizon.md
```

Из каталога модуля:

```bash
python main.py -i examples/lab6_example.json -s dynamic_programming_snapshot.md
```

## Формат JSON для `knapsack`

```json
{
  "problem_type": "knapsack",
  "capacity": 10,
  "items": [
    {"name": "A", "weight": 2, "value": 6, "max_count": 3},
    {"name": "B", "weight": 3, "value": 9, "max_count": 2}
  ]
}
```

Пример `lab6_knapsack_example.json` дает:

```text
A = 2, B = 2, C = 0
F = 30
W = 10
```

## Формат JSON для `finite_horizon`

```json
{
  "problem_type": "finite_horizon",
  "objective": "min",
  "stages": [
    {
      "name": "Этап 1",
      "transitions": [
        {"state": "S0", "next_state": "S1", "cost": 4},
        {"state": "S0", "next_state": "S2", "cost": 3}
      ]
    }
  ],
  "start_state": "S0"
}
```

Пример `lab6_finite_horizon_example.json` дает стратегию:

```text
S0 -> S2 -> T2
стоимость = 5
```

## Вариант 17

Исходная задача:

```text
z = y1^2 + y2^2 + ... + yn^2 -> max

y1 * y2 * ... * yn = c

yi >= 0
```

Файл `lab6_example.json` задает эту модель символически. Программа не подставляет произвольные значения `n` и `c`, а формирует общий вывод.

Итоговый статус:

```text
symbolic_solution
```

Общее решение:

1. если `n = 1` и `c >= 0`, то `y1 = c`, `z = c^2`;
2. если `n >= 2` и `c >= 0`, задача максимизации не ограничена сверху;
3. если `c < 0`, допустимых решений нет, так как все `yi >= 0`.

Доказательство неограниченности для `n >= 2`, `c > 0`:

```text
y1 = t
y2 = c / t
y3 = ... = yn = 1
```

Тогда произведение равно `c`, а

```text
z(t) = t^2 + c^2/t^2 + (n - 2) -> infinity при t -> infinity.
```

Для `c = 0` можно взять `y1 = t`, `y2 = 0`, и сумма квадратов также не ограничена сверху.

## Числовой демонстрационный пример

Файл `lab6_multiplicative_concrete_example.json` задает, например, `n = 3`, `c = 10` и возвращает статус:

```text
unbounded
```

Он нужен только для демонстрации, так как в методичке параметры `n` и `c` заданы в общем виде.

## Статусы

| Статус | Смысл |
|---|---|
| `optimal` | найдено оптимальное решение дискретной задачи |
| `unbounded` | целевая функция не ограничена сверху |
| `infeasible` | допустимых решений нет |
| `symbolic_solution` | получено аналитическое решение при символических параметрах |
| `input_required` | нужны конкретные данные для режима, который не допускает символическую обработку |
