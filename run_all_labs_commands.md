# Команды для запуска лабораторных работ

Запуск команд выполняется из **корня репозитория**, где находится общий файл `main.py`.

Комплекс примеров перенесён на **17-й вариант**. Часть условий 17-го варианта не совпадает с типами задач, которые были изначально реализованы в соответствующих модулях. Поэтому команды ниже разделены на две группы:

1. команды, которые запускаются текущими модулями без аварийной ошибки;
2. команды-заготовки для ЛР 6 и ЛР 8, которые требуют расширения модулей.

## Подготовка каталога результатов

Linux/macOS/Git Bash:

```bash
mkdir -p results
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force results
```

# 1. Команды, которые запускаются текущими модулями

## Лабораторная работа 2

```bash
python main.py -n 2 -i lab2_example.json -o results/lab2_example.md
```

## Лабораторная работа 3

```bash
python main.py -n 3 -i lab3_dual_example.json -o results/lab3_dual_example.md
python main.py -n 3 -i lab3_tableau_example.json -o results/lab3_tableau_example.md
```

## Лабораторная работа 4

```bash
python main.py -n 4 -i lab4_transport_example.json -o results/lab4_transport_example.md
python main.py -n 4 -i lab4_unbalanced_example.json -o results/lab4_unbalanced_example.md
```

## Лабораторная работа 5

Файлы `lab5_shortest_path_example.json`, `lab5_mst_example.json`, `lab5_max_flow_example.json`, `lab5_min_cost_flow_example.json` сохранены как заготовки с условием 17-го варианта. В них не задана конкретная матрица `board`, поэтому ожидаемый статус запуска — `input_required`. Это штатное завершение, а не ошибка.

Файл `lab5_tictactoe_concrete_example.json` содержит конкретную матрицу поля и выполняет полноценную проверку предвыигрышной конфигурации.

```bash
python main.py -n 5 -i lab5_shortest_path_example.json -o results/lab5_shortest_path_example.md
python main.py -n 5 -i lab5_mst_example.json -o results/lab5_mst_example.md
python main.py -n 5 -i lab5_max_flow_example.json -o results/lab5_max_flow_example.md
python main.py -n 5 -i lab5_min_cost_flow_example.json -o results/lab5_min_cost_flow_example.md
python main.py -n 5 -i lab5_tictactoe_concrete_example.json -o results/lab5_tictactoe_concrete_example.md
```

## Лабораторная работа 7

```bash
python main.py -n 7 -i lab7_objective_parameter_example.json -o results/lab7_objective_parameter_example.md
python main.py -n 7 -i lab7_rhs_parameter_example.json -o results/lab7_rhs_parameter_example.md
```

## Лабораторная работа 9

```bash
python main.py -n 9 -i lab9_integer_example.json -o results/lab9_integer_example.md
python main.py -n 9 -i lab9_binary_example.json -o results/lab9_binary_example.md
```

## Все запускаемые команды одним блоком для Linux/macOS/Git Bash

```bash
mkdir -p results

python main.py -n 2 -i lab2_example.json -o results/lab2_example.md

python main.py -n 3 -i lab3_dual_example.json -o results/lab3_dual_example.md
python main.py -n 3 -i lab3_tableau_example.json -o results/lab3_tableau_example.md

python main.py -n 4 -i lab4_transport_example.json -o results/lab4_transport_example.md
python main.py -n 4 -i lab4_unbalanced_example.json -o results/lab4_unbalanced_example.md

python main.py -n 5 -i lab5_shortest_path_example.json -o results/lab5_shortest_path_example.md
python main.py -n 5 -i lab5_mst_example.json -o results/lab5_mst_example.md
python main.py -n 5 -i lab5_max_flow_example.json -o results/lab5_max_flow_example.md
python main.py -n 5 -i lab5_min_cost_flow_example.json -o results/lab5_min_cost_flow_example.md
python main.py -n 5 -i lab5_tictactoe_concrete_example.json -o results/lab5_tictactoe_concrete_example.md

python main.py -n 7 -i lab7_objective_parameter_example.json -o results/lab7_objective_parameter_example.md
python main.py -n 7 -i lab7_rhs_parameter_example.json -o results/lab7_rhs_parameter_example.md

python main.py -n 9 -i lab9_integer_example.json -o results/lab9_integer_example.md
python main.py -n 9 -i lab9_binary_example.json -o results/lab9_binary_example.md
```

## Все запускаемые команды одним блоком для Windows PowerShell

```powershell
New-Item -ItemType Directory -Force results

python main.py -n 2 -i lab2_example.json -o results/lab2_example.md

python main.py -n 3 -i lab3_dual_example.json -o results/lab3_dual_example.md
python main.py -n 3 -i lab3_tableau_example.json -o results/lab3_tableau_example.md

python main.py -n 4 -i lab4_transport_example.json -o results/lab4_transport_example.md
python main.py -n 4 -i lab4_unbalanced_example.json -o results/lab4_unbalanced_example.md

python main.py -n 5 -i lab5_shortest_path_example.json -o results/lab5_shortest_path_example.md
python main.py -n 5 -i lab5_mst_example.json -o results/lab5_mst_example.md
python main.py -n 5 -i lab5_max_flow_example.json -o results/lab5_max_flow_example.md
python main.py -n 5 -i lab5_min_cost_flow_example.json -o results/lab5_min_cost_flow_example.md
python main.py -n 5 -i lab5_tictactoe_concrete_example.json -o results/lab5_tictactoe_concrete_example.md

python main.py -n 7 -i lab7_objective_parameter_example.json -o results/lab7_objective_parameter_example.md
python main.py -n 7 -i lab7_rhs_parameter_example.json -o results/lab7_rhs_parameter_example.md

python main.py -n 9 -i lab9_integer_example.json -o results/lab9_integer_example.md
python main.py -n 9 -i lab9_binary_example.json -o results/lab9_binary_example.md
```

Всего в запускаемом блоке: **14 команд**.

# 2. Команды-заготовки, которые требуют расширения модулей

Эти команды оставлены как справка по файлам 17-го варианта, но текущие реализации ЛР 6 и ЛР 8 их пока не обрабатывают.

## Лабораторная работа 6

Текущие JSON-файлы ЛР 6 имеют тип:

```text
multiplicative_constraint_dynamic_programming
```

Текущий модуль ЛР 6 поддерживает только:

```text
knapsack
finite_horizon
```

Поэтому эти команды не включены в запускаемый блок:

```bash
python main.py -n 6 -i lab6_knapsack_example.json -o results/lab6_knapsack_example.md
python main.py -n 6 -i lab6_finite_horizon_example.json -o results/lab6_finite_horizon_example.md
```

## Лабораторная работа 8

Текущие JSON-файлы ЛР 8 имеют тип задачи:

```text
preventive_maintenance_decision_tree
```

Текущий модуль ЛР 8 поддерживает только:

```text
matrix_game
decision
bimatrix
```

Поэтому эти команды не включены в запускаемый блок:

```bash
python main.py -n 8 -i lab8_matrix_game_example.json -o results/lab8_matrix_game_example.md
python main.py -n 8 -i lab8_bimatrix_example.json -o results/lab8_bimatrix_example.md
python main.py -n 8 -i lab8_decision_example.json -o results/lab8_decision_example.md
```
