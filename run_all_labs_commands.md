# Команды запуска модулей

Файл содержит готовые команды для запуска всех лабораторных работ из корня проекта. Markdown-файлы в `results/` являются генерируемыми отчетами: их можно удалить и создать заново этими командами.

## Подготовка папки результатов

Bash / Git Bash / macOS / Linux:

```bash
mkdir -p results/lab5 results/lab6 results/lab7 results/lab8
```

PowerShell:

```powershell
New-Item -ItemType Directory -Force results/lab5, results/lab6, results/lab7, results/lab8
```

## Полный запуск варианта 17

```bash
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

## ЛР1: графический метод линейного программирования

```bash
python main.py -n 1 -i lab1_example.json -o results/lab1.md
```

Результат варианта 17:

```text
x1 = 150, y = 100, x2 = 200, F = 24750
```

## ЛР2: симплекс-метод

```bash
python main.py -n 2 -i lab2_example.json -o results/lab2.md
```

Результат варианта 17: `infeasible`. Это не ошибка программы: исходная постановка с требованием `7000` четырехкомнатных квартир и бюджетом 40 млн несовместна.

## ЛР3: двойственный симплекс-метод

```bash
python main.py -n 3 -i lab3_example.json -o results/lab3.md
```

Дополнительный запуск с готовой таблицей:

```bash
python main.py -n 3 -i lab3_tableau_example.json -o results/lab3_tableau.md
```

Результат варианта 17: `unbounded`; целевая функция не ограничена сверху.

## ЛР4: транспортная задача

```bash
python main.py -n 4 -i lab4_example.json -o results/lab4.md
python main.py -n 4 -i lab4_unbalanced_example.json -o results/lab4_unbalanced.md
```

Результат варианта 17: минимальная стоимость перевозок `7100`.

## ЛР5: сетевые модели

ЛР5 состоит из 4 заданий, а задание 2 включает 3 подзадачи. Для полной сдачи запускаются все шесть файлов.

```bash
python main.py -n 5 -i lab5_mst_example.json -o results/lab5/lab5_task1_mst.md
python main.py -n 5 -i lab5_shortest_path_example.json -o results/lab5/lab5_task2_1_shortest_path.md
python main.py -n 5 -i lab5_max_flow_example.json -o results/lab5/lab5_task2_2_max_flow.md
python main.py -n 5 -i lab5_min_cost_flow_example.json -o results/lab5/lab5_task2_3_min_cost_flow.md
python main.py -n 5 -i lab5_tictactoe_example.json -o results/lab5/lab5_task3_tictactoe.md
python main.py -n 5 -i lab5_example.json -o results/lab5/lab5_task4_project_scheduling.md
```

Контрольные результаты:

| Задание | Файл | Результат |
|---|---|---|
| 1 | `lab5_mst_example.json` | MST, вес `33` |
| 2.1 | `lab5_shortest_path_example.json` | путь `1 -> 3 -> 5 -> 6 -> 7`, длина `8` |
| 2.2 | `lab5_max_flow_example.json` | максимальный поток `23` |
| 2.3 | `lab5_min_cost_flow_example.json` | минимальная стоимость `35` при потоке `5` |
| 3 | `lab5_tictactoe_example.json` | ходы `X` в `(2;2)` и `(2;7)` |
| 4 | `lab5_example.json` | критический путь `1 -> 4 -> 6 -> 7`, длительность `21`, стоимость `186` |

## ЛР6: динамическое программирование

```bash
python main.py -n 6 -i lab6_example.json -o results/lab6.md
```

Дополнительные примеры:

```bash
python main.py -n 6 -i lab6_multiplicative_concrete_example.json -o results/lab6/lab6_multiplicative_concrete.md
python main.py -n 6 -i lab6_knapsack_example.json -o results/lab6/lab6_knapsack.md
python main.py -n 6 -i lab6_finite_horizon_example.json -o results/lab6/lab6_finite_horizon.md
```

Результат варианта 17: `symbolic_solution`. Для `n >= 2` и `c >= 0` задача максимизации не ограничена сверху; при `n = 1` и `c >= 0` имеем `z = c^2`; при `c < 0` допустимых решений нет.

## ЛР7: параметрическое линейное программирование

```bash
python main.py -n 7 -i lab7_example.json -o results/lab7.md
python main.py -n 7 -i lab7_objective_parameter_example.json -o results/lab7/lab7_objective_parameter.md
python main.py -n 7 -i lab7_rhs_parameter_example.json -o results/lab7/lab7_rhs_parameter.md
```

Результат варианта 17:

```text
-1 <= lambda <= 1/2
x1 = 1 - 2lambda
x2 = 1 + lambda
x3 = 0
Lmax = 3
```

## ЛР8: теория игр и принятие решений

Основной запуск текущего `lab8_example.json`:

```bash
python main.py -n 8 -i lab8_example.json -o results/lab8.md
```

Дополнительные файлы:

```bash
python main.py -n 8 -i lab8_renewal_example.json -o results/lab8/lab8_renewal.md
python main.py -n 8 -i lab8_matrix_game_example.json -o results/lab8/lab8_matrix_game.md
python main.py -n 8 -i lab8_decision_example.json -o results/lab8/lab8_decision.md
python main.py -n 8 -i lab8_bimatrix_example.json -o results/lab8/lab8_bimatrix.md
```

Для бумажного решения профилактического обслуживания используйте упрощенный режим. Во входном JSON должны быть поля:

```json
"use_simplified_calculation": true,
"max_cycle_months": 12
```

Тогда результат:

```text
T = 8 месяцев
стоимость парка = 397.5 долл./мес.
```

Если используется `renewal`-модель, где случайная поломка завершает цикл, результат будет другим: `T = 10`, стоимость парка около `324.454208` долл./мес.

## ЛР9: целочисленное линейное программирование

```bash
python main.py -n 9 -i lab9_example.json -o results/lab9.md
python main.py -n 9 -i lab9_binary_example.json -o results/lab9_binary.md
python main.py -n 9 -i lab9_integer_example.json -o results/lab9_integer.md
```

Результат варианта 17:

```text
A = 40, B = 31, C = 3, Fmax = 3751
```

## Локальный запуск без корневого запускатора

Каждый модуль можно запускать напрямую из своего каталога. Пример:

```bash
cd lab2_simplex
python main.py -i examples/lab2_example.json -s simplex_snapshot.md
```

Для локального запуска параметр результата называется `--snapshot` или `-s`.
