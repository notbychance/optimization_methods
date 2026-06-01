# ЛР8. Теория игр и принятие решений

Модуль рассчитывает матричные игры, критерии принятия решений, биматричные игры и дерево решений профилактического обслуживания.

## Поддерживаемые типы задач

| `task_type` | Назначение |
|---|---|
| `matrix_game` | матричная игра двух игроков с нулевой суммой |
| `decision` | выбор альтернативы по критериям принятия решений |
| `bimatrix` | биматричная игра с поиском равновесий Нэша в чистых стратегиях |
| `preventive_maintenance_decision_tree` | дерево решений для выбора цикла профилактического обслуживания |

## Возможности

Для `matrix_game`:

- нижняя и верхняя цена игры;
- седловые точки;
- чистые оптимальные стратегии;
- смешанные стратегии перебором носителей;
- решение систем методом Гаусса-Жордана.

Для `decision`:

- критерий Вальда;
- критерий максимакса;
- критерий Лапласа;
- критерий Гурвица;
- критерий Сэвиджа;
- критерий Байеса при заданных вероятностях состояний.

Для `bimatrix`:

- взаимные лучшие ответы;
- равновесия Нэша в чистых стратегиях.

Для `preventive_maintenance_decision_tree`:

- перебор длин профилактического цикла;
- расчет ожидаемой стоимости;
- построение текстового дерева решений;
- два режима расчета: упрощенный фиксированный цикл и renewal-модель.

## Структура

```text
lab8_game_theory/
├── main.py
├── game_theory.py
├── game_models.py
├── matrix_tools.py
├── fraction_tools.py
├── problem_reader.py
├── snapshot.py
├── README.md
└── examples/
    ├── lab8_example.json
    ├── lab8_renewal_example.json
    ├── lab8_matrix_game_example.json
    ├── lab8_decision_example.json
    └── lab8_bimatrix_example.json
```

## Запуск

Из корня проекта:

```bash
python main.py -n 8 -i lab8_example.json -o results/lab8.md
```

Дополнительные примеры:

```bash
python main.py -n 8 -i lab8_renewal_example.json -o results/lab8_renewal.md
python main.py -n 8 -i lab8_matrix_game_example.json -o results/lab8_matrix_game.md
python main.py -n 8 -i lab8_decision_example.json -o results/lab8_decision.md
python main.py -n 8 -i lab8_bimatrix_example.json -o results/lab8_bimatrix.md
```

Из каталога модуля:

```bash
python main.py -i examples/lab8_example.json -s game_theory_snapshot.md
```

## Вариант 17: профилактический ремонт автомобилей

Условие:

- парк: 20 грузовых автомобилей;
- стоимость случайной поломки: 200 долл.;
- стоимость планового профилактического ремонта: 75 долл.;
- вероятность поломки в 1-й месяц равна 0;
- во 2-й месяц — 0.03;
- далее вероятность растет на 0.01 до 10-го месяца включительно;
- начиная с 11-го месяца вероятность равна 0.13.

## Формат JSON для профилактического ремонта

```json
{
  "task_type": "preventive_maintenance_decision_tree",
  "fleet_size": 20,
  "failure_probability_by_month": {
    "1": 0,
    "2": 0.03,
    "3": 0.04,
    "10": 0.11,
    "11_and_later": 0.13
  },
  "random_failure_cost": 200,
  "preventive_repair_cost": 75,
  "max_cycle_months": 12,
  "use_simplified_calculation": true
}
```

## Режимы расчета профилактического обслуживания

### 1. Упрощенная модель фиксированного цикла

Включается одним из способов:

```json
"use_simplified_calculation": true
```

или

```json
"calculation_model": "simplified_fixed_cycle"
```

Формула:

```text
K(T) = N * (Cp + Cf * sum(p_i, i = 1..T)) / T
```

где `N = 20`, `Cp = 75`, `Cf = 200`.

При просмотре циклов `T = 1..12` результат совпадает с бумажным расчетом:

```text
T = 8 месяцев
средняя стоимость на 1 автомобиль = 19.875 долл./мес.
средняя стоимость для парка = 397.5 долл./мес.
```

### 2. Renewal-модель

Включается одним из способов:

```json
"use_simplified_calculation": false
```

или

```json
"calculation_model": "renewal"
```

В этой модели случайная поломка завершает текущий цикл и запускает новый. Для тех же вероятностей получается другой результат:

```text
T = 10 месяцев
средняя стоимость на 1 автомобиль ~= 16.222710 долл./мес.
средняя стоимость для парка ~= 324.454208 долл./мес.
```

Если в JSON не задан ни флаг, ни `calculation_model`, используется значение по умолчанию `renewal`.

## Прочие форматы JSON

### Матричная игра

```json
{
  "task_type": "matrix_game",
  "payoff_matrix": [[2, 1], [0, 3]],
  "row_strategy_names": ["A1", "A2"],
  "column_strategy_names": ["B1", "B2"]
}
```

### Критерии принятия решений

```json
{
  "task_type": "decision",
  "objective": "max",
  "alternatives": ["Проект A", "Проект B"],
  "states": ["S1", "S2"],
  "payoff_matrix": [[10, 5], [7, 8]],
  "probabilities": [0.4, 0.6],
  "hurwicz_alpha": "1/2"
}
```

### Биматричная игра

```json
{
  "task_type": "bimatrix",
  "row_player_matrix": [[2, 0], [3, 1]],
  "column_player_matrix": [[1, 2], [0, 1]]
}
```

## Статусы

| Статус | Смысл |
|---|---|
| `optimal_cycle_found` | найден оптимальный цикл профилактического обслуживания |
| `pure_saddle_point` | найдена седловая точка матричной игры |
| `mixed_strategy` | найдены смешанные стратегии |
| `criteria_evaluated` | рассчитаны критерии принятия решений |
| `pure_nash_equilibria_found` | найдены равновесия Нэша в чистых стратегиях |
| `no_pure_nash_equilibrium` | равновесий Нэша в чистых стратегиях нет |
