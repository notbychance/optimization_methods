# Optimization Methods Toolkit

Набор независимых консольных Python-модулей для лабораторных работ по дисциплине «Методы оптимизации». Проект рассчитан на вариант 17 и одновременно позволяет подставлять свои входные данные через JSON-файлы.

Каждый модуль:

- читает входной JSON;
- выполняет расчет собственным алгоритмом без внешних оптимизационных библиотек;
- выводит краткий результат в консоль;
- сохраняет подробный Markdown-протокол с таблицами, матрицами, графами, ветвлениями или деревом решений.

## Структура проекта

```text
.
├── main.py
├── run_all_labs_commands.md
├── lab1_linear_programming/
├── lab2_simplex/
├── lab3_dual_simplex/
├── lab4_transportation/
├── lab5_network_models/
├── lab6_dynamic_programming/
├── lab7_parametric_linear_programming/
├── lab8_game_theory/
├── lab9_integer_linear_programming/
├── LICENSE
└── README.md
```

## Состав модулей

| № | Каталог | Лабораторная работа | Основной метод |
|---:|---|---|---|
| 1 | `lab1_linear_programming` | Решение задач линейного программирования | графический метод |
| 2 | `lab2_simplex` | Симплекс-метод | двухфазный симплекс-метод |
| 3 | `lab3_dual_simplex` | Двойственный симплекс-метод | двойственный симплекс + матричное представление |
| 4 | `lab4_transportation` | Транспортные задачи | метод потенциалов |
| 5 | `lab5_network_models` | Сетевые модели | MST, Дейкстра, максимальный поток, поток минимальной стоимости, CPM, проверка поля |
| 6 | `lab6_dynamic_programming` | Детерминированные модели динамического программирования | рекурсии Беллмана и аналитическая проверка варианта 17 |
| 7 | `lab7_parametric_linear_programming` | Параметрическое линейное программирование | перебор базисов и интервалы параметра |
| 8 | `lab8_game_theory` | Теория игр и принятие решений | матричные игры, критерии решений, биматричные игры, дерево решений |
| 9 | `lab9_integer_linear_programming` | Целочисленное линейное программирование | ветви и границы + симплекс-релаксации |

## Требования

Нужен Python 3.10 или новее.

```bash
python --version
```

Сторонние зависимости для расчетов не требуются.

## Общий запуск из корня проекта

```bash
python main.py --number НОМЕР --input ВХОДНОЙ_ФАЙЛ.json --output РЕЗУЛЬТАТ.md
```

Короткая форма:

```bash
python main.py -n НОМЕР -i ВХОДНОЙ_ФАЙЛ.json -o РЕЗУЛЬТАТ.md
```

Параметры:

| Параметр | Коротко | Назначение |
|---|---|---|
| `--number` | `-n` | номер лабораторной от 1 до 9 |
| `--input` | `-i` | путь к JSON-файлу или имя файла из папки `examples` нужного модуля |
| `--output`, `--snapshot`, `--export` | `-o`, `-s` | путь к Markdown-файлу результата |

Если указан относительный путь входного файла, запускатор ищет его:

1. относительно корня проекта;
2. относительно каталога выбранного модуля;
3. по имени файла в `examples` выбранного модуля.

## Быстрый запуск варианта 17

```bash
mkdir -p results/lab5

python main.py -n 1 -i lab1_example.json -o results/lab1.md
python main.py -n 2 -i lab2_example.json -o results/lab2.md
python main.py -n 3 -i lab3_example.json -o results/lab3.md
python main.py -n 4 -i lab4_example.json -o results/lab4.md
python main.py -n 5 -i lab5_mst_example.json -o results/lab5/lab5_task1_mst.md
python main.py -n 5 -i lab5_shortest_path_example.json -o results/lab5/lab5_task2_1_shortest_path.md
python main.py -n 5 -i lab5_max_flow_example.json -o results/lab5/lab5_task2_2_max_flow.md
python main.py -n 5 -i lab5_min_cost_flow_example.json -o results/lab5/lab5_task2_3_min_cost_flow.md
python main.py -n 5 -i lab5_tictactoe_example.json -o results/lab5/lab5_task3_tictactoe.md
python main.py -n 5 -i lab5_example.json -o results/lab5/lab5_task4_project_scheduling.md
python main.py -n 6 -i lab6_example.json -o results/lab6.md
python main.py -n 7 -i lab7_example.json -o results/lab7.md
python main.py -n 8 -i lab8_example.json -o results/lab8.md
python main.py -n 9 -i lab9_example.json -o results/lab9.md
```

Подробные команды, включая дополнительные демонстрационные файлы, приведены в `run_all_labs_commands.md`.

## Контрольные результаты варианта 17

| ЛР | Основной входной файл | Ожидаемый итог |
|---:|---|---|
| 1 | `lab1_example.json` | `x1 = 150`, `y = 100`, `x2 = 200`, `F = 24750` |
| 2 | `lab2_example.json` | `infeasible`; исходные данные варианта несовместны при ограничении `7000` четырехкомнатных квартир и бюджете 40 млн |
| 3 | `lab3_example.json` | `unbounded`; целевая функция не ограничена сверху |
| 4 | `lab4_example.json` | оптимальная стоимость перевозок `7100` |
| 5.1 | `lab5_mst_example.json` | минимальное остовное дерево, вес `33` |
| 5.2.1 | `lab5_shortest_path_example.json` | кратчайший путь `1 -> 3 -> 5 -> 6 -> 7`, длина `8` |
| 5.2.2 | `lab5_max_flow_example.json` | максимальный поток `23` |
| 5.2.3 | `lab5_min_cost_flow_example.json` | поток минимальной стоимости `35` при требуемом потоке `5` |
| 5.3 | `lab5_tictactoe_example.json` | предвыигрышные ходы `X`: `(2;2)` и `(2;7)` |
| 5.4 | `lab5_example.json` | критический путь `1 -> 4 -> 6 -> 7`, длительность `21`, стоимость `186` |
| 6 | `lab6_example.json` | `symbolic_solution`: при `n >= 2`, `c >= 0` максимум не ограничен сверху |
| 7 | `lab7_example.json` | оптимальный базис `x1, x2`, интервал `-1 <= lambda <= 1/2`, `Lmax = 3` |
| 8 | `lab8_example.json` | профилактический цикл по выбранной модели расчета; для бумажной модели нужен флаг `use_simplified_calculation: true` |
| 9 | `lab9_example.json` | `A = 40`, `B = 31`, `C = 3`, `Fmax = 3751` |

## Особые замечания по вариантам

### ЛР2

Файл `lab2_example.json` буквально отражает условие варианта 17. При таких данных система ограничений несовместна: требование по четырехкомнатным квартирам слишком велико относительно бюджета. Программа корректно завершает фазу I статусом `infeasible`.

### ЛР5

Лабораторная работа состоит из четырех заданий, причем второе задание делится на три подзадачи. Поэтому для полного протокола ЛР5 нужно запускать не один, а шесть JSON-файлов:

- `lab5_mst_example.json` — задание 1;
- `lab5_shortest_path_example.json` — задание 2.1;
- `lab5_max_flow_example.json` — задание 2.2;
- `lab5_min_cost_flow_example.json` — задание 2.3;
- `lab5_tictactoe_example.json` — задание 3;
- `lab5_example.json` — задание 4.

### ЛР8

Для задачи профилактического обслуживания реализованы две модели:

- `simplified_fixed_cycle` — учебная модель фиксированного профилактического цикла, совпадающая с бумажным расчетом: `T = 8`, стоимость парка `397.5` долл./мес.;
- `renewal` — расширенная модель, где случайная поломка завершает текущий цикл; она дает `T = 10` и стоимость парка около `324.454208` долл./мес.

Если нужен бумажный ответ, добавьте во входной JSON:

```json
"use_simplified_calculation": true,
"max_cycle_months": 12
```

## Локальный запуск модулей

Каждый модуль можно запускать напрямую из его каталога:

```bash
cd lab2_simplex
python main.py -i examples/lab2_example.json -s simplex_snapshot.md
```

При локальном запуске параметр результата обычно называется `--snapshot` или `-s`.

## Файлы результата

Markdown-отчеты не хранятся как исходные данные. Их можно в любой момент перегенерировать командами из `run_all_labs_commands.md`.

Обычно отчет содержит:

- исходные данные;
- промежуточные таблицы, матрицы, графы или дерево решений;
- выбранные переходы, базисы, циклы, пути или ветви;
- итоговый статус;
- найденное решение или математическую причину отсутствия оптимума.
