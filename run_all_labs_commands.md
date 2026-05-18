# Команды запуска модулей

Файл содержит готовые команды для запуска всех модулей из корня проекта. Файлы варианта 17 названы по правилу `lab{номер}_example.json`. Дополнительные демонстрационные файлы названы по правилу `lab{номер}_{тип}_example.json`.

## Подготовка папки результатов

Bash / Git Bash / macOS / Linux:

```bash
mkdir -p results
```

PowerShell:

```powershell
New-Item -ItemType Directory -Force results
```

## Полный запуск по варианту 17

```bash
python main.py -n 1 -i lab1_example.json -o results/lab1.md
python main.py -n 2 -i lab2_example.json -o results/lab2.md
python main.py -n 3 -i lab3_example.json -o results/lab3.md
python main.py -n 4 -i lab4_example.json -o results/lab4.md
python main.py -n 5 -i lab5_example.json -o results/lab5.md
python main.py -n 6 -i lab6_example.json -o results/lab6.md
python main.py -n 7 -i lab7_example.json -o results/lab7.md
python main.py -n 8 -i lab8_example.json -o results/lab8.md
python main.py -n 9 -i lab9_example.json -o results/lab9.md
```

## Модуль 1: графический метод линейного программирования

```bash
python main.py -n 1 -i lab1_example.json -o results/lab1.md
```

После запуска создаются Markdown-отчет и PNG-график области допустимых решений.

## Модуль 2: двухфазный симплекс-метод

```bash
python main.py -n 2 -i lab2_example.json -o results/lab2.md
```

## Модуль 3: двойственный симплекс-метод

Ввод математической модели варианта 17:

```bash
python main.py -n 3 -i lab3_example.json -o results/lab3.md
```

Ввод готовой таблицы:

```bash
python main.py -n 3 -i lab3_tableau_example.json -o results/lab3_tableau.md
```

## Модуль 4: транспортная задача

```bash
python main.py -n 4 -i lab4_example.json -o results/lab4.md
python main.py -n 4 -i lab4_unbalanced_example.json -o results/lab4_unbalanced.md
```

## Модуль 5: сетевые модели и проверка поля

Вариант 17, сетевое планирование:

```bash
python main.py -n 5 -i lab5_example.json -o results/lab5.md
```

Дополнительные файлы примеров:

```bash
python main.py -n 5 -i lab5_tictactoe_example.json -o results/lab5_tictactoe.md
python main.py -n 5 -i lab5_shortest_path_example.json -o results/lab5_shortest_path.md
python main.py -n 5 -i lab5_mst_example.json -o results/lab5_mst.md
python main.py -n 5 -i lab5_max_flow_example.json -o results/lab5_max_flow.md
python main.py -n 5 -i lab5_min_cost_flow_example.json -o results/lab5_min_cost_flow.md
```

## Модуль 6: динамическое программирование

Вариант 17, символическое условие:

```bash
python main.py -n 6 -i lab6_example.json -o results/lab6.md
```

Дополнительные файлы примеров:

```bash
python main.py -n 6 -i lab6_multiplicative_concrete_example.json -o results/lab6_multiplicative_concrete.md
python main.py -n 6 -i lab6_knapsack_example.json -o results/lab6_knapsack.md
python main.py -n 6 -i lab6_finite_horizon_example.json -o results/lab6_finite_horizon.md
```

Если параметры модели заданы символически, модуль завершится штатным статусом `input_required`.

## Модуль 7: параметрическое линейное программирование

```bash
python main.py -n 7 -i lab7_example.json -o results/lab7.md
python main.py -n 7 -i lab7_objective_parameter_example.json -o results/lab7_objective_parameter.md
```

## Модуль 8: теория игр и принятие решений

Вариант 17, дерево решений профилактического обслуживания:

```bash
python main.py -n 8 -i lab8_example.json -o results/lab8.md
```

Дополнительные файлы примеров:

```bash
python main.py -n 8 -i lab8_matrix_game_example.json -o results/lab8_matrix_game.md
python main.py -n 8 -i lab8_decision_example.json -o results/lab8_decision.md
python main.py -n 8 -i lab8_bimatrix_example.json -o results/lab8_bimatrix.md
```

## Модуль 9: целочисленное линейное программирование

```bash
python main.py -n 9 -i lab9_example.json -o results/lab9.md
python main.py -n 9 -i lab9_binary_example.json -o results/lab9_binary.md
```

## Локальный запуск без корневого запускатора

Каждый модуль можно запускать напрямую из своего каталога. Пример:

```bash
cd lab2_simplex
python main.py -i examples/lab2_example.json -s simplex_snapshot.md
```

Для локального запуска параметр результата называется `--snapshot` или `-s`.
