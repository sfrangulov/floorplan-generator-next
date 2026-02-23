# Алгоритм генерации планировок: Greedy + CSP

## Метаинформация

| Параметр | Значение |
|---|---|
| Версия | 1.0 |
| Дата | 2026-02-23 |
| Статус | Основной алгоритм (рекомендуемый для первой реализации) |
| Связан с | functional-requirements.md (§8 — заменяет описание алгоритма) |
| Альтернативы | algorithm-hybrid-ga-csp.md, algorithm-neural-network.md |

---

## 1. Обзор

Документ детализирует §8 «Алгоритм генерации» из functional-requirements.md. Вместо абстрактного «Backtracking CSP-солвер» здесь описан конкретный двухуровневый подход:

| Уровень | Что решает | Алгоритм | Время |
|---|---|---|---|
| **Макро** | Топология: позиции и размеры комнат | Жадный (Greedy) с scoring + рестарты | 5–80 мс |
| **Микро** | Двери, окна, стояки, мебель | CSP с backtracking | 250–2200 мс |

Общее время генерации одной планировки: **~0.5–3.5 сек** (включая рестарты).

```
┌─────────────────────────────────────────────────────────┐
│                 GREEDY LAYOUT (макро)                    │
│                                                         │
│  Состав → Размеры → Приоритетная очередь → Цикл:       │
│    ┌─ Найти candidate slots (приклеивание к размещённым)│
│    ├─ Score каждого слота (смежность, окна, зоны, ...)  │
│    └─ Выбрать лучший (softmax top-K)                    │
│                                                         │
│  Тупик? → Рестарт с новым seed                          │
└───────────────────────┬─────────────────────────────────┘
                        │ зафиксированная топология
                        ▼
┌─────────────────────────────────────────────────────────┐
│                 CSP SOLVER (микро)                       │
│                                                         │
│  Двери (backtracking по позициям на общих стенах)       │
│  → Окна (внешние стены, площадь остекления)             │
│  → Стояки (в мокрых зонах)                              │
│  → Мебель (backtracking: крупная → средняя → мелкая)    │
│                                                         │
│  CSP fail? → Greedy рестарт                             │
└───────────────────────┬─────────────────────────────────┘
                        │ полная планировка
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Валидация (P01–P34 + F01–F32) → Рендеринг SVG         │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Макро-уровень: жадное размещение комнат

### 2.1 Приоритетная очередь

Комнаты размещаются не в произвольном порядке, а от самых «требовательных» к самым «гибким». Это ключевая эвристика, снижающая вероятность тупиков:

| Приоритет | Тип помещения | Обоснование |
|---|---|---|
| 1 | HALLWAY (прихожая) | Точка входа; привязана к краю холста |
| 2 | CORRIDOR (коридор) | Связующее звено; примыкает к прихожей |
| 3 | KITCHEN | Мокрая зона + требует окно + рабочий треугольник |
| 4 | BATHROOM / TOILET / COMBINED_BATHROOM | Мокрые зоны; должны быть сгруппированы с кухней (P24) |
| 5 | LIVING_ROOM | Центральное положение (P27); требует окно; мин. ширина 3.2 м (P26) |
| 6 | BEDROOM × N | Требуют окна; непроходные (P17) |
| 7 | CHILDREN / CABINET | Требуют окна |
| 8 | STORAGE / WARDROBE / LAUNDRY | Мало ограничений; заполняют оставшееся пространство |

**Мокрый кластер (приоритеты 3–4)** размещается как единый блок: кухня первой (нужно окно), затем ванная/туалет «приклеиваются» к ней. Это гарантирует P24 (группировка мокрых зон) на уровне конструкции, а не постфактум.

Внутри одного приоритета порядок рандомизируется через `random.Random(seed)` для разнообразия.

### 2.2 Размещение первой комнаты

Прихожая размещается у одного из 4 краёв холста. Выбор края — случайный (через seed), но с ограничением: входная дверь должна быть на внешней стене.

```python
def place_hallway(hallway: Room, canvas: Rectangle, rng: random.Random) -> Position:
    edge = rng.choice(["top", "bottom", "left", "right"])
    # Позиция вдоль выбранного края — случайная
    offset = rng.uniform(0, canvas.size_along(edge) - hallway.size_along(edge))
    return snap_to_edge(hallway, canvas, edge, offset)
```

### 2.3 Candidate slots (приклеивание)

Для каждой следующей комнаты ищутся все допустимые позиции «приклеивания» к уже размещённым:

```python
def find_candidate_slots(room: Room, placed: list[Room], canvas: Rectangle) -> list[Slot]:
    candidates = []

    for target in placed:
        # Проверяем: допустимо ли вообще соседство по матрице (P16)?
        if adjacency_forbidden(room.room_type, target.room_type):
            continue

        for side in [TOP, BOTTOM, LEFT, RIGHT]:
            for align in [ALIGN_START, ALIGN_CENTER, ALIGN_END]:
                slot = attach(room, target, side, align)

                # Фильтры валидности:
                if not canvas.contains(slot.bbox):
                    continue                          # За пределами холста
                if any(slot.bbox.overlaps(p.bbox) for p in placed):
                    continue                          # Пересечение с уже размещённой
                if shared_wall_length(slot, target) < MIN_DOOR_WIDTH:
                    continue                          # Общая стена слишком короткая для двери

                candidates.append(slot)

    return candidates
```

Каждая пара (target × side × align) даёт один candidate. Для N размещённых комнат: до `N × 4 × 3 = 12N` кандидатов (на практике 10–40 после фильтрации).

### 2.4 Scoring-функция

Каждый candidate slot оценивается по взвешенной сумме критериев. Жадный алгоритм выбирает слот с максимальным score.

```python
def score_slot(room: Room, slot: Slot, placed: list[Room],
               remaining: list[Room], canvas: Rectangle) -> float:
    s = 0.0

    # ── Смежность (P16) ──────────────────────────────────
    # Бонус за каждого обязательного/желательного соседа
    s += W_ADJ * count_required_adjacencies(room, slot, placed)

    # ── Мокрый кластер (P24) ─────────────────────────────
    # Бонус за размещение мокрой зоны рядом с другой мокрой
    if room.is_wet_zone:
        s += W_WET * count_adjacent_wet_zones(slot, placed)

    # ── Внешняя стена → окно (P12, P13) ──────────────────
    # Большой бонус если комната требует окно и получает внешнюю стену
    if room.requires_window:
        has_ext = has_external_wall(slot, placed, canvas)
        s += W_WINDOW * (1.0 if has_ext else -0.5)  # Штраф если нет внешней стены

    # ── Зонирование день/ночь (P19) ──────────────────────
    # Бонус за корректное размещение в своей зоне
    s += W_ZONE * correct_zone_score(room, slot, placed)

    # ── Компактность ──────────────────────────────────────
    # Бонус за минимизацию общего bounding box (квартира не «расползается»)
    bbox_before = bounding_box(placed)
    bbox_after = bounding_box(placed + [slot])
    compactness = 1.0 - (bbox_after.area - bbox_before.area) / canvas.area
    s += W_COMPACT * compactness

    # ── Центральность гостиной (P27) ─────────────────────
    if room.room_type == LIVING_ROOM:
        s += W_CENTRAL * adjacent_to_entry_zone(slot, placed)

    # ── Look-ahead: не запираем будущие комнаты ──────────
    s -= W_BLOCK * future_blocking_penalty(slot, placed, remaining, canvas)

    return s
```

**Веса scoring-функции:**

| Вес | Значение | Что контролирует |
|---|---|---|
| W_ADJ | 10.0 | Матрица смежности (P16) |
| W_WET | 8.0 | Группировка мокрых зон (P24) |
| W_WINDOW | 15.0 | Внешняя стена для окон (P12, P13) |
| W_ZONE | 5.0 | Зонирование день/ночь (P19) |
| W_COMPACT | 3.0 | Компактность формы квартиры |
| W_CENTRAL | 12.0 | Центральность гостиной (P27) |
| W_BLOCK | 5.0 | Штраф за «запирание» будущих комнат |

Веса подобраны так, чтобы **критичные ограничения** (окна, мокрые зоны) имели приоритет над **эстетическими** (компактность, зонирование).

### 2.5 Look-ahead (предотвращение тупиков)

Главная слабость жадного алгоритма — тупики. Look-ahead на 1 шаг значительно снижает их вероятность:

```python
def future_blocking_penalty(slot: Slot, placed: list[Room],
                            remaining: list[Room], canvas: Rectangle) -> float:
    """Проверяет: если поставить комнату в slot,
    смогут ли следующие 3 комнаты найти хотя бы 1 candidate?"""
    test_placed = placed + [slot.as_room()]
    blocked = 0

    # Проверяем только ближайшие 3 комнаты (баланс точности и скорости)
    for future_room in remaining[:3]:
        future_candidates = find_candidate_slots(future_room, test_placed, canvas)
        if len(future_candidates) == 0:
            blocked += 1
        elif len(future_candidates) < 3:
            blocked += 0.3  # Мало вариантов — тоже плохой знак

    return blocked / max(len(remaining[:3]), 1)
```

Сложность: O(3 × N × 12) на один candidate — дешёвая проверка (~1–5 мс).

### 2.6 Выбор с рандомизацией (softmax top-K)

Вместо строгого выбора лучшего candidate (всегда один и тот же → нет разнообразия) используется стохастический выбор среди лучших:

```python
def select_slot(candidates: list[Slot], rng: random.Random,
                top_k: int = 3, temperature: float = 0.5) -> Slot:
    # Сортируем по score, берём top-K
    ranked = sorted(candidates, key=lambda c: c.score, reverse=True)[:top_k]

    # Softmax с температурой
    scores = [c.score / temperature for c in ranked]
    max_s = max(scores)
    exps = [math.exp(s - max_s) for s in scores]  # Numerical stability
    total = sum(exps)
    probs = [e / total for e in exps]

    # Взвешенный случайный выбор
    return rng.choices(ranked, weights=probs, k=1)[0]
```

| temperature | Поведение | Применение |
|---|---|---|
| 0.1 | Почти детерминированный (лучший candidate в >95% случаев) | Отладка |
| 0.5 | Предпочтение лучшим, но есть вариативность | **По умолчанию** |
| 1.0 | Умеренная рандомизация | Максимальное разнообразие |
| 2.0+ | Почти равномерный выбор | Не рекомендуется |

### 2.7 Обработка тупиков (рестарты)

Если `find_candidate_slots` возвращает пустой список — тупик. Стратегия — рестарт с изменённым seed:

```python
def greedy_layout(rooms_spec: list[RoomSpec], seed: int,
                  max_restarts: int = 10) -> GreedyResult | None:
    for restart in range(max_restarts):
        current_seed = seed + restart * 1000
        rng = random.Random(current_seed)

        rooms = assign_sizes(rooms_spec, rng)       # Шаг 2: случайные размеры
        queue = priority_sort(rooms, rng)            # Шаг 3: приоритетная очередь
        result = greedy_place(queue, canvas, rng)    # Шаг 4: размещение

        if result.success:
            return result

        # Каждый рестарт: другой seed → другие размеры, порядок, выборы

    return None  # Все рестарты неуспешны
```

Каждый рестарт меняет:
- Конкретные размеры комнат (в пределах допустимых диапазонов)
- Порядок комнат внутри одного приоритета
- Выбор slot-а (через softmax)
- Край холста для прихожей

**Ожидаемый success rate:**

| Конфигурация | Успех с 1-й попытки | Успех за 10 рестартов |
|---|---|---|
| 1-комн. эконом (5–6 комнат) | ~90% | ~99.9% |
| 2-комн. комфорт (7–8 комнат) | ~75% | ~99% |
| 3-комн. бизнес (9–11 комнат) | ~60% | ~97% |
| 4-комн. премиум (12–14 комнат) | ~45% | ~92% |

### 2.8 Полный псевдокод макро-уровня

```python
def greedy_place(queue: list[Room], canvas: Rectangle,
                 rng: random.Random) -> GreedyResult:
    placed: list[Room] = []

    # Первая комната — прихожая у края
    hallway = queue.pop(0)
    hallway.position = place_hallway(hallway, canvas, rng)
    placed.append(hallway)

    for room in queue:
        candidates = find_candidate_slots(room, placed, canvas)

        if not candidates:
            return GreedyResult(success=False, placed=placed,
                                failed_room=room)

        for slot in candidates:
            slot.score = score_slot(room, slot, placed,
                                     queue[queue.index(room)+1:], canvas)

        best = select_slot(candidates, rng)
        room.position = best.position
        room.attached_to = best.target
        room.shared_wall = best.shared_wall
        placed.append(room)

    return GreedyResult(success=True, placed=placed)
```

---

## 3. Микро-уровень: CSP-солвер

CSP-солвер получает зафиксированную топологию из greedy layout и размещает внутренние элементы с гарантией соблюдения ограничений.

### 3.1 Переменные и домены

| Переменная | Домен | Шаг дискретизации |
|---|---|---|
| Door_i: позиция на общей стене | [100, wall_length − 100] | 50 px |
| Door_i: направление (swing) | {INWARD, OUTWARD} | — |
| Window_j: позиция на внешней стене | [200, wall_length − 200] | 50 px |
| Window_j: размер | {900, 1200, 1500, 1800} мм | — |
| Stoyak_k: позиция | Углы и стены мокрых зон | — |
| Furniture_m: (x, y) | Сетка внутри комнаты | 50 px |
| Furniture_m: rotation | {0°, 90°, 180°, 270°} | — |

### 3.2 Порядок решения

CSP решает подзадачи последовательно:

#### Шаг 6. Двери

Для каждой пары смежных комнат (определяется по shared_wall из greedy):

```
FOR each (room_a, room_b) with shared_wall:
    wall = shared_wall(room_a, room_b)
    door_type = determine_door_type(room_a, room_b)
    door_width = door_width_by_type(door_type)  # P20

    FOR pos IN range(100, wall.length - door_width - 100, step=50):
        FOR swing IN [OUTWARD, INWARD]:
            door = Door(pos, door_type, door_width, swing)

            IF room_b.is_wet_zone AND swing != OUTWARD:
                CONTINUE                        # P21: двери санузлов наружу
            IF room_a.type == KITCHEN AND room_b.type == TOILET:
                SKIP PAIR                       # P15: запрет кухня→туалет
            IF door_wall_gap(door, wall) < 100:
                CONTINUE                        # P23: зазор ≥ 100 мм
            IF any(collides(door.swing_arc, d.swing_arc) for d in placed_doors):
                CONTINUE                        # P22: дуги не пересекаются

            PLACE door
            BREAK
    ELSE:
        RETURN CSPResult(success=False, reason="cannot_place_door")
```

#### Шаг 7. Окна

Для каждой комнаты, требующей окно (P12, P13):

```
FOR room IN rooms WHERE room.requires_window:
    ext_walls = external_walls(room, canvas)

    IF not ext_walls:
        RETURN CSPResult(success=False, reason="no_external_wall")

    needed_area = room.area_m2 / 8.0            # P14: ≥ 1/8 площади пола
    placed_window_area = 0.0

    FOR wall IN ext_walls:
        window_size = choose_window_size(needed_area - placed_window_area)
        pos = center_on_wall(wall, window_size)
        PLACE window(pos, window_size)
        placed_window_area += window.area_m2

        IF placed_window_area >= needed_area:
            BREAK
```

#### Шаг 8. Стояки

```
wet_cluster = find_wet_zone_cluster(rooms)       # Должен быть 1 кластер (P24)
stoyak_positions = corner_positions(wet_cluster)  # Углы мокрых зон

FOR stoyak_pos IN stoyak_positions:
    stoyak = Stoyak(stoyak_pos)

    # Проверяем: все унитазы ≤ 1000 мм от стояка (F32)
    IF all(dist(toilet, stoyak) <= 1000 for toilet in planned_toilets):
        PLACE stoyak
        BREAK
```

#### Шаг 9. Мебель (backtracking)

Самая сложная часть — много переменных, много ограничений:

```
FOR room IN rooms:
    furniture_list = required_furniture(room.type, apartment.class)

    # Сортируем: сначала крупная мебель, потом мелкая
    furniture_list.sort(key=lambda f: f.area, reverse=True)

    success = place_furniture_backtrack(room, furniture_list, index=0)

    IF not success:
        RETURN CSPResult(success=False, reason="furniture_fail", room=room)
```

```python
def place_furniture_backtrack(room, items, index, placed=[]):
    if index == len(items):
        return True  # Все предметы размещены

    item = items[index]
    domain = generate_positions(item, room, step=50)

    # MRV: если домен мал, предупреждение
    # Forward checking: исключить позиции, конфликтующие с placed

    for pos, rotation in domain:
        item.set(pos, rotation)

        if violates_hard_constraints(item, room, placed):
            continue

        placed.append(item)
        if place_furniture_backtrack(room, items, index + 1, placed):
            return True
        placed.pop()  # Backtrack

    return False  # Все позиции перебраны — неудача
```

### 3.3 Hard constraints (CSP)

| ID | Constraint | Правило | Описание |
|---|---|---|---|
| HC01 | no_overlap | — | Мебель не пересекается |
| HC02 | inside_room | — | Мебель внутри своей комнаты |
| HC03 | not_blocking_door | — | Мебель не перекрывает зону открывания двери |
| HC04 | toilet_axis | F01 | Ось унитаза ≥ 350 мм от стены |
| HC05 | toilet_front | F02 | Перед унитазом ≥ 600 мм |
| HC06 | sink_front | F03 | Перед раковиной ≥ 700 мм |
| HC07 | bathtub_exit | F04 | Выход из ванны ≥ 550 мм |
| HC08 | outlet_water | F05 | Розетка ≥ 600 мм от воды |
| HC09 | stove_wall | F08 | Плита ≥ 200 мм от стены |
| HC10 | stove_window | F09 | Плита ≥ 450 мм от окна |
| HC11 | hood_gas | F10 | Вытяжка-газ ≥ 750 мм |
| HC12 | hood_electric | F11 | Вытяжка-электро ≥ 650 мм |
| HC13 | oven_front | F17 | Перед духовкой ≥ 800 мм |
| HC14 | passage | F18 | Проход ≥ 700 мм |
| HC15 | washer_gap | F31 | Стиралка-стена сзади ≥ 50 мм |
| HC16 | toilet_stoyak | F32 | Унитаз ≤ 1000 мм от стояка |

### 3.4 Soft constraints (нарушение = warning, не fail)

| ID | Constraint | Правило | Описание |
|---|---|---|---|
| SC01 | triangle | F06 | Рабочий треугольник 3500–8000 мм |
| SC02 | sink_stove | F07 | Мойка-плита 800–2000 мм |
| SC03 | fridge_stove | F12 | Холодильник-плита ≥ 300 мм |
| SC04 | kitchen_rows | F13 | Между рядами ≥ 1200 мм |
| SC05 | bed_passage | F14 | Проход у кровати ≥ 700 мм |
| SC06 | wardrobe_front | F15 | Перед шкафом ≥ 800 мм |
| SC07 | drawers_front | F16 | Перед ящиками ≥ 800 мм |
| SC08 | table_wall | F19 | Стол-стена ≥ 900 мм |
| SC09 | shelf_height | F20 | Полка ≤ 1900 мм |
| SC10 | conversation | F21 | Диван-кресло ≤ 2000 мм |
| SC11 | armchairs | F22 | Между креслами ≈ 1050 мм |
| SC12 | wall_furniture | F23 | Мебель не у стены ≥ 900 мм |
| SC13 | carpet_wall | F24 | Ковёр-стена ≥ 600 мм |
| SC14 | shelving | F25 | Стеллаж-мебель ≥ 800 мм |
| SC15 | load_35 | F26 | Загрузка мебелью ≤ 35% |
| SC16 | tv_window | F27 | ТВ не напротив окна |
| SC17 | sofa_bed | F28 | Раскладной диван ≥ 2000 мм |
| SC18 | armchair_seat | F29 | Сиденье кресла ≥ 480 мм |
| SC19 | entry_zone | F30 | Зона разувания 600×800 мм |
| SC20 | dining_entry | P28 | Стол не напротив входа |

CSP пытается соблюсти soft constraints, но не делает backtrack при их нарушении — только логирует.

### 3.5 Оптимизации CSP

| Оптимизация | Описание | Эффект |
|---|---|---|
| **Forward checking** | После размещения предмета — исключить из доменов оставшихся позиции, нарушающие HC01 (overlap) и HC14 (passage) | Отсечение ~60% домена |
| **MRV** | Следующий предмет — тот, у которого осталось меньше допустимых позиций | Ранний backtrack |
| **Constraint propagation** | Пустой домен → немедленный backtrack | Экономия перебора |
| **Крупная → мелкая** | Сначала размещаем большую мебель (кровать, ванна, диван) | Крупная определяет каркас |
| **Wall-snap** | Мебель прижимается к стенам (большинство предметов ставится вдоль стен) | Сокращение домена в ~4× |
| **Spatial hash** | Быстрая проверка пересечений через пространственный хеш | O(1) вместо O(N) |

### 3.6 Результат CSP

```python
@dataclass
class CSPResult:
    success: bool
    doors: list[Door]
    windows: list[Window]
    stoyaks: list[Stoyak]
    furniture: dict[str, list[FurnitureItem]]  # room_id → мебель
    hard_violations: int       # Должно быть 0 при success=True
    soft_violations: int       # Количество нарушений мягких ограничений
    soft_details: list[str]    # Описания мягких нарушений
```

---

## 4. Полный цикл генерации

### 4.1 Одна планировка

```python
def generate_single(class_: ApartmentClass, rooms: int,
                    seed: int, max_restarts: int = 10) -> GenerationResult | None:

    rooms_spec = determine_composition(class_, rooms)  # Шаг 1

    for restart in range(max_restarts):
        s = seed + restart * 1000
        rng = random.Random(s)

        # ── Макро: Greedy ──
        greedy = greedy_layout(rooms_spec, rng)
        if not greedy.success:
            continue

        # ── Микро: CSP ──
        csp = csp_solve(greedy.placed)
        if not csp.success:
            continue

        # ── Валидация ──
        violations = validate_all(greedy.placed, csp)
        # P01–P28: реальные; P29–P34: mock (always PASS); F01–F32
        if violations.has_mandatory:
            continue

        # ── Успех ──
        return GenerationResult(
            rooms=greedy.placed,
            doors=csp.doors,
            windows=csp.windows,
            stoyaks=csp.stoyaks,
            furniture=csp.furniture,
            recommended_violations=violations.recommended_count,
            restart_number=restart,
            seed_used=s
        )

    return None
```

### 4.2 Генерация датасета

```python
def generate_dataset(class_: ApartmentClass, rooms: int, count: int,
                     seed: int, output: Path, variants: int = 1):
    metadata = []

    for i in range(count):
        result = generate_single(class_, rooms, seed + i)

        if result is None:
            log.warning(f"Не удалось сгенерировать #{i}")
            continue

        # Рендеринг SVG (если variants=2, CSP запускается дважды для mebel_1/mebel_2)
        svg = render_svg(result, variants)
        filename = f"{class_.value}_{rooms}r_{i:04d}.svg"
        save(svg, output / filename)

        metadata.append({
            "filename": filename,
            "class": class_.value,
            "rooms": rooms,
            "total_area_m2": result.total_area,
            "room_composition": result.composition,
            "recommended_violations": result.recommended_violations,
            "restart_number": result.restart_number,
        })

    save_json(metadata, output / "metadata.json")
```

### 4.3 Вариативность мебели (--variants 2)

Когда нужны два варианта расстановки мебели для одной планировки:

1. Greedy находит одну топологию (фиксированные комнаты, двери, окна, стояки)
2. CSP запускается **дважды** для мебели:
   - Первый раз: `rng_1 = Random(seed)` → mebel_1 (display:inline)
   - Второй раз: `rng_2 = Random(seed + 500)` → mebel_2 (display:none)
3. Оба результата объединяются в один SVG

---

## 5. Обязательный набор мебели по типам помещений

| Тип комнаты | Обязательная мебель | Опциональная (по классу) |
|---|---|---|
| HALLWAY | HALLWAY_WARDROBE, SHOE_RACK | BENCH, COAT_RACK |
| KITCHEN | STOVE/HOB, KITCHEN_SINK, FRIDGE, HOOD | DISHWASHER, MICROWAVE, OVEN |
| LIVING_ROOM | SOFA_2/SOFA_3, TV_STAND, COFFEE_TABLE | ARMCHAIR ×2, SHELVING, DINING_TABLE+CHAIRS |
| BEDROOM | BED_DOUBLE/BED_KING, WARDROBE_SLIDING | NIGHTSTAND ×2, DRESSER, VANITY |
| CHILDREN | CHILD_BED, CHILD_DESK, CHILD_WARDROBE | BOOKSHELF |
| BATHROOM | BATHTUB/SHOWER, SINK | WASHING_MACHINE |
| TOILET | TOILET_BOWL | SINK (маленький) |
| COMBINED_BATHROOM | BATHTUB/SHOWER, SINK, TOILET_BOWL | WASHING_MACHINE, BIDET |
| KITCHEN_DINING | всё от KITCHEN + DINING_TABLE + CHAIRS ×4 | — |
| STORAGE | — | SHELVING |
| WARDROBE | — | SHELVING, COAT_RACK |

Выбор конкретного варианта (SOFA_2 vs SOFA_3, BED_DOUBLE vs BED_KING) зависит от площади комнаты и класса жилья.

---

## 6. Производительность

### 6.1 Оценка по этапам

| Этап | Время (1 попытка) | Сложность |
|---|---|---|
| Greedy layout | 5–50 мс | O(N² × K), N = комнат, K = candidates |
| Look-ahead | 10–30 мс | O(K × 3 × N) |
| CSP: двери | 10–50 мс | O(D × P), D = дверей, P = позиций |
| CSP: окна | 5–20 мс | O(W × walls) |
| CSP: стояки | 1–5 мс | O(positions) |
| CSP: мебель | 200–2000 мс | O(M × G × 4), M = предметов, G = сетка |
| Валидация | 5–10 мс | O(rules × rooms) |
| SVG-рендеринг | 30–50 мс | O(elements) |
| **Итого (1 попытка)** | **~300–2200 мс** | |
| **Среднее с рестартами** | **~0.5–3.5 сек** | |

### 6.2 Сравнение подходов

| | Greedy + CSP | GA + CSP | GNN + CSP |
|---|---|---|---|
| **1 планировка** | ~0.5–3.5 сек | ~30–180 сек | ~0.3–2 сек |
| **100 планировок** | ~1–6 мин | ~1–5 часов | ~1–4 мин |
| **Сложность реализации** | Низкая | Средняя | Высокая |
| **Гарантия корректности** | Да (CSP) | Да (CSP) | Да (CSP) |
| **Разнообразие** | Среднее | Высокое | Высокое |
| **Оптимальность** | Нет (локальная) | Да (глобальная) | Зависит от обучения |
| **Зависимости** | Только Python | Только Python | Python + PyTorch + PyG |
| **Нужны данные** | Нет | Нет | Да (≥ 10 000) |

### 6.3 Параллелизация

Генерация разных планировок полностью независима:

```bash
floorplan generate --class comfort --rooms 2 --count 100 --output ./dataset --seed 42 --workers 4
```

Реализация: `concurrent.futures.ProcessPoolExecutor(max_workers)`.

---

## 7. Обработка неудач

| Ситуация | Действие |
|---|---|
| Greedy: тупик (нет candidates) | Рестарт с seed + 1000 |
| CSP: не может разместить дверь | Рестарт greedy (другая топология) |
| CSP: комната без внешней стены для окна | Рестарт greedy |
| CSP: не может разместить мебель | Рестарт; если 3+ рестарта по мебели — уменьшить набор (убрать опциональную) |
| Валидация: обязательное правило нарушено | Рестарт greedy |
| Все max_restarts исчерпаны | Залогировать, пропустить, перейти к следующему seed |
| Success rate < 90% на конфигурации | Увеличить max_restarts или перейти на GA+CSP для этой конфигурации |

---

## 8. Обновления к functional-requirements.md

### 8.1 Структура проекта (§3)

Заменить `generator/solver.py` на:

```
├── generator/
│   ├── greedy/
│   │   ├── priority.py           # Приоритетная очередь комнат
│   │   ├── candidates.py         # Поиск candidate slots
│   │   ├── scoring.py            # Функция оценки слотов
│   │   └── engine.py             # Главный цикл greedy + рестарты
│   ├── csp/
│   │   ├── solver.py             # CSP backtracking солвер
│   │   ├── constraints.py        # Hard + soft constraints
│   │   ├── door_placer.py        # Размещение дверей
│   │   ├── window_placer.py      # Размещение окон
│   │   ├── stoyak_placer.py      # Размещение стояков
│   │   └── furniture_placer.py   # Размещение мебели
│   ├── layout_engine.py          # Оркестратор: Greedy → CSP → Validate
│   └── factory.py                # Фабрика генерации
```

### 8.2 Дополнительные тесты

#### Unit-тесты Greedy (test_greedy.py)

| # | Тест | Описание |
|---|---|---|
| GR01 | test_priority_queue_order | Порядок: прихожая → коридор → мокрые → гостиная → спальни |
| GR02 | test_hallway_at_edge | Прихожая размещается у края холста |
| GR03 | test_candidates_no_overlap | Все candidate slots не пересекаются с placed |
| GR04 | test_candidates_inside_canvas | Все candidate slots внутри холста |
| GR05 | test_candidates_shared_wall_min | Общая стена ≥ MIN_DOOR_WIDTH |
| GR06 | test_scoring_window_bonus | Комната с требованием окна: слот у внешней стены > внутренний |
| GR07 | test_scoring_wet_cluster_bonus | Мокрая зона рядом с мокрой > рядом с жилой |
| GR08 | test_scoring_adjacency_bonus | Обязательный сосед по P16 > необязательный |
| GR09 | test_scoring_central_living_room | Гостиная рядом с прихожей > далеко от неё |
| GR10 | test_scoring_lookahead_penalty | Slot, блокирующий будущую комнату, штрафуется |
| GR11 | test_select_softmax_deterministic_low_temp | temperature=0.01 → всегда лучший |
| GR12 | test_select_softmax_varies_with_seed | Разные seed → разные выборы при temperature=0.5 |
| GR13 | test_restart_changes_seed | Рестарт использует seed + N*1000 |
| GR14 | test_restart_success_after_deadend | Тупик → рестарт → успех |
| GR15 | test_reproducible_with_same_seed | Один seed → один результат |
| GR16 | test_different_seeds_different_layouts | Разные seed → разные планировки |
| GR17 | test_economy_1room_success_rate | ≥ 90% успех с 1-й попытки (100 runs) |
| GR18 | test_comfort_2room_success_10_restarts | ≥ 99% успех за 10 рестартов (50 runs) |

#### Unit-тесты CSP (test_csp.py)

| # | Тест | Описание |
|---|---|---|
| CS01 | test_door_on_shared_wall | Дверь размещается на общей стене |
| CS02 | test_door_gap_100mm | Зазор дверь-стена ≥ 100 мм (P23) |
| CS03 | test_door_swing_no_collision | Дуги подметания не пересекаются (P22) |
| CS04 | test_bathroom_door_outward | Дверь санузла наружу (P21) |
| CS05 | test_no_toilet_from_kitchen | Нет двери кухня→туалет (P15) |
| CS06 | test_window_on_external_wall | Окно только на внешней стене |
| CS07 | test_window_area_sufficient | Площадь остекления ≥ 1/8 (P14) |
| CS08 | test_stoyak_in_wet_zone | Стояк в мокрой зоне |
| CS09 | test_toilet_near_stoyak | Унитаз ≤ 1000 мм от стояка (F32) |
| CS10 | test_furniture_no_overlap | Мебель не пересекается |
| CS11 | test_furniture_inside_room | Мебель внутри своей комнаты |
| CS12 | test_furniture_not_blocking_door | Мебель не перекрывает дверь |
| CS13 | test_passage_700mm | Проходы ≥ 700 мм (F18) |
| CS14 | test_forward_checking_prunes | Forward checking уменьшает домен |
| CS15 | test_csp_success_valid_topology | CSP успешен на валидной топологии |
| CS16 | test_csp_fail_impossible_room | CSP возвращает fail при невозможной комнате |
| CS17 | test_two_variants_different_furniture | Два вызова с разным seed → разная мебель |

#### Интеграционные тесты (test_greedy_csp_integration.py)

| # | Тест | Описание |
|---|---|---|
| GI01 | test_full_pipeline_economy_1room | Greedy → CSP → Validate → SVG для 1-комн. |
| GI02 | test_full_pipeline_comfort_2room | Для 2-комн. комфорт |
| GI03 | test_full_pipeline_business_3room | Для 3-комн. бизнес |
| GI04 | test_full_pipeline_premium_4room | Для 4-комн. премиум |
| GI05 | test_greedy_restart_on_deadend | Тупик greedy → рестарт → CSP → успех |
| GI06 | test_csp_fail_triggers_restart | CSP fail → greedy рестарт → успех |
| GI07 | test_all_mandatory_rules_pass | 0 нарушений обязательных правил |
| GI08 | test_mock_rules_always_pass | P29–P34 всегда PASS |
| GI09 | test_batch_100_unique | 100 планировок — все уникальны |
| GI10 | test_metadata_json_correct | metadata.json содержит restart_number |

#### Сводка дополнительных тестов

| Категория | Файл | Кол-во |
|---|---|---|
| Greedy | test_greedy.py | 18 |
| CSP | test_csp.py | 17 |
| Интеграция Greedy+CSP | test_greedy_csp_integration.py | 10 |
| **Итого дополнительных** | | **45** |
| **Общий итог (с functional-requirements.md)** | | **202 + 45 = 247** |

### 8.3 Обновление TDD-фаз (§11)

Заменить Фазу 3 на:

**Фаза 3A: Greedy Layout**
1. test_greedy.py — 18 тестов (красные)
2. greedy/priority.py — приоритетная очередь
3. greedy/candidates.py — поиск candidate slots
4. greedy/scoring.py — функция оценки + look-ahead
5. greedy/engine.py — главный цикл + рестарты → 18 тестов зелёные

**Фаза 3B: CSP Solver**
6. test_csp.py — 17 тестов (красные)
7. csp/constraints.py — hard + soft constraints
8. csp/door_placer.py
9. csp/window_placer.py
10. csp/stoyak_placer.py
11. csp/furniture_placer.py
12. csp/solver.py → 17 тестов зелёные

**Фаза 3C: Интеграция**
13. test_greedy_csp_integration.py — 10 тестов (красные)
14. layout_engine.py — оркестратор Greedy → CSP → Validate
15. factory.py → 10 тестов зелёные

### 8.4 Обновление критериев приёмки (§12)

| Критерий | Метрика |
|---|---|
| Все unit-тесты | 208/208 green |
| Все интеграционные тесты | 24/24 green |
| Все SVG-тесты | 15/15 green |
| Покрытие кода | ≥ 90% |
| Greedy success rate (10 рестартов) | ≥ 95% на всех конфигурациях |
| CSP success rate | ≥ 90% на топологиях от Greedy |
| Обязательные правила | 0 нарушений |
| Генерация 1 планировки | ≤ 5 сек |
| Датасет 100 планировок (4 workers) | ≤ 10 мин |
| Уникальность | Нет дубликатов (при разных seed) |
| Воспроизводимость | Одинаковый seed → идентичный результат |

---

## 9. Возможные улучшения (roadmap)

| Улучшение | Сложность | Эффект |
|---|---|---|
| Look-ahead на 2 шага | Средняя | Снижение тупиков на 10–15% |
| Адаптивные веса scoring | Низкая | Разные веса для разных классов/конфигураций |
| Beam search вместо greedy | Средняя | Параллельно вести K лучших вариантов (K=3–5) |
| Greedy + ограниченный backtrack | Средняя | При тупике — откат на 1–2 комнаты вместо полного рестарта |
| Замена на GA (algorithm-hybrid-ga-csp.md) | Высокая | Глобальная оптимизация для сложных конфигураций |
| Замена на GNN (algorithm-neural-network.md) | Высокая | ~100× ускорение (нужен обучающий датасет) |

---

*Документ детализирует §8 functional-requirements.md. Рекомендуемый основной алгоритм для первой реализации. Для сложных конфигураций (4+ комнат премиум) см. algorithm-hybrid-ga-csp.md как fallback.*
