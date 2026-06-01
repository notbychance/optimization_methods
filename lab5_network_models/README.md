# ЛР5. Сетевые модели

Модуль решает задачи на графах, проверяет предвыигрышные конфигурации поля и рассчитывает временные характеристики сетевого графика.

ЛР5 состоит из четырех заданий:

1. минимальное остовное дерево;
2. три сетевые подзадачи: кратчайший путь, максимальный поток, поток минимальной стоимости;
3. проверка предвыигрышной конфигурации крестиков-ноликов;
4. сетевое планирование методом критического пути.

Для полной сдачи нужно запустить все файлы из раздела «Запуск варианта 17».

## Поддерживаемые типы задач

| `problem_type` | Назначение | Алгоритм |
|---|---|---|
| `mst` | минимальное остовное дерево | Краскал |
| `shortest_path` | кратчайший путь | Дейкстра |
| `max_flow` | максимальный поток | Эдмондс-Карп |
| `min_cost_flow` | поток минимальной стоимости | последовательный выбор кратчайших увеличивающих путей по стоимости |
| `prewinning_tictactoe_configuration` | проверка предвыигрышной конфигурации поля | перебор пустых клеток и направлений |
| `project_scheduling` | сетевое планирование | метод критического пути |

## Структура

```text
lab5_network_models/
├── main.py
├── graph_models.py
├── network_algorithms.py
├── problem_reader.py
├── snapshot.py
├── README.md
├── test_snapshot.md
└── examples/
    ├── lab5_mst_example.json
    ├── lab5_shortest_path_example.json
    ├── lab5_max_flow_example.json
    ├── lab5_min_cost_flow_example.json
    ├── lab5_tictactoe_example.json
    ├── lab5_tictactoe_concrete_example.json
    ├── lab5_example.json
    └── lab5_project_scheduling_example.json
```

## Запуск варианта 17

Из корня проекта:

```bash
mkdir -p results/lab5

python main.py -n 5 -i lab5_mst_example.json -o results/lab5/lab5_task1_mst.md
python main.py -n 5 -i lab5_shortest_path_example.json -o results/lab5/lab5_task2_1_shortest_path.md
python main.py -n 5 -i lab5_max_flow_example.json -o results/lab5/lab5_task2_2_max_flow.md
python main.py -n 5 -i lab5_min_cost_flow_example.json -o results/lab5/lab5_task2_3_min_cost_flow.md
python main.py -n 5 -i lab5_tictactoe_example.json -o results/lab5/lab5_task3_tictactoe.md
python main.py -n 5 -i lab5_example.json -o results/lab5/lab5_task4_project_scheduling.md
```

Из каталога модуля:

```bash
python main.py -i examples/lab5_mst_example.json -s task1_mst.md
```

## Контрольные результаты текущих входных данных

| Задание | Файл | Результат |
|---|---|---|
| 1 | `lab5_mst_example.json` | минимальное остовное дерево, вес `33` |
| 2.1 | `lab5_shortest_path_example.json` | путь `1 -> 3 -> 5 -> 6 -> 7`, длина `8` |
| 2.2 | `lab5_max_flow_example.json` | максимальный поток `23` |
| 2.3 | `lab5_min_cost_flow_example.json` | минимальная стоимость `35` при требуемом потоке `5` |
| 3 | `lab5_tictactoe_example.json` | предвыигрышные ходы `X` в клетках `(2;2)` и `(2;7)` |
| 4 | `lab5_example.json` | критический путь `1 -> 4 -> 6 -> 7`, длительность `21`, стоимость `186` |

## Формат JSON: минимальное остовное дерево

```json
{
  "problem_type": "mst",
  "directed": false,
  "nodes": ["1", "2", "3"],
  "edges": [
    {"from": "1", "to": "2", "weight": 7},
    {"from": "1", "to": "3", "weight": 9}
  ]
}
```

В текущем файле задания 1 используются рукописные данные:

```text
1-2: 7, 1-3: 9, 1-6: 14, 2-3: 10, 2-4: 15,
3-4: 11, 3-6: 2, 4-5: 6, 5-6: 9
```

Выбранные программой ребра MST:

```text
3-6 = 2
4-5 = 6
1-2 = 7
1-3 = 9
5-6 = 9
Итого: 33
```

## Формат JSON: кратчайший путь

```json
{
  "problem_type": "shortest_path",
  "directed": true,
  "nodes": ["1", "2", "3", "4", "5", "6", "7"],
  "edges": [
    {"from": "1", "to": "2", "weight": 4}
  ],
  "source": "1",
  "target": "7"
}
```

Для текущих данных результат:

```text
1 -> 3 -> 5 -> 6 -> 7
длина = 8
```

## Формат JSON: максимальный поток

```json
{
  "problem_type": "max_flow",
  "directed": true,
  "nodes": ["1", "2", "3", "4", "5", "6"],
  "edges": [
    {"from": "1", "to": "2", "capacity": 16}
  ],
  "source": "1",
  "target": "6"
}
```

Для текущих данных максимальный поток равен:

```text
23
```

Ненулевые потоки:

```text
1 -> 2: 12
1 -> 3: 11
2 -> 4: 12
3 -> 5: 11
5 -> 4: 7
4 -> 6: 19
5 -> 6: 4
```

## Формат JSON: поток минимальной стоимости

```json
{
  "problem_type": "min_cost_flow",
  "directed": true,
  "nodes": ["1", "2", "3", "4", "5"],
  "edges": [
    {"from": "1", "to": "2", "capacity": 4, "cost": 2}
  ],
  "source": "1",
  "target": "5",
  "desired_flow": 5
}
```

Для текущих данных:

```text
требуемый поток = 5
минимальная стоимость = 35
```

## Формат JSON: проверка поля

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

Программа проверяет все пустые клетки для обоих игроков. Для текущего поля найдены два хода за `X`, которые сразу дают пять символов подряд по горизонтали:

```text
(2;2), (2;7)
```

## Формат JSON: сетевое планирование

```json
{
  "problem_type": "project_scheduling",
  "nodes": ["1", "2", "3", "4", "5", "6", "7"],
  "edges": [
    {"from": "1", "to": "2", "duration": 2, "cost": 11}
  ]
}
```

Для варианта 17 используется срочный режим работ, так как вариант нечетный.

Результат:

```text
критический путь: 1 -> 4 -> 6 -> 7
продолжительность комплекса: 21
стоимость комплекса: 186
```

Критические работы:

```text
(1;4), (4;6), (6;7)
```

## Статусы

| Статус | Смысл |
|---|---|
| `optimal` | решение найдено |
| `infeasible` | требуемый поток или путь невозможен |
| `unbounded` | для поддерживаемых задач обычно не используется |
| `prewinning` | найден ход, создающий выигрышную цепочку |
| `not_prewinning` | таких ходов нет |
| `input_required` | для проверки поля не задана конкретная матрица |
