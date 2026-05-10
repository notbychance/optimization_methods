# Команды запуска модулей

Файл содержит готовые команды для запуска всех модулей из корня проекта. Команды используют входные JSON-файлы из каталогов `examples` и сохраняют Markdown-протоколы в папку `results`.

## Подготовка папки результатов

Bash / Git Bash / macOS / Linux:

```bash
mkdir -p results
```

PowerShell:

```powershell
New-Item -ItemType Directory -Force results
```

## Полный запуск по одному примеру на модуль

```bash
python main.py -n 2 -i lab2_example.json -o results/lab2_simplex.md
python main.py -n 3 -i lab3_dual_example.json -o results/lab3_dual_simplex.md
python main.py -n 4 -i lab4_transport_example.json -o results/lab4_transportation.md
python main.py -n 5 -i lab5_tictactoe_concrete_example.json -o results/lab5_network_models.md
python main.py -n 6 -i lab6_multiplicative_concrete_example.json -o results/lab6_dynamic_programming.md
python main.py -n 7 -i lab7_rhs_parameter_example.json -o results/lab7_parametric_lp.md
python main.py -n 8 -i lab8_decision_example.json -o results/lab8_game_theory.md
python main.py -n 9 -i lab9_integer_example.json -o results/lab9_integer_lp.md
```

## Модуль 2: двухфазный симплекс-метод

```bash
python main.py -n 2 -i lab2_example.json -o results/lab2_simplex.md
```

## Модуль 3: двойственный симплекс-метод

Ввод математической модели:

```bash
python main.py -n 3 -i lab3_dual_example.json -o results/lab3_dual_model.md
```

Ввод готовой таблицы:

```bash
python main.py -n 3 -i lab3_tableau_example.json -o results/lab3_dual_tableau.md
```

## Модуль 4: транспортная задача

```bash
python main.py -n 4 -i lab4_transport_example.json -o results/lab4_transportation.md
python main.py -n 4 -i lab4_unbalanced_example.json -o results/lab4_transportation_unbalanced.md
```

## Модуль 5: сетевые модели и проверка поля

Проверка конкретной конфигурации поля:

```bash
python main.py -n 5 -i lab5_tictactoe_concrete_example.json -o results/lab5_tictactoe_concrete.md
```

Дополнительные файлы примеров:

```bash
python main.py -n 5 -i lab5_shortest_path_example.json -o results/lab5_shortest_path_example.md
python main.py -n 5 -i lab5_mst_example.json -o results/lab5_mst_example.md
python main.py -n 5 -i lab5_max_flow_example.json -o results/lab5_max_flow_example.md
python main.py -n 5 -i lab5_min_cost_flow_example.json -o results/lab5_min_cost_flow_example.md
python main.py -n 5 -i lab5_project_scheduling_example.json -o results/lab5_project_scheduling_example.md
```

Если во входном файле вместо конкретной матрицы поля задано текстовое описание, модуль завершится штатным статусом `input_required`.

## Модуль 6: динамическое программирование

Числовой пример для задачи с мультипликативным ограничением:

```bash
python main.py -n 6 -i lab6_multiplicative_concrete_example.json -o results/lab6_multiplicative_concrete.md
```

Дополнительные файлы примеров:

```bash
python main.py -n 6 -i lab6_knapsack_example.json -o results/lab6_knapsack_example.md
python main.py -n 6 -i lab6_finite_horizon_example.json -o results/lab6_finite_horizon_example.md
```

Если параметры модели заданы символически, модуль завершится штатным статусом `input_required`.

## Модуль 7: параметрическое линейное программирование

```bash
python main.py -n 7 -i lab7_objective_parameter_example.json -o results/lab7_objective_parameter.md
python main.py -n 7 -i lab7_rhs_parameter_example.json -o results/lab7_rhs_parameter.md
```

## Модуль 8: теория игр и принятие решений

```bash
python main.py -n 8 -i lab8_matrix_game_example.json -o results/lab8_matrix_game.md
python main.py -n 8 -i lab8_decision_example.json -o results/lab8_decision.md
python main.py -n 8 -i lab8_bimatrix_example.json -o results/lab8_bimatrix.md
```

Все три файла могут содержать один и тот же тип задачи. Фактический режим определяется полем `task_type` внутри JSON.

## Модуль 9: целочисленное линейное программирование

```bash
python main.py -n 9 -i lab9_integer_example.json -o results/lab9_integer.md
python main.py -n 9 -i lab9_binary_example.json -o results/lab9_binary.md
```

## Локальный запуск без корневого запускатора

Каждый модуль можно запускать напрямую из своего каталога. Пример:

```bash
cd lab2_simplex
python main.py -i examples/lab2_example.json -s simplex_snapshot.md
```

Для локального запуска параметр результата называется `--snapshot` или `-s`.
