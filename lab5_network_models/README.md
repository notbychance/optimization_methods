# Лабораторная работа №5 — сетевые модели

Программа решает типовые задачи сетевых моделей без использования специализированных библиотек оптимизации.

Реализованы четыре режима:

1. `mst` — построение минимального остовного дерева алгоритмом Краскала;
2. `shortest_path` — нахождение кратчайшего пути алгоритмом Дейкстры;
3. `max_flow` — нахождение максимального потока алгоритмом Эдмондса-Карпа;
4. `min_cost_flow` — нахождение потока наименьшей стоимости методом последовательного выбора кратчайшего по стоимости увеличивающего пути в остаточной сети.

Программа соответствует структуре лабораторной работы: выполняет математическую обработку сетевой модели, решает задачу алгоритмом общего вида, читает исходные данные из файла и сохраняет пошаговые снимки вычислений.

## Структура проекта

```text
lab5_network_models_python/
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
    └── lab5_min_cost_flow_example.json
```

## Назначение файлов

| Файл | Назначение |
|---|---|
| `main.py` | модуль запуска программы |
| `graph_models.py` | модели данных: ребро, задача, результат |
| `network_algorithms.py` | собственные реализации алгоритмов сетевых моделей |
| `problem_reader.py` | чтение условия из JSON-файла |
| `snapshot.py` | запись поэтапных снимков алгоритма в Markdown-файл |
| `examples/` | примеры входных данных |

## Требования

Нужен только Python 3.10 или новее.

Сторонние библиотеки не требуются.

## Запуск

Общий вид команды:

```bash
python main.py --input путь_к_json --snapshot путь_к_файлу_снимков.md
```

Примеры:

```bash
python main.py --input examples/lab5_mst_example.json --snapshot mst_snapshot.md
python main.py --input examples/lab5_shortest_path_example.json --snapshot shortest_path_snapshot.md
python main.py --input examples/lab5_max_flow_example.json --snapshot max_flow_snapshot.md
python main.py --input examples/lab5_min_cost_flow_example.json --snapshot min_cost_flow_snapshot.md
```

## Формат входного файла

Входной файл имеет формат JSON.

Общие поля:

| Поле | Обязательность | Описание |
|---|---:|---|
| `problem_type` | да | тип задачи: `mst`, `shortest_path`, `max_flow`, `min_cost_flow` |
| `nodes` | да | список вершин сети |
| `edges` | да | список ребер или дуг |
| `directed` | нет | признак ориентированного графа |
| `source` | для 3 режимов | исходная вершина для `shortest_path`, `max_flow`, `min_cost_flow` |
| `target` | для 3 режимов | конечная вершина для `shortest_path`, `max_flow`, `min_cost_flow` |
| `desired_flow` | нет | требуемая величина потока для `min_cost_flow` |

Поля ребра/дуги:

| Поле | Описание |
|---|---|
| `from` | начальная вершина |
| `to` | конечная вершина |
| `weight` | вес ребра или длина дуги |
| `capacity` | пропускная способность дуги |
| `cost` | стоимость передачи единицы потока по дуге |

## Пример для минимального остовного дерева

```json
{
  "problem_type": "mst",
  "directed": false,
  "nodes": ["A", "B", "C", "D", "E"],
  "edges": [
    {"from": "A", "to": "B", "weight": 4},
    {"from": "A", "to": "C", "weight": 2},
    {"from": "B", "to": "C", "weight": 1},
    {"from": "B", "to": "D", "weight": 5},
    {"from": "C", "to": "D", "weight": 8},
    {"from": "C", "to": "E", "weight": 10},
    {"from": "D", "to": "E", "weight": 2}
  ]
}
```

## Пример для кратчайшего пути

```json
{
  "problem_type": "shortest_path",
  "directed": true,
  "source": "S",
  "target": "T",
  "nodes": ["S", "A", "B", "C", "T"],
  "edges": [
    {"from": "S", "to": "A", "weight": 4},
    {"from": "S", "to": "B", "weight": 2},
    {"from": "B", "to": "A", "weight": 1},
    {"from": "A", "to": "C", "weight": 5},
    {"from": "B", "to": "C", "weight": 8},
    {"from": "C", "to": "T", "weight": 3},
    {"from": "A", "to": "T", "weight": 10}
  ]
}
```

## Пример для максимального потока

```json
{
  "problem_type": "max_flow",
  "directed": true,
  "source": "S",
  "target": "T",
  "nodes": ["S", "A", "B", "C", "T"],
  "edges": [
    {"from": "S", "to": "A", "capacity": 10},
    {"from": "S", "to": "B", "capacity": 8},
    {"from": "A", "to": "B", "capacity": 5},
    {"from": "A", "to": "C", "capacity": 5},
    {"from": "B", "to": "C", "capacity": 10},
    {"from": "C", "to": "T", "capacity": 10},
    {"from": "B", "to": "T", "capacity": 5}
  ]
}
```

## Пример для потока наименьшей стоимости

```json
{
  "problem_type": "min_cost_flow",
  "directed": true,
  "source": "S",
  "target": "T",
  "desired_flow": 7,
  "nodes": ["S", "A", "B", "T"],
  "edges": [
    {"from": "S", "to": "A", "capacity": 4, "cost": 2},
    {"from": "S", "to": "B", "capacity": 5, "cost": 4},
    {"from": "A", "to": "B", "capacity": 2, "cost": 1},
    {"from": "A", "to": "T", "capacity": 3, "cost": 3},
    {"from": "B", "to": "T", "capacity": 6, "cost": 1}
  ]
}
```

## Файл снимков алгоритма

Файл снимков создается в формате Markdown.

В него записываются:

- исходные матрицы весов, пропускных способностей или стоимостей;
- таблицы выбора ребер для алгоритма Краскала;
- таблицы меток и релаксаций для алгоритма Дейкстры;
- матрицы текущего потока и остаточной сети для задач потока;
- итоговые таблицы с найденным решением.

Пример запуска с выводом снимков:

```bash
python main.py --input examples/lab5_max_flow_example.json --snapshot max_flow_snapshot.md
```

После запуска файл `max_flow_snapshot.md` можно вставить в отчет как поэтапное описание работы алгоритма.

## Статусы результата

| Статус | Значение |
|---|---|
| `optimal` | решение найдено |
| `disconnected` | минимальное остовное дерево не построено, граф несвязный |
| `unreachable` | путь между заданными вершинами не найден |
| `infeasible` | требуемый поток невозможно передать через сеть |

## Что включить в отчет

В отчет по лабораторной работе удобно включить:

1. постановку задачи;
2. исходную сетевую модель;
3. математическое описание выбранного алгоритма;
4. входной JSON-файл;
5. фрагменты файла снимков с итерациями;
6. итоговое решение;
7. листинг программы.
