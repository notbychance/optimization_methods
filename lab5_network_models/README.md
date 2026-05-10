# Модуль 5: сетевые модели и проверка конфигурации поля

Консольная программа для решения задач на графах и проверки предвыигрышной конфигурации клеточного поля. Все алгоритмы реализованы вручную без специализированных библиотек.

## Поддерживаемые типы задач

| `problem_type` | Назначение | Алгоритм |
|---|---|---|
| `mst` | минимальное остовное дерево | алгоритм Краскала |
| `shortest_path` | кратчайший путь от источника к цели | алгоритм Дейкстры |
| `max_flow` | максимальный поток | алгоритм Эдмондса-Карпа |
| `min_cost_flow` | поток минимальной стоимости | последовательный поиск кратчайших увеличивающих путей по стоимости |
| `prewinning_tictactoe_configuration` | проверка, можно ли одним ходом получить цепочку заданной длины | перебор пустых клеток и проверка направлений |

## Структура

```text
lab5_network_models/
├── main.py
├── graph_models.py
├── network_algorithms.py
├── problem_reader.py
├── snapshot.py
├── README.md
└── examples/
    ├── lab5_mst_example.json
    ├── lab5_shortest_path_example.json
    ├── lab5_max_flow_example.json
    ├── lab5_min_cost_flow_example.json
    └── lab5_tictactoe_concrete_example.json
```

| Файл | Назначение |
|---|---|
| `main.py` | Запуск программы и вывод результата |
| `graph_models.py` | Классы данных графов, рёбер и результатов |
| `network_algorithms.py` | Алгоритмы графов, потоков и проверки поля |
| `problem_reader.py` | Чтение JSON и валидация входных данных |
| `snapshot.py` | Экспорт шагов алгоритма в Markdown |
| `examples/` | Примеры входных файлов |

## Запуск

Из каталога модуля:

```bash
python main.py -i examples/lab5_tictactoe_concrete_example.json -s network_snapshot.md
```

Из корня проекта:

```bash
python main.py -n 5 -i lab5_tictactoe_concrete_example.json -o results/lab5_network_models.md
```

## Общий формат графовой задачи

```json
{
  "problem_type": "shortest_path",
  "directed": true,
  "nodes": ["A", "B", "C"],
  "edges": [
    {"from": "A", "to": "B", "weight": 4},
    {"from": "B", "to": "C", "weight": 2},
    {"from": "A", "to": "C", "weight": 10}
  ],
  "source": "A",
  "target": "C"
}
```

Поля:

| Поле | Описание |
|---|---|
| `problem_type` | тип задачи |
| `directed` | ориентированный граф; для `mst` обычно `false` |
| `nodes` | список вершин; если не задан, собирается из рёбер |
| `edges` | список рёбер или дуг |
| `from`, `to` | начальная и конечная вершина ребра |
| `weight` | вес ребра для MST и кратчайшего пути |
| `capacity` | пропускная способность для потоковых задач |
| `cost` | стоимость единицы потока для `min_cost_flow` |
| `source` | источник для путей и потоков |
| `target` | сток или целевая вершина |
| `desired_flow` | требуемый объём потока для `min_cost_flow`; необязательно |

## Пример для минимального остовного дерева

```json
{
  "problem_type": "mst",
  "directed": false,
  "nodes": ["A", "B", "C"],
  "edges": [
    {"from": "A", "to": "B", "weight": 3},
    {"from": "B", "to": "C", "weight": 2},
    {"from": "A", "to": "C", "weight": 5}
  ]
}
```

## Пример для максимального потока

```json
{
  "problem_type": "max_flow",
  "directed": true,
  "nodes": ["S", "A", "T"],
  "edges": [
    {"from": "S", "to": "A", "capacity": 5},
    {"from": "A", "to": "T", "capacity": 4}
  ],
  "source": "S",
  "target": "T"
}
```

## Формат задачи проверки поля

```json
{
  "problem_type": "prewinning_tictactoe_configuration",
  "win_length": 5,
  "symbols": {
    "first_player": "X",
    "second_player": "O",
    "empty_cell": "."
  },
  "board": [
    ".......",
    "..XXXX.",
    "...O...",
    "...O...",
    "...O...",
    "......."
  ]
}
```

Для поля поддерживаются три формы:

```json
"board": ["..X", ".O.", "..."]
```

```json
"board": [[".", ".", "X"], [".", "O", "."], [".", ".", "."]]
```

```json
"board": "..X\n.O.\n..."
```

Если `board` передан текстовым описанием, а не конкретной матрицей, программа завершится статусом `input_required`.

## Результат

В консоль выводятся тип задачи, статус, сообщение и итоговые данные: путь, выбранные рёбра, поток или список найденных ходов. Markdown-файл содержит исходные данные, промежуточные шаги и итог.

## Возможные статусы

| Статус | Смысл |
|---|---|
| `optimal` | задача решена |
| `no_path` | путь между заданными вершинами не найден |
| `infeasible` | требуемый поток построить невозможно |
| `input_required` | для проверки поля не задана конкретная матрица |
| `prewinning` | найден хотя бы один выигрышный ход |
| `not_prewinning` | выигрышные ходы не найдены |
