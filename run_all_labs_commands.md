# Команды для запуска всех лабораторных работ на всех тестовых случаях

Запуск команд выполняется из **корня репозитория**, где находится общий файл `main.py`.

Перед запуском при необходимости создайте каталог для результатов:

```bash
mkdir -p results
```

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

```bash
python main.py -n 5 -i lab5_shortest_path_example.json -o results/lab5_shortest_path_example.md
python main.py -n 5 -i lab5_mst_example.json -o results/lab5_mst_example.md
python main.py -n 5 -i lab5_max_flow_example.json -o results/lab5_max_flow_example.md
python main.py -n 5 -i lab5_min_cost_flow_example.json -o results/lab5_min_cost_flow_example.md
```

## Лабораторная работа 6

```bash
python main.py -n 6 -i lab6_knapsack_example.json -o results/lab6_knapsack_example.md
python main.py -n 6 -i lab6_finite_horizon_example.json -o results/lab6_finite_horizon_example.md
```

## Лабораторная работа 7

```bash
python main.py -n 7 -i lab7_objective_parameter_example.json -o results/lab7_objective_parameter_example.md
python main.py -n 7 -i lab7_rhs_parameter_example.json -o results/lab7_rhs_parameter_example.md
```

## Лабораторная работа 8

```bash
python main.py -n 8 -i lab8_matrix_game_example.json -o results/lab8_matrix_game_example.md
python main.py -n 8 -i lab8_bimatrix_example.json -o results/lab8_bimatrix_example.md
python main.py -n 8 -i lab8_decision_example.json -o results/lab8_decision_example.md
```

## Лабораторная работа 9

```bash
python main.py -n 9 -i lab9_integer_example.json -o results/lab9_integer_example.md
python main.py -n 9 -i lab9_binary_example.json -o results/lab9_binary_example.md
```

## Все команды одним блоком

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

python main.py -n 6 -i lab6_knapsack_example.json -o results/lab6_knapsack_example.md
python main.py -n 6 -i lab6_finite_horizon_example.json -o results/lab6_finite_horizon_example.md

python main.py -n 7 -i lab7_objective_parameter_example.json -o results/lab7_objective_parameter_example.md
python main.py -n 7 -i lab7_rhs_parameter_example.json -o results/lab7_rhs_parameter_example.md

python main.py -n 8 -i lab8_matrix_game_example.json -o results/lab8_matrix_game_example.md
python main.py -n 8 -i lab8_bimatrix_example.json -o results/lab8_bimatrix_example.md
python main.py -n 8 -i lab8_decision_example.json -o results/lab8_decision_example.md

python main.py -n 9 -i lab9_integer_example.json -o results/lab9_integer_example.md
python main.py -n 9 -i lab9_binary_example.json -o results/lab9_binary_example.md
```

Всего: **18 запусков** для всех тестовых JSON-файлов из каталогов `examples`.
