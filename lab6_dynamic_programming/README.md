# Модуль 6: динамическое программирование

Консольная программа для решения детерминированных задач динамического программирования. Модуль поддерживает дискретную задачу о рюкзаке, универсальную конечную многоэтапную модель и аналитическую задачу с мультипликативным ограничением.

## Поддерживаемые типы задач

| `problem_type` | Назначение |
|---|---|
| `knapsack` | выбор количества предметов при ограниченной вместимости |
| `finite_horizon` | конечная многоэтапная задача с состояниями, решениями и переходами |
| `multiplicative_constraint_dynamic_programming` | задача с произведением переменных в ограничении |

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
    ├── lab6_knapsack_example.json
    ├── lab6_finite_horizon_example.json
    └── lab6_multiplicative_concrete_example.json
```

| Файл | Назначение |
|---|---|
| `main.py` | Запуск программы |
| `dp_models.py` | Классы данных задач и результатов |
| `dynamic_programming.py` | Алгоритмы динамического программирования и проверки моделей |
| `problem_reader.py` | Чтение JSON |
| `snapshot.py` | Экспорт таблиц Беллмана, переходов и рассуждений в Markdown |
| `examples/` | Примеры входных файлов |

## Запуск

Из каталога модуля:

```bash
python main.py -i examples/lab6_multiplicative_concrete_example.json -s dynamic_programming_snapshot.md
```

Из корня проекта:

```bash
python main.py -n 6 -i lab6_multiplicative_concrete_example.json -o results/lab6_dynamic_programming.md
```

## Формат JSON для `knapsack`

```json
{
  "problem_type": "knapsack",
  "capacity": 10,
  "items": [
    {"name": "A", "weight": 2, "value": 6, "max_count": 3},
    {"name": "B", "weight": 3, "value": 8, "max_count": 2}
  ]
}
```

Поля:

| Поле | Описание |
|---|---|
| `capacity` | вместимость |
| `items[].name` | имя предмета |
| `items[].weight` | вес единицы |
| `items[].value` | ценность единицы |
| `items[].max_count` | максимальное количество; необязательно |

## Формат JSON для `finite_horizon`

```json
{
  "problem_type": "finite_horizon",
  "optimization": "max",
  "initial_state": "S0",
  "terminal_values": {
    "S2": 0
  },
  "stages": [
    {
      "name": "1",
      "states": ["S0"],
      "transitions": [
        {"from": "S0", "decision": "a", "to": "S1", "value": 5}
      ]
    },
    {
      "name": "2",
      "states": ["S1"],
      "transitions": [
        {"from": "S1", "decision": "b", "to": "S2", "value": 3}
      ]
    }
  ]
}
```

Поля:

| Поле | Описание |
|---|---|
| `optimization` | `max` или `min` |
| `initial_state` | начальное состояние |
| `terminal_values` | значения конечных состояний |
| `stages` | список этапов |
| `transitions` | допустимые переходы этапа |

## Формат JSON для `multiplicative_constraint_dynamic_programming`

```json
{
  "problem_type": "multiplicative_constraint_dynamic_programming",
  "optimization": "max",
  "parameters": {
    "n": 3,
    "c": 10
  }
}
```

Модель имеет вид:

```text
z = y1^2 + y2^2 + ... + yn^2
y1 * y2 * ... * yn = c
yi >= 0
```

Если `n` или `c` заданы символически или отсутствуют, программа возвращает статус `input_required`. Для направления `max` при `n >= 2` и положительном `c` задача определяется как неограниченная сверху.

## Результат

В консоль выводятся статус, сообщение, значение целевой функции и найденные решения. Markdown-файл содержит таблицы динамического программирования, значения функций Беллмана, выбранные альтернативы или аналитическое обоснование статуса.

## Возможные статусы

| Статус | Смысл |
|---|---|
| `optimal` | найдено оптимальное решение |
| `input_required` | нужны конкретные значения параметров |
| `unbounded` | целевая функция не ограничена |
| `infeasible` | допустимых решений нет |
