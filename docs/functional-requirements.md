# Функциональные требования и спецификация тестов: Генератор планировок квартир (floorplan-generator)

## Метаинформация

| Параметр | Значение |
|---|---|
| Версия документа | 1.0 |
| Дата | 2026-02-23 |
| Статус | Черновик |
| Связанные документы | apartment-planning-rules.md, equipment-furniture-rules.md, rules.docx |
| Эталонный SVG | plan_example.svg |

---

## 1. Назначение продукта

Генератор планировок квартир — CLI-инструмент на Python для создания **синтетического датасета** планировок квартир в формате SVG. Каждая сгенерированная планировка должна соблюдать российские строительные нормы (СП 54.13330.2022, СНиП 31-01-2003, СанПиН, ГОСТ 13025) и эргономические стандарты расстановки мебели (Э. Нойферт).

Целевое использование датасета — обучение и тестирование ML-моделей распознавания и оценки планировок.

---

## 2. Технический стек

| Компонент | Технология | Обоснование |
|---|---|---|
| Язык | Python 3.12+ | Целевая платформа |
| Менеджер пакетов | uv | Быстрое разрешение зависимостей |
| Доменные модели | Pydantic v2 | Валидация на уровне моделей |
| CLI | typer | Декларативный CLI с автодокументацией |
| SVG-генерация | lxml | Прямой контроль над XML/SVG |
| Тесты | pytest + pytest-cov | TDD, покрытие ≥ 90% |
| Линтер | ruff | Быстрый анализ кода |

---

## 3. Структура проекта

```
floorplan-generator/
├── pyproject.toml
├── src/floorplan_generator/
│   ├── __init__.py
│   ├── cli.py                      # Typer CLI
│   ├── core/
│   │   ├── models.py               # Apartment, Room, Door, Window, FurnitureItem
│   │   ├── dimensions.py           # Все константы размеров из нормативных документов
│   │   ├── enums.py                # RoomType, ApartmentClass, DoorType, FurnitureType...
│   │   └── geometry.py             # Point, Rectangle, Polygon, distance(), overlap()
│   ├── rules/
│   │   ├── rule_engine.py          # ABC RuleValidator + RuleViolation + RuleResult
│   │   ├── planning_rules.py       # P01–P28: правила планировки + P29–P34: mock-правила
│   │   ├── furniture_rules.py      # F01–F32: правила расстановки мебели
│   │   └── registry.py             # RuleRegistry — реестр всех правил
│   ├── generator/
│   │   ├── solver.py               # Backtracking CSP-солвер
│   │   ├── layout_engine.py        # Размещение комнат в 2D
│   │   ├── furniture_placer.py     # Расстановка мебели в комнатах
│   │   └── factory.py              # Фабрика генерации по классу/кол-ву комнат
│   └── rendering/
│       ├── svg_builder.py          # Генерация SVG
│       ├── furniture_library.py    # Библиотека SVG-сниппетов мебели
│       └── style.py                # Стили линий, заливок
├── tests/
│   ├── conftest.py                 # Фикстуры и хелперы
│   ├── unit/
│   │   ├── test_geometry.py        # Геометрические утилиты
│   │   ├── test_models.py          # Валидация моделей
│   │   ├── test_planning_rules.py  # Тесты правил планировки
│   │   └── test_furniture_rules.py # Тесты правил расстановки
│   ├── integration/
│   │   ├── test_generation.py      # Полный цикл генерации
│   │   └── test_validation.py      # Все правила на сгенерированных планах
│   └── svg/
│       └── test_svg_output.py      # Валидность SVG, структура групп
└── data/
    └── furniture_library.json      # Извлечённые SVG-сниппеты мебели из plan_example.svg
```

---

## 4. Доменная модель

### 4.1 Перечисления (enums.py)

**RoomType** — тип помещения:

| Значение | Описание | Мокрая зона | Требует окна |
|---|---|---|---|
| LIVING_ROOM | Гостиная / общая комната | Нет | Да |
| BEDROOM | Спальня | Нет | Да |
| CHILDREN | Детская | Нет | Да |
| CABINET | Кабинет | Нет | Да |
| KITCHEN | Кухня | Да | Да |
| KITCHEN_DINING | Кухня-столовая | Да | Да |
| KITCHEN_NICHE | Кухня-ниша | Да | Нет |
| HALLWAY | Прихожая / передняя | Нет | Нет |
| CORRIDOR | Коридор | Нет | Нет |
| HALL | Холл | Нет | Нет |
| BATHROOM | Ванная | Да | Нет |
| TOILET | Туалет (уборная) | Да | Нет |
| COMBINED_BATHROOM | Совмещённый санузел | Да | Нет |
| STORAGE | Кладовая | Нет | Нет |
| WARDROBE | Гардеробная | Нет | Нет |
| LAUNDRY | Постирочная | Да | Нет |
| BALCONY | Балкон / лоджия | Нет | Н/Д |

**ApartmentClass** — класс жилья:

| Значение | Описание |
|---|---|
| ECONOMY | Эконом |
| COMFORT | Комфорт |
| BUSINESS | Бизнес |
| PREMIUM | Премиум / Элит |

**DoorType** — тип двери:

| Значение | Описание |
|---|---|
| ENTRANCE | Входная |
| INTERIOR | Межкомнатная (жилая комната) |
| INTERIOR_WIDE | Межкомнатная широкая (гостиная) |
| DOUBLE | Двустворчатая |
| KITCHEN | Кухонная |
| BATHROOM | Ванная / туалет |
| COMBINED_BATHROOM | Совмещённый санузел |

**SwingDirection** — направление открывания:

| Значение | Описание |
|---|---|
| INWARD | Внутрь помещения |
| OUTWARD | Наружу (в коридор / к эвакуации) |

**FurnitureType** — тип мебели / оборудования (основные категории):

| Категория | Элементы |
|---|---|
| Сантехника | BATHTUB, SHOWER, SINK, DOUBLE_SINK, TOILET_BOWL, BIDET, WASHING_MACHINE, DRYER |
| Кухня | STOVE, HOB, OVEN, FRIDGE, FRIDGE_SIDE_BY_SIDE, DISHWASHER, KITCHEN_SINK, HOOD, MICROWAVE |
| Гостиная | SOFA_2, SOFA_3, SOFA_4, SOFA_CORNER, ARMCHAIR, COFFEE_TABLE, TV_STAND, SHELVING |
| Спальня | BED_SINGLE, BED_DOUBLE, BED_KING, NIGHTSTAND, DRESSER, WARDROBE_SLIDING, WARDROBE_SWING, VANITY |
| Детская | CHILD_BED, CHILD_DESK, CHILD_WARDROBE |
| Прихожая | HALLWAY_WARDROBE, SHOE_RACK, BENCH, COAT_RACK |
| Общее | DINING_TABLE, DINING_CHAIR, DESK, BOOKSHELF |

**FunctionalZone** — функциональная зона:

| Значение | Описание |
|---|---|
| ENTRY | Входная зона |
| DAY | Дневная (общественная) |
| NIGHT | Ночная (приватная) |

**LayoutType** — тип расстановки мебели в гостиной:

| Значение | Описание |
|---|---|
| SYMMETRIC | Симметричная |
| ASYMMETRIC | Асимметричная |
| CIRCULAR | Круговая (радиальная) |

**KitchenLayoutType** — тип планировки кухни:

| Значение | Описание | Мин. площадь |
|---|---|---|
| LINEAR | Линейная | 5 м² |
| L_SHAPED | Г-образная (угловая) | 7 м² |
| U_SHAPED | П-образная | 10 м² |
| PARALLEL | Двурядная (параллельная) | 9 м² |
| ISLAND | Островная | 15 м² |
| PENINSULA | С полуостровом | 12 м² |

### 4.2 Геометрические примитивы (geometry.py)

**Point(x: float, y: float)** — точка в 2D-пространстве.

**Rectangle(x: float, y: float, width: float, height: float)** — прямоугольник, выровненный по осям.
Вычисляемые свойства: center, area, aspect_ratio, corners, contains(point), overlaps(other), distance_to(other).

**Polygon(points: list[Point])** — произвольный многоугольник.
Вычисляемые свойства: area, perimeter, bounding_box, centroid, contains(point).

**Segment(start: Point, end: Point)** — отрезок.
Вычисляемые свойства: length, midpoint, intersects(other).

**Функции:** distance(a, b), segments_intersect(s1, s2), point_in_polygon(point, polygon), rectangles_overlap(r1, r2), min_distance_rect_to_rect(r1, r2).

### 4.3 Константы размеров (dimensions.py)

Все числовые значения из apartment-planning-rules.md и equipment-furniture-rules.md организуются как именованные константы с единицами измерения в миллиметрах.

Группы констант: MIN_AREAS (м²), MIN_WIDTHS (мм), MIN_HEIGHTS (мм), DOOR_SIZES (мм), WINDOW_RATIOS, ADJACENCY_MATRIX, FURNITURE_SIZES (мм), CLEARANCES (мм), KITCHEN_TRIANGLE (мм).

### 4.4 Модели предметной области (models.py)

**Window(id, position: Point, width: float, height: float, wall_side: str)**
Вычисляемое: area_m2.

**Door(id, position: Point, width: float, door_type: DoorType, swing: SwingDirection, room_from: str, room_to: str)**
Вычисляемое: swing_arc (Rectangle — зона подметания полотна).

**FurnitureItem(id, furniture_type: FurnitureType, position: Point, width: float, depth: float, rotation: float)**
Вычисляемое: bounding_box, clearance_zone (зона доступа перед предметом).

**Room(id, room_type: RoomType, boundary: Polygon, doors: list[Door], windows: list[Window], furniture: list[FurnitureItem])**
Вычисляемое: area_m2, width_m, height_m, aspect_ratio, is_wet_zone, requires_window, free_area_ratio.

**Apartment(id, apartment_class: ApartmentClass, rooms: list[Room], num_rooms: int)**
Вычисляемое: total_area_m2, living_area_m2, adjacency_graph, functional_zones, room_composition.

---

## 5. Реестр правил

### 5.1 Правила планировки (P01–P28 + Mock P29–P34)

| ID | Название | Описание | Тип | Параметры проверки | Нормативная база |
|---|---|---|---|---|---|
| P01 | Мин. площадь гостиной (1-комн.) | Площадь общей комнаты в 1-комн. квартире ≥ 14 м² | Обяз. | room.area_m2 ≥ 14 при apartment.num_rooms == 1 | СП 54, п.5.11 |
| P02 | Мин. площадь гостиной (2+ комн.) | Площадь общей комнаты в 2+ комн. квартире ≥ 16 м² | Обяз. | room.area_m2 ≥ 16 при apartment.num_rooms ≥ 2 | СП 54, п.5.11 |
| P03 | Мин. площадь спальни (1 чел.) | Площадь спальни на 1 человека ≥ 8 м² | Обяз. | room.area_m2 ≥ 8 | СП 54, п.5.11 |
| P04 | Мин. площадь спальни (2 чел.) | Площадь спальни на 2 человека ≥ 10 м² | Обяз. | room.area_m2 ≥ 10 | СП 54, п.5.11 |
| P05 | Мин. площадь кухни | Кухня ≥ 8 м²; в 1-комн. допускается 5 м² | Обяз. | room.area_m2 ≥ 8 (или ≥ 5 при num_rooms==1) | СП 54, п.5.11 |
| P06 | Мин. ширина кухни | Ширина кухни ≥ 1700 мм | Обяз. | room.width_m ≥ 1.7 | СП 54 |
| P07 | Мин. ширина коридора | Ширина коридора ≥ 850 мм (при длине > 1.5 м — ≥ 1000 мм) | Обяз. | room.width_m ≥ 0.85 (или ≥ 1.0) | СП 54 |
| P08 | Мин. ширина прихожей | Ширина прихожей ≥ 1400 мм | Обяз. | room.width_m ≥ 1.4 | СП 54 |
| P09 | Мин. ширина ванной | Ширина ванной ≥ 1500 мм | Обяз. | room.width_m ≥ 1.5 | СП 54 |
| P10 | Мин. ширина совм. санузла | Ширина совм. санузла ≥ 1700 мм | Обяз. | room.width_m ≥ 1.7 | СП 54 |
| P11 | Пропорции жилой комнаты | Соотношение сторон жилой комнаты ≤ 1:2 | Рек. | room.aspect_ratio ≤ 2.0 | Практика |
| P12 | Окна в жилых комнатах | Жилые комнаты обязаны иметь хотя бы одно окно | Обяз. | len(room.windows) ≥ 1 для жилых | СП 54 |
| P13 | Окна в кухне | Кухня обязана иметь окно (кроме кухни-ниши с электроплитой) | Обяз. | len(room.windows) ≥ 1 для KITCHEN/KITCHEN_DINING | СП 54 |
| P14 | Площадь остекления | Суммарная площадь окон ≥ 1/8 площади пола помещения | Обяз. | sum(w.area_m2) ≥ room.area_m2 / 8 | СНиП 23-05 |
| P15 | Запрет вход в туалет из кухни | Дверь из кухни не может вести напрямую в туалет с унитазом | Обяз. | нет двери Kitchen→Toilet | СП 54, п.5.12 |
| P16 | Матрица смежности | Все пары смежных помещений (связанных дверью) соответствуют матрице допустимости | Обяз. | adjacency_matrix[from][to] ∈ {+, (у)} | СП 54 |
| P17 | Непроходные спальни | В 2+ комн. квартирах спальни не должны быть проходными (≤ 1 дверь в спальню) | Обяз. | doors_count(BEDROOM) ≤ 1 (кроме входной) | СНиП 31-01 |
| P18 | Обязательный состав | Квартира содержит: ≥ 1 жилая комната + кухня + санузел + прихожая | Обяз. | наличие всех типов | СП 54, п.5.3 |
| P19 | Зонирование день/ночь | Дневная и ночная зоны не пересекаются транзитным движением | Рек. | graph analysis: нет транзита через ночную зону к дневной | Практика |
| P20 | Мин. ширина входной двери | Входная дверь ≥ 800 мм | Обяз. | door.width ≥ 800 | СП 3.13130 |
| P21 | Двери санузлов наружу | Двери санузлов открываются наружу (в коридор) | Обяз. | door.swing == OUTWARD для BATHROOM/TOILET | СП 54 |
| P22 | Двери не сталкиваются | Зоны подметания полотен соседних дверей не пересекаются | Обяз. | !overlaps(door_i.swing_arc, door_j.swing_arc) | СП 54 |
| P23 | Зазор дверь-стена | Расстояние от двери до смежной стены ≥ 100 мм | Обяз. | distance(door.edge, wall) ≥ 100 | Практика |
| P24 | Группировка мокрых зон | Все мокрые зоны смежны друг другу или имеют общую стену (для стояков) | Обяз. | connected_component(wet_zones).size == 1 | СП 54 |
| P25 | Санузел при спальне | Вход в санузел из спальни допускается только при наличии второго санузла с входом из коридора | Обяз. | если door(Bedroom→Bathroom), то exists door(Corridor→Bathroom2) | СП 54 |
| P26 | Мин. ширина гостиной | Ширина общей комнаты (гостиной) ≥ 3200 мм | Рек. | room.width_m ≥ 3.2 для LIVING_ROOM | Практика |
| P27 | Центральное положение гостиной | Гостиная должна быть связующим звеном между входной зоной и остальными помещениями | Рек. | adjacency(hallway, living_room) == True | Практика |
| P28 | Обеденная группа не напротив входа | В гостиной-столовой обеденная группа не ставится напротив входа | Рек. | !faces_door(dining_table, room_entry_door) | Эргономика |

#### Mock-правила (всегда PASS)

Следующие нормативные требования из apartment-planning-rules.md не проверяемы на 2D-плане одного этажа, но включены в реестр как **mock-правила** — заглушки, которые всегда возвращают `RuleResult.PASS`. Это обеспечивает полноту реестра и позволяет в будущем заменить заглушки реальной логикой (например, при расширении на 3D или многоэтажные дома).

| ID | Название | Описание | Тип | Поведение | Причина mock | Нормативная база |
|---|---|---|---|---|---|---|
| P29 | Мин. высота жилых помещений | Высота жилых комнат и кухни ≥ 2500 мм | Mock | always PASS | 3D-параметр; фиксируется константой по классу жилья | СП 54, п.5.8 |
| P30 | Мин. высота коридоров | Высота коридоров и холлов ≥ 2100 мм | Mock | always PASS | 3D-параметр | СП 54, п.5.8 |
| P31 | Санузлы не над жилыми | Санузлы и ванные не располагаются над жилыми комнатами и кухнями нижнего этажа | Mock | always PASS | Многоэтажный контекст; генерируется один этаж | СП 54, п.5.12 |
| P32 | Инсоляция ≥ 2 часа | Непрерывная инсоляция жилых комнат ≥ 2 часов в день | Mock | always PASS | Требует ориентации здания и расчёта теней | СанПиН 2.2.1/2.1.1.1076 |
| P33 | Гидроизоляция мокрых зон | Полы мокрых зон имеют гидроизоляцию | Mock | always PASS | Конструктивное требование, не отражается на плане | СП 29.13330 |
| P34 | Вытяжная вентиляция | Кухня, ванная и туалет оборудованы вытяжной вентиляцией | Mock | always PASS | Инженерное требование; косвенно учитывается через P24 | СП 54, п.5.8 |

**Реализация mock-правил в коде:**

```python
class MockAlwaysPassRule(RuleValidator):
    """Базовый класс для mock-правил, которые всегда возвращают PASS."""

    def validate(self, apartment: Apartment) -> RuleResult:
        return RuleResult(
            rule_id=self.rule_id,
            status=RuleStatus.PASS,
            message=f"{self.name}: mock — всегда PASS (не проверяется на 2D-плане)"
        )
```

### 5.2 Правила расстановки мебели (F01–F29)

| ID | Название | Описание | Тип | Параметры проверки | Источник |
|---|---|---|---|---|---|
| **Санузел** | | | | | |
| F01 | Ось унитаза от стены | Центр унитаза ≥ 350 мм от ближайшей боковой стены | Обяз. | dist(toilet.center_x, wall) ≥ 350 | Эргономика |
| F02 | Зона перед унитазом | Свободное пространство перед унитазом ≥ 600 мм (опт. 750 мм) | Обяз. | clearance_front(toilet) ≥ 600 | Эргономика |
| F03 | Зона перед раковиной | Свободное пространство перед раковиной ≥ 700 мм | Обяз. | clearance_front(sink) ≥ 700 | Эргономика |
| F04 | Зона выхода из ванны | Свободная зона для выхода из ванны ≥ 550 мм | Обяз. | clearance_side(bathtub) ≥ 550 | Эргономика |
| F05 | Розетка от воды | Розетка ≥ 600 мм от края ванны/душа (зона 3 по ГОСТ) | Обяз. | dist(outlet, water_edge) ≥ 600 | ГОСТ Р 50571 |
| **Кухня** | | | | | |
| F06 | Рабочий треугольник | Периметр треугольника мойка-плита-холодильник: 3500–8000 мм (опт. 4000–6000) | Рек. | 3500 ≤ perimeter(triangle) ≤ 8000 | Нойферт |
| F07 | Мойка ↔ плита | Расстояние мойка-плита: 800–2000 мм | Рек. | 800 ≤ dist(sink, stove) ≤ 2000 | Нойферт |
| F08 | Плита — боковая стена | Расстояние от плиты до боковой стены ≥ 200 мм | Обяз. | dist(stove.side, wall) ≥ 200 | Пожаробез. |
| F09 | Плита — окно | Расстояние от плиты до окна ≥ 450 мм | Обяз. | dist(stove, window) ≥ 450 | Пожаробез. |
| F10 | Вытяжка — газовая плита | Расстояние вытяжка-газовая плита ≥ 750 мм (по высоте) | Обяз. | hood.height - stove.height ≥ 750 | СП |
| F11 | Вытяжка — электроплита | Расстояние вытяжка-электроплита ≥ 650 мм (по высоте) | Обяз. | hood.height - stove.height ≥ 650 | СП |
| F12 | Холодильник — плита | Расстояние холодильник-плита ≥ 300 мм | Рек. | dist(fridge, stove) ≥ 300 | Практика |
| F13 | Между рядами кухни | Расстояние между параллельными рядами кухни ≥ 1200 мм | Рек. | passage_width ≥ 1200 | Эргономика |
| **Спальня** | | | | | |
| F14 | Проход вокруг двуспальной кровати | Проход с трёх сторон ≥ 700 мм (опт. 900 мм) | Рек. | clearance(bed, 3_sides) ≥ 700 | Эргономика |
| F15 | Перед распашным шкафом | Свободное пространство перед распашным шкафом ≥ 800 мм | Рек. | clearance_front(wardrobe_swing) ≥ 800 | Эргономика |
| F16 | Перед выдвижными ящиками | Свободное пространство перед ящиками ≥ 800 мм | Рек. | clearance_front(drawers) ≥ 800 | Эргономика |
| **Безопасность** | | | | | |
| F17 | Перед духовым шкафом | Свободное пространство перед духовкой ≥ 800 мм | Обяз. | clearance_front(oven) ≥ 800 | Безопасность |
| F18 | Проход для 1 человека | Минимальный проход между мебелью / мебелью и стеной ≥ 700 мм | Обяз. | min_passage ≥ 700 | Эргономика |
| **Обеденная зона** | | | | | |
| F19 | Стол — стена (проход) | За стулом до стены (проход) ≥ 900 мм | Рек. | clearance(table_chair, wall) ≥ 900 | Эргономика |
| F20 | Макс. высота полки | Верхняя полка ≤ 1900 мм | Рек. | shelf.top ≤ 1900 | Эргономика |
| **Гостиная (из rules.docx)** | | | | | |
| F21 | Собеседники ≤ 2000 мм | Расстояние между диваном и креслами ≤ 2000 мм | Рек. | dist(sofa, armchair) ≤ 2000 | rules.docx |
| F22 | Между креслами / кресло-диван | Расстояние между разнесёнными креслами / кресло-диван ≈ 1050 мм | Рек. | dist(armchair, sofa) ≈ 1050 | rules.docx |
| F23 | Стена — мебель (не по периметру) | Мебель не у стены — расстояние до стены ≥ 900 мм | Рек. | dist(furniture, wall) ≥ 900 | rules.docx |
| F24 | Стена — край ковра | Расстояние от стены до края ковра ≥ 600 мм | Рек. | dist(carpet, wall) ≥ 600 | rules.docx |
| F25 | Шкаф/стеллаж — другая мебель | Между шкафом/стеллажом и другой мебелью ≥ 800 мм | Рек. | dist(shelving, other) ≥ 800 | rules.docx |
| F26 | Загрузка мебелью гостиной ≤ 35% | Площадь мебели / площадь гостиной ≤ 0.35 | Рек. | furniture_area / room.area ≤ 0.35 | rules.docx |
| F27 | ТВ не у окна / не напротив окна | Телевизор не размещается напротив окна и не вблизи окна | Рек. | !faces_window(tv) && dist(tv, window) ≥ 500 | rules.docx |
| F28 | Раскладной диван — спальное место | Длина спального места раскладного дивана ≥ 2000 мм | Рек. | sofa_bed.length ≥ 2000 | rules.docx |
| F29 | Мин. ширина сиденья кресла | Ширина сиденья ≥ 480 мм | Рек. | armchair.seat_width ≥ 480 | rules.docx |
| F30 | Зона разувания у входа | Свободная зона у входной двери ≥ 600 × 800 мм | Рек. | free_rect(entry, 600, 800) exists | Эргономика |
| F31 | Стиральная машина — зазор сзади | Зазор между стиральной машиной и стеной сзади ≥ 50 мм | Обяз. | dist(washer.back, wall) ≥ 50 | Техника |
| F32 | Унитаз — макс. от стояка | Расстояние от унитаза до стояка канализации ≤ 1000 мм | Обяз. | dist(toilet, stoyak) ≤ 1000 | СП |

---

## 6. Формат SVG (на основе plan_example.svg)

### 6.1 Общая структура

Каждый сгенерированный SVG-файл должен воспроизводить структуру эталона:

```xml
<svg version="1.1"
     xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     width="2000px" height="2000px"
     viewBox="0 0 2000 2000">

  <!-- 1. Фон -->
  <path id="background" style="fill:#FFFFFF;" d="..."/>

  <!-- 2. Группы помещений -->
  <g id="{room_id}">
    <path id="{room_id}_path" style="fill:none;" d="..."/>
    <text id="{room_id}_text" transform="matrix(1 0 0 1 {cx} {cy})"
          style="font-family:'GraphikLCG-Regular'; font-size:40px; text-anchor:middle;">
      {Название помещения}
    </text>
  </g>
  <!-- ... повторяется для каждого помещения ... -->

  <!-- 3. Маркеры стояков -->
  <path id="u1" style="fill:#FFFFFF;stroke:#FFFFFF;..." d="..."/>
  <!-- ... -->

  <!-- 4. Мебель — вариант 1 (видимый) -->
  <g id="mebel_1" style="display:inline;">
    <!-- Группы предметов мебели -->
  </g>

  <!-- 5. Мебель — вариант 2 (скрытый) -->
  <g id="mebel_2" style="display:none;">
    <!-- Альтернативная расстановка -->
  </g>

  <!-- 6. Конструктив (стены, двери, окна) -->
  <g id="floor">
    <!-- Стены: <rect> (прямоугольники толщиной стены) -->
    <!-- Двери: <path> (дуга подметания полотна) + <rect> (дверной блок) -->
    <!-- Окна: <rect> (прямоугольник проёма на внешней стене) -->
  </g>
</svg>
```

### 6.2 Именование элементов

| Элемент | Шаблон ID | Примеры |
|---|---|---|
| Помещение (группа) | `{тип}{номер}` | b1, s1, c1, h1, r1, r2, r3 |
| Контур помещения | `{room_id}_path` | b1_path, c1_path |
| Текст помещения | `{room_id}_text` | b1_text, c1_text |
| Стояк | `u{номер}` | u1, u7, u9, u11 |
| Мебель (группа) | `mebel_{вариант}` | mebel_1, mebel_2 |
| Конструктив | `floor` | floor |
| Фон | `background` | background |

Буквенные коды помещений:

| Буква | Тип | Пример |
|---|---|---|
| b | Ванная (bathroom) | b1 |
| s | Спальня (sleep) | s1, s2 |
| c | Гостиная (common) | c1 |
| h | Холл / прихожая (hall) | h1 |
| r | Комната (room) | r1, r2, r3 |
| k | Кухня (kitchen) | k1 |
| t | Туалет (toilet) | t1 |
| w | Гардеробная (wardrobe) | w1 |
| l | Кладовая (locker) | l1 |
| d | Коридор (doorway) | d1 |

### 6.3 Система координат

| Параметр | Значение |
|---|---|
| Холст | 2000 × 2000 px |
| ViewBox | 0 0 2000 2000 |
| Начало координат | Левый верхний угол |
| Ось X | Слева направо |
| Ось Y | Сверху вниз (стандарт SVG) |
| Единицы | Пиксели (px) |
| Масштаб | Определяется при генерации: px_per_mm = canvas_size / apartment_size_mm |

### 6.4 Стили

Все стили — inline (без `<defs>`):

| Элемент | Стиль |
|---|---|
| Фон | fill:#FFFFFF; fill-rule:evenodd; clip-rule:evenodd; |
| Контур помещения | fill:none; |
| Мебель | fill:none; stroke:#000000; stroke-linecap:round; stroke-linejoin:round; stroke-miterlimit:10; |
| Стены | fill:none; stroke:#000000; stroke-linecap:round; stroke-linejoin:round; stroke-miterlimit:10; |
| Двери (дуга) | fill:none; stroke:#000000; stroke-linecap:round; stroke-linejoin:round; stroke-miterlimit:10; |
| Стояки | fill:#FFFFFF; stroke:#FFFFFF; stroke-linecap:round; stroke-linejoin:round; stroke-miterlimit:10; |
| Текст | font-family:'GraphikLCG-Regular'; font-size:40px; text-anchor:middle; |

### 6.5 Кодирование геометрических элементов

**Стены** — прямоугольники `<rect>`:
- Внешние стены: `<rect x y width height/>` с толщиной ≈ 200–250 мм в масштабе
- Внутренние перегородки: толщина ≈ 80–120 мм в масштабе
- Несущие стены: толщина ≈ 200–380 мм

**Двери** — составной элемент:
- Дверной блок: `<rect>` (ширина проёма × толщина стены)
- Дуга подметания: `<path d="M... c..."/>` (четвертьокружность Безье, радиус = ширина полотна)

**Окна** — маркеры на внешней стене:
- `<rect>` малого размера (≈ 11.7 × 14.2 в эталоне) — обозначение створок
- Расположены в ряд на линии внешней стены

**Стояки** — круги:
- `<path>` с Безье-аппроксимацией окружности радиуса ≈ 6 px
- Белая заливка и обводка (#FFFFFF)

**Мебель** — составные группы `<g>`:
- Контур: `<polygon>` или `<rect>`
- Внутренняя детализация: `<path>`, `<line>`, `<circle>`, `<ellipse>`
- Позиционирование: `transform="matrix(a b c d e f)"` — поворот + смещение

---

## 7. Библиотека мебели (furniture_library.json)

Все SVG-сниппеты мебели и оборудования извлекаются из plan_example.svg и сохраняются в структурированный JSON-файл. Формат записи:

```json
{
  "furniture_type": "SOFA_3",
  "category": "living_room",
  "label_ru": "Диван 3-местный",
  "width_mm": 2100,
  "depth_mm": 950,
  "svg_snippet": "<g>...</g>",
  "anchor_point": {"x": 0, "y": 0},
  "clearance_zones": {
    "front": 450,
    "back": 50,
    "left": 0,
    "right": 0
  }
}
```

Для каждого типа мебели фиксируются: тип, размеры в мм, SVG-фрагмент, точка привязки (anchor), зоны доступа (clearance) в мм.

---

## 8. Алгоритм генерации (описание)

### 8.1 Вход

| Параметр CLI | Тип | Обязательный | Описание |
|---|---|---|---|
| --class | ApartmentClass | Да | Класс жилья |
| --rooms | int (1–6) | Да | Количество жилых комнат |
| --count | int | Да | Количество планировок в датасете |
| --output | path | Да | Папка для SVG-файлов |
| --seed | int | Нет | Сид генератора для воспроизводимости |
| --variants | int (1–2) | Нет | Количество вариантов мебели (mebel_1, mebel_2). По умолчанию 1 |

### 8.2 Шаги генерации

**Шаг 1. Определение состава помещений.**
На основе класса жилья и количества комнат определяется набор помещений: типы, количество санузлов, наличие гардеробных, кладовых и т.д. (см. раздел 9 apartment-planning-rules.md).

**Шаг 2. Назначение размеров.**
Каждому помещению назначаются ширина и высота с учётом:
- минимальных площадей (P01–P05)
- минимальных ширин (P06–P10)
- рекомендуемых пропорций (P11)
- диапазонов площадей по классу жилья

**Шаг 3. Размещение комнат на плане (layout).**
Backtracking CSP-солвер размещает прямоугольники комнат на 2D-сетке:
- без взаимных пересечений
- с учётом матрицы смежности (P16)
- с группировкой мокрых зон (P24)
- с разделением дневной/ночной зон (P19)
- с центральным положением гостиной

**Шаг 4. Размещение дверей.**
Между смежными комнатами размещаются двери:
- проверяется матрица допустимости (P16)
- ширина по типу (P20)
- направление открывания (P21)
- зазор до стены (P23)
- отсутствие столкновений полотен (P22)

**Шаг 5. Размещение окон.**
На внешних стенах размещаются окна:
- во всех помещениях, требующих окон (P12, P13)
- с соблюдением минимальной площади остекления (P14)

**Шаг 6. Размещение стояков.**
Стояки водоснабжения и канализации размещаются в мокрых зонах с учётом максимального удаления сантехприборов от стояка.

**Шаг 7. Расстановка мебели.**
Для каждого помещения размещается обязательный набор мебели:
- проверяются все правила F01–F32
- мебель не пересекается между собой
- соблюдаются зоны доступа и проходы

**Шаг 8. Валидация.**
Прогон всех обязательных правил (P01–P28 + F01–F32). Mock-правила P29–P34 также прогоняются (всегда PASS). При нарушении — backtrack к соответствующему шагу.

**Шаг 9. Рендеринг SVG.**
Сборка SVG-файла по шаблону (раздел 6).

### 8.3 Выход

Для каждой планировки генерируется файл `{output}/{class}_{rooms}r_{index:04d}.svg`.

Дополнительно генерируется `{output}/metadata.json` с описанием каждого файла: класс, количество комнат, общая площадь, состав помещений, количество нарушений рекомендательных правил.

---

## 9. CLI-команды

### 9.1 generate — генерация датасета

```
floorplan generate --class comfort --rooms 2 --count 50 --output ./dataset [--seed 42] [--variants 2]
```

Результат: папка с SVG-файлами и metadata.json.

### 9.2 validate — валидация существующего SVG

```
floorplan validate ./plan.svg [--rules all|mandatory|recommended] [--format text|json]
```

Результат: список нарушений с указанием ID правила, описания и серьёзности.

### 9.3 rules — справка по правилам

```
floorplan rules [--list] [--id P01] [--type mandatory|recommended]
```

Результат: таблица правил с ID, описанием, типом и нормативной базой.

### 9.4 extract-furniture — извлечение мебели из SVG

```
floorplan extract-furniture ./plan_example.svg --output ./data/furniture_library.json
```

Результат: JSON-файл библиотеки мебели.

---

## 10. Спецификация тестов (TDD)

### 10.1 Общие принципы

- Подход: **Test-Driven Development** — тесты пишутся до реализации
- Фреймворк: **pytest** с фикстурами в conftest.py
- Покрытие: **≥ 90%** строк кода (pytest-cov)
- Структура: unit / integration / svg
- Именование: `test_{rule_id}_{scenario}` (например `test_P01_living_room_14sqm_pass`)

### 10.2 Фикстуры (conftest.py)

| Фикстура | Описание |
|---|---|
| `make_room(room_type, width, height, **kwargs)` | Создаёт Room с прямоугольной границей |
| `make_apartment(class, rooms_spec)` | Создаёт Apartment с заданным составом |
| `make_door(type, width, swing, from, to)` | Создаёт Door |
| `make_window(width, height)` | Создаёт Window |
| `make_furniture(type, x, y, w, d, rotation)` | Создаёт FurnitureItem |
| `economy_1room()` | Готовая 1-комн. квартира эконом-класса |
| `comfort_2room()` | Готовая 2-комн. квартира комфорт-класса |
| `comfort_3room()` | Готовая 3-комн. квартира комфорт-класса |
| `business_3room()` | Готовая 3-комн. квартира бизнес-класса |

### 10.3 Unit-тесты геометрии (test_geometry.py)

| # | Тест | Описание |
|---|---|---|
| G01 | test_point_distance | Расстояние между двумя точками |
| G02 | test_rectangle_area | Площадь прямоугольника |
| G03 | test_rectangle_aspect_ratio | Соотношение сторон |
| G04 | test_rectangle_contains_point | Точка внутри прямоугольника |
| G05 | test_rectangle_overlap_true | Два пересекающихся прямоугольника |
| G06 | test_rectangle_overlap_false | Два непересекающихся прямоугольника |
| G07 | test_rectangle_overlap_edge | Касание ребром (не пересечение) |
| G08 | test_polygon_area_square | Площадь квадрата как полигона |
| G09 | test_polygon_area_irregular | Площадь неправильного полигона |
| G10 | test_polygon_contains_point_inside | Точка внутри полигона |
| G11 | test_polygon_contains_point_outside | Точка вне полигона |
| G12 | test_polygon_contains_point_edge | Точка на ребре полигона |
| G13 | test_segment_intersection | Пересечение двух отрезков |
| G14 | test_segment_no_intersection | Непересекающиеся отрезки |
| G15 | test_segment_parallel | Параллельные отрезки |
| G16 | test_min_distance_rects | Минимальное расстояние между прямоугольниками |
| G17 | test_polygon_bounding_box | Bounding box полигона |
| G18 | test_polygon_centroid | Центроид полигона |

### 10.4 Unit-тесты моделей (test_models.py)

| # | Тест | Описание |
|---|---|---|
| M01 | test_room_area_calculation | Площадь комнаты в м² вычисляется корректно |
| M02 | test_room_width_calculation | Ширина комнаты (мин. сторона) |
| M03 | test_room_aspect_ratio | Соотношение сторон комнаты |
| M04 | test_room_is_wet_zone | Мокрая зона определяется по типу |
| M05 | test_room_requires_window | Требование окна по типу |
| M06 | test_door_swing_arc | Зона подметания дверного полотна |
| M07 | test_window_area | Площадь окна |
| M08 | test_furniture_bounding_box | Bounding box мебели с учётом поворота |
| M09 | test_furniture_clearance_zone | Зона доступа перед мебелью |
| M10 | test_apartment_total_area | Общая площадь квартиры |
| M11 | test_apartment_living_area | Жилая площадь (только жилые комнаты) |
| M12 | test_apartment_adjacency_graph | Граф смежности из дверей |
| M13 | test_apartment_room_composition | Состав помещений |
| M14 | test_room_free_area_ratio | Доля свободной площади |

### 10.5 Unit-тесты планировочных правил (test_planning_rules.py)

Для каждого правила P01–P25 — минимум по 2 теста (pass + fail), для сложных — 3–5.

| # | Тест | Правило | Сценарий | Ожидание |
|---|---|---|---|---|
| P01a | test_P01_living_room_14sqm_pass | P01 | Гостиная 14 м² в 1-комн. | PASS |
| P01b | test_P01_living_room_13sqm_fail | P01 | Гостиная 13 м² в 1-комн. | FAIL |
| P01c | test_P01_living_room_14sqm_in_2room_not_applied | P01 | Гостиная 14 м² в 2-комн. | N/A (P02 applies) |
| P02a | test_P02_living_room_16sqm_pass | P02 | Гостиная 16 м² в 2-комн. | PASS |
| P02b | test_P02_living_room_15sqm_fail | P02 | Гостиная 15.5 м² в 2-комн. | FAIL |
| P03a | test_P03_bedroom_8sqm_pass | P03 | Спальня 8 м² (1 чел.) | PASS |
| P03b | test_P03_bedroom_7sqm_fail | P03 | Спальня 7.5 м² | FAIL |
| P04a | test_P04_bedroom_10sqm_pass | P04 | Спальня 10 м² (2 чел.) | PASS |
| P04b | test_P04_bedroom_9sqm_fail | P04 | Спальня 9 м² (2 чел.) | FAIL |
| P05a | test_P05_kitchen_8sqm_pass | P05 | Кухня 8 м² | PASS |
| P05b | test_P05_kitchen_7sqm_fail | P05 | Кухня 7 м² в 2-комн. | FAIL |
| P05c | test_P05_kitchen_5sqm_1room_pass | P05 | Кухня 5 м² в 1-комн. | PASS |
| P05d | test_P05_kitchen_4sqm_1room_fail | P05 | Кухня 4 м² в 1-комн. | FAIL |
| P06a | test_P06_kitchen_width_1700_pass | P06 | Кухня шириной 1.7 м | PASS |
| P06b | test_P06_kitchen_width_1600_fail | P06 | Кухня шириной 1.6 м | FAIL |
| P07a | test_P07_corridor_width_850_pass | P07 | Коридор 0.85 м, длина 1.4 м | PASS |
| P07b | test_P07_corridor_width_800_fail | P07 | Коридор 0.8 м | FAIL |
| P07c | test_P07_corridor_long_1000_pass | P07 | Коридор 1.0 м, длина 2.0 м | PASS |
| P07d | test_P07_corridor_long_900_fail | P07 | Коридор 0.9 м, длина 2.0 м | FAIL |
| P08a | test_P08_hallway_1400_pass | P08 | Прихожая 1.4 м | PASS |
| P08b | test_P08_hallway_1300_fail | P08 | Прихожая 1.3 м | FAIL |
| P09a | test_P09_bathroom_1500_pass | P09 | Ванная 1.5 м | PASS |
| P09b | test_P09_bathroom_1400_fail | P09 | Ванная 1.4 м | FAIL |
| P10a | test_P10_combined_bath_1700_pass | P10 | Совм. санузел 1.7 м | PASS |
| P10b | test_P10_combined_bath_1600_fail | P10 | Совм. санузел 1.6 м | FAIL |
| P11a | test_P11_aspect_ratio_1_5_pass | P11 | Комната 4×6 м (1:1.5) | PASS |
| P11b | test_P11_aspect_ratio_2_5_fail | P11 | Комната 3×7.5 м (1:2.5) | FAIL |
| P11c | test_P11_aspect_ratio_2_0_edge | P11 | Комната 3×6 м (1:2.0) | PASS (граница) |
| P12a | test_P12_living_room_has_window_pass | P12 | Гостиная с 1 окном | PASS |
| P12b | test_P12_living_room_no_window_fail | P12 | Гостиная без окон | FAIL |
| P12c | test_P12_corridor_no_window_pass | P12 | Коридор без окон | PASS (не требуется) |
| P13a | test_P13_kitchen_has_window_pass | P13 | Кухня с окном | PASS |
| P13b | test_P13_kitchen_no_window_fail | P13 | Кухня без окон | FAIL |
| P13c | test_P13_kitchen_niche_no_window_pass | P13 | Кухня-ниша без окна (электроплита) | PASS |
| P14a | test_P14_window_area_ratio_pass | P14 | Окно 2.5 м² в комнате 18 м² (1/7.2) | PASS |
| P14b | test_P14_window_area_ratio_fail | P14 | Окно 1.5 м² в комнате 18 м² (1/12) | FAIL |
| P14c | test_P14_multiple_windows_sum | P14 | Два окна по 1.3 м² в комнате 18 м² | PASS |
| P15a | test_P15_toilet_from_corridor_pass | P15 | Туалет из коридора | PASS |
| P15b | test_P15_toilet_from_kitchen_fail | P15 | Туалет из кухни | FAIL |
| P16a | test_P16_hallway_to_corridor_pass | P16 | Прихожая→Коридор (разрешено) | PASS |
| P16b | test_P16_bedroom_to_kitchen_fail | P16 | Спальня→Кухня (запрещено) | FAIL |
| P16c | test_P16_bedroom_to_bathroom_conditional | P16 | Спальня→Ванная (условно) | PASS при наличии 2-го санузла |
| P17a | test_P17_bedroom_not_passthrough_pass | P17 | Спальня с 1 дверью в 2-комн. | PASS |
| P17b | test_P17_bedroom_passthrough_fail | P17 | Спальня с 2 дверьми (проходная) | FAIL |
| P17c | test_P17_living_room_passthrough_ok | P17 | Проходная гостиная | PASS (допустимо) |
| P18a | test_P18_full_composition_pass | P18 | Жилая + кухня + санузел + прихожая | PASS |
| P18b | test_P18_no_kitchen_fail | P18 | Нет кухни | FAIL |
| P18c | test_P18_no_bathroom_fail | P18 | Нет санузла | FAIL |
| P18d | test_P18_no_hallway_fail | P18 | Нет прихожей | FAIL |
| P19a | test_P19_zones_separated_pass | P19 | Дневная и ночная зоны не пересекаются | PASS |
| P19b | test_P19_transit_through_night_fail | P19 | Путь из кухни через спальню | FAIL |
| P20a | test_P20_entrance_door_800_pass | P20 | Входная дверь 860 мм | PASS |
| P20b | test_P20_entrance_door_700_fail | P20 | Входная дверь 700 мм | FAIL |
| P21a | test_P21_bathroom_door_outward_pass | P21 | Дверь санузла наружу | PASS |
| P21b | test_P21_bathroom_door_inward_fail | P21 | Дверь санузла внутрь | FAIL |
| P22a | test_P22_doors_not_collide_pass | P22 | Две двери не сталкиваются | PASS |
| P22b | test_P22_doors_collide_fail | P22 | Дуги подметания пересекаются | FAIL |
| P23a | test_P23_door_wall_gap_100_pass | P23 | 100 мм от двери до стены | PASS |
| P23b | test_P23_door_wall_gap_50_fail | P23 | 50 мм от двери до стены | FAIL |
| P24a | test_P24_wet_zones_grouped_pass | P24 | Ванная и кухня смежны | PASS |
| P24b | test_P24_wet_zones_scattered_fail | P24 | Ванная отделена от кухни жилой комнатой | FAIL |
| P25a | test_P25_ensuite_with_second_bathroom_pass | P25 | Санузел при спальне + гостевой из коридора | PASS |
| P25b | test_P25_ensuite_without_second_fail | P25 | Санузел при спальне, других нет | FAIL |
| P26a | test_P26_living_room_width_3200_pass | P26 | Гостиная шириной 3.2 м | PASS |
| P26b | test_P26_living_room_width_2800_fail | P26 | Гостиная шириной 2.8 м | FAIL |
| P27a | test_P27_living_room_central_pass | P27 | Гостиная смежна с прихожей/холлом | PASS |
| P27b | test_P27_living_room_isolated_fail | P27 | Гостиная не связана с входной зоной | FAIL |
| P28a | test_P28_dining_not_facing_entry_pass | P28 | Стол не напротив входа | PASS |
| P28b | test_P28_dining_facing_entry_fail | P28 | Стол напротив входной двери | FAIL |
| **Mock-правила** | | | | |
| P29a | test_P29_room_height_always_pass | P29 | Любая квартира — mock PASS | PASS |
| P29b | test_P29_room_height_returns_mock_message | P29 | Результат содержит пометку "mock" | PASS + msg |
| P30a | test_P30_corridor_height_always_pass | P30 | Любая квартира — mock PASS | PASS |
| P30b | test_P30_corridor_height_returns_mock_message | P30 | Результат содержит пометку "mock" | PASS + msg |
| P31a | test_P31_sanitary_above_living_always_pass | P31 | Любая квартира — mock PASS | PASS |
| P31b | test_P31_sanitary_above_living_returns_mock_message | P31 | Результат содержит пометку "mock" | PASS + msg |
| P32a | test_P32_insolation_always_pass | P32 | Любая квартира — mock PASS | PASS |
| P32b | test_P32_insolation_returns_mock_message | P32 | Результат содержит пометку "mock" | PASS + msg |
| P33a | test_P33_waterproofing_always_pass | P33 | Любая квартира — mock PASS | PASS |
| P33b | test_P33_waterproofing_returns_mock_message | P33 | Результат содержит пометку "mock" | PASS + msg |
| P34a | test_P34_ventilation_always_pass | P34 | Любая квартира — mock PASS | PASS |
| P34b | test_P34_ventilation_returns_mock_message | P34 | Результат содержит пометку "mock" | PASS + msg |

**Итого планировочных тестов: 73** (61 реальных + 12 mock)

### 10.6 Unit-тесты правил расстановки мебели (test_furniture_rules.py)

| # | Тест | Правило | Сценарий | Ожидание |
|---|---|---|---|---|
| F01a | test_F01_toilet_center_350_from_wall_pass | F01 | Ось унитаза 350 мм от стены | PASS |
| F01b | test_F01_toilet_center_250_from_wall_fail | F01 | Ось унитаза 250 мм от стены | FAIL |
| F02a | test_F02_toilet_front_clearance_600_pass | F02 | 600 мм перед унитазом | PASS |
| F02b | test_F02_toilet_front_clearance_400_fail | F02 | 400 мм перед унитазом | FAIL |
| F03a | test_F03_sink_front_clearance_700_pass | F03 | 700 мм перед раковиной | PASS |
| F03b | test_F03_sink_front_clearance_500_fail | F03 | 500 мм перед раковиной | FAIL |
| F04a | test_F04_bathtub_exit_550_pass | F04 | 550 мм у выхода из ванны | PASS |
| F04b | test_F04_bathtub_exit_400_fail | F04 | 400 мм у выхода из ванны | FAIL |
| F05a | test_F05_outlet_600_from_water_pass | F05 | Розетка 600 мм от ванны | PASS |
| F05b | test_F05_outlet_400_from_water_fail | F05 | Розетка 400 мм от ванны | FAIL |
| F06a | test_F06_triangle_perimeter_5000_pass | F06 | Периметр треугольника 5000 мм | PASS |
| F06b | test_F06_triangle_perimeter_2500_fail | F06 | Периметр 2500 мм (< 3500) | FAIL |
| F06c | test_F06_triangle_perimeter_9000_fail | F06 | Периметр 9000 мм (> 8000) | FAIL |
| F07a | test_F07_sink_stove_1200_pass | F07 | 1200 мм мойка-плита | PASS |
| F07b | test_F07_sink_stove_500_fail | F07 | 500 мм (< 800) | FAIL |
| F07c | test_F07_sink_stove_2500_fail | F07 | 2500 мм (> 2000) | FAIL |
| F08a | test_F08_stove_wall_200_pass | F08 | 200 мм плита-стена | PASS |
| F08b | test_F08_stove_wall_100_fail | F08 | 100 мм плита-стена | FAIL |
| F09a | test_F09_stove_window_450_pass | F09 | 450 мм плита-окно | PASS |
| F09b | test_F09_stove_window_300_fail | F09 | 300 мм плита-окно | FAIL |
| F10a | test_F10_hood_gas_stove_750_pass | F10 | 750 мм вытяжка-газ. плита | PASS |
| F10b | test_F10_hood_gas_stove_600_fail | F10 | 600 мм вытяжка-газ. плита | FAIL |
| F11a | test_F11_hood_electric_stove_650_pass | F11 | 650 мм вытяжка-электро. | PASS |
| F11b | test_F11_hood_electric_stove_500_fail | F11 | 500 мм вытяжка-электро. | FAIL |
| F12a | test_F12_fridge_stove_300_pass | F12 | 300 мм холодильник-плита | PASS |
| F12b | test_F12_fridge_stove_200_fail | F12 | 200 мм холодильник-плита | FAIL |
| F13a | test_F13_kitchen_rows_1200_pass | F13 | 1200 мм между рядами | PASS |
| F13b | test_F13_kitchen_rows_1000_fail | F13 | 1000 мм между рядами | FAIL |
| F14a | test_F14_bed_passage_700_pass | F14 | 700 мм проход у кровати | PASS |
| F14b | test_F14_bed_passage_500_fail | F14 | 500 мм проход у кровати | FAIL |
| F14c | test_F14_single_bed_one_side_ok | F14 | Односпальная у стены (1 сторона) | PASS |
| F15a | test_F15_swing_wardrobe_800_pass | F15 | 800 мм перед распашным шкафом | PASS |
| F15b | test_F15_swing_wardrobe_600_fail | F15 | 600 мм перед распашным шкафом | FAIL |
| F16a | test_F16_drawers_800_pass | F16 | 800 мм перед ящиками | PASS |
| F16b | test_F16_drawers_600_fail | F16 | 600 мм перед ящиками | FAIL |
| F17a | test_F17_oven_clearance_800_pass | F17 | 800 мм перед духовкой | PASS |
| F17b | test_F17_oven_clearance_500_fail | F17 | 500 мм перед духовкой | FAIL |
| F18a | test_F18_passage_700_pass | F18 | 700 мм проход | PASS |
| F18b | test_F18_passage_500_fail | F18 | 500 мм проход | FAIL |
| F18c | test_F18_passage_between_furniture | F18 | 700 мм между двумя предметами | PASS |
| F19a | test_F19_table_wall_passage_900_pass | F19 | 900 мм стол-стена (проход) | PASS |
| F19b | test_F19_table_wall_passage_700_fail | F19 | 700 мм стол-стена (проход) | FAIL |
| F20a | test_F20_shelf_height_1900_pass | F20 | Полка на 1900 мм | PASS |
| F20b | test_F20_shelf_height_2100_fail | F20 | Полка на 2100 мм | FAIL |
| F21a | test_F21_sofa_armchair_1500_pass | F21 | 1500 мм диван-кресло | PASS |
| F21b | test_F21_sofa_armchair_2500_fail | F21 | 2500 мм (> 2000) | FAIL |
| F22a | test_F22_armchairs_apart_1050_pass | F22 | 1050 мм между креслами | PASS |
| F22b | test_F22_armchairs_apart_600_fail | F22 | 600 мм между креслами | FAIL |
| F23a | test_F23_wall_furniture_900_pass | F23 | 900 мм стена-мебель (не по периметру) | PASS |
| F23b | test_F23_wall_furniture_500_fail | F23 | 500 мм стена-мебель | FAIL |
| F24a | test_F24_carpet_wall_600_pass | F24 | 600 мм ковёр-стена | PASS |
| F24b | test_F24_carpet_wall_300_fail | F24 | 300 мм ковёр-стена | FAIL |
| F25a | test_F25_shelving_furniture_800_pass | F25 | 800 мм стеллаж-мебель | PASS |
| F25b | test_F25_shelving_furniture_500_fail | F25 | 500 мм стеллаж-мебель | FAIL |
| F26a | test_F26_living_room_furniture_30pct_pass | F26 | 30% загрузка мебелью | PASS |
| F26b | test_F26_living_room_furniture_50pct_fail | F26 | 50% загрузка мебелью | FAIL |
| F27a | test_F27_tv_not_facing_window_pass | F27 | ТВ не напротив окна | PASS |
| F27b | test_F27_tv_facing_window_fail | F27 | ТВ напротив окна | FAIL |
| F28a | test_F28_sofa_bed_2000_pass | F28 | Раскладной диван 2000 мм | PASS |
| F28b | test_F28_sofa_bed_1800_fail | F28 | Раскладной диван 1800 мм | FAIL |
| F29a | test_F29_armchair_seat_480_pass | F29 | Сиденье кресла 480 мм | PASS |
| F29b | test_F29_armchair_seat_400_fail | F29 | Сиденье кресла 400 мм | FAIL |
| F30a | test_F30_entry_zone_600x800_pass | F30 | Зона 600×800 мм у входа есть | PASS |
| F30b | test_F30_entry_zone_blocked_fail | F30 | Зона у входа заблокирована мебелью | FAIL |
| F31a | test_F31_washer_gap_50_pass | F31 | 50 мм за стиральной машиной | PASS |
| F31b | test_F31_washer_gap_20_fail | F31 | 20 мм за стиральной машиной | FAIL |
| F32a | test_F32_toilet_stoyak_800_pass | F32 | Унитаз 800 мм от стояка | PASS |
| F32b | test_F32_toilet_stoyak_1500_fail | F32 | Унитаз 1500 мм от стояка | FAIL |

**Итого тестов расстановки: 68**

### 10.7 Интеграционные тесты (test_generation.py)

| # | Тест | Описание |
|---|---|---|
| I01 | test_generate_economy_1room | Генерация 1-комн. эконом: валидный SVG, все обязательные правила соблюдены |
| I02 | test_generate_comfort_2room | Генерация 2-комн. комфорт |
| I03 | test_generate_comfort_3room | Генерация 3-комн. комфорт |
| I04 | test_generate_business_3room | Генерация 3-комн. бизнес |
| I05 | test_generate_premium_4room | Генерация 4-комн. премиум |
| I06 | test_generate_batch_10 | Пакетная генерация 10 штук — все уникальны |
| I07 | test_generate_reproducible_seed | Одинаковый seed → идентичный результат |
| I08 | test_generate_different_seeds | Разные seed → разные планировки |
| I09 | test_generate_two_variants | С --variants 2: mebel_1 и mebel_2 присутствуют |
| I10 | test_metadata_json_generated | metadata.json создаётся и содержит корректные данные |

### 10.8 Интеграционные тесты валидации (test_validation.py)

| # | Тест | Описание |
|---|---|---|
| V01 | test_validate_all_mandatory_rules_pass | Все обязательные правила проходят на сгенерированном плане |
| V02 | test_validate_reports_violations | Валидатор находит искусственно внесённые нарушения |
| V03 | test_validate_json_output | JSON-вывод валидации корректен |
| V04 | test_validate_plan_example_svg | Валидация эталонного plan_example.svg |

### 10.9 Тесты SVG (test_svg_output.py)

| # | Тест | Описание |
|---|---|---|
| S01 | test_svg_valid_xml | Сгенерированный SVG — валидный XML |
| S02 | test_svg_viewbox_2000x2000 | viewBox = "0 0 2000 2000" |
| S03 | test_svg_has_background | Элемент id="background" присутствует |
| S04 | test_svg_room_groups_structure | Каждая комната: `<g id="X"><path id="X_path"/><text id="X_text"/></g>` |
| S05 | test_svg_room_ids_unique | Все room ID уникальны |
| S06 | test_svg_mebel_1_present | Группа id="mebel_1" с display:inline |
| S07 | test_svg_mebel_2_hidden | Группа id="mebel_2" с display:none (если --variants 2) |
| S08 | test_svg_floor_group_present | Группа id="floor" присутствует |
| S09 | test_svg_stoyak_markers | Маркеры стояков (u1, u2...) присутствуют в мокрых зонах |
| S10 | test_svg_doors_as_arcs | Двери кодируются дугами (path с Безье) |
| S11 | test_svg_walls_as_rects | Стены кодируются прямоугольниками |
| S12 | test_svg_inline_styles | Все стили inline (без `<defs>`) |
| S13 | test_svg_text_font_and_size | Текст: GraphikLCG-Regular, 40px |
| S14 | test_svg_rooms_no_overlap | Контуры помещений не пересекаются |
| S15 | test_svg_furniture_inside_rooms | Вся мебель внутри своих помещений |

### 10.10 Сводка по тестам

| Категория | Файл | Кол-во тестов |
|---|---|---|
| Геометрия | test_geometry.py | 18 |
| Модели | test_models.py | 14 |
| Планировочные правила | test_planning_rules.py | 73 (61 + 12 mock) |
| Правила расстановки | test_furniture_rules.py | 68 |
| Интеграция (генерация) | test_generation.py | 10 |
| Интеграция (валидация) | test_validation.py | 4 |
| SVG-выход | test_svg_output.py | 15 |
| **ИТОГО** | | **202** |

---

## 11. Порядок реализации (TDD-фазы)

### Фаза 1: Фундамент
1. pyproject.toml + uv init
2. core/enums.py — все перечисления
3. core/geometry.py — геометрические примитивы
4. tests/unit/test_geometry.py — 18 тестов → зелёные
5. core/dimensions.py — все константы
6. core/models.py — Pydantic-модели
7. tests/unit/test_models.py — 14 тестов → зелёные

### Фаза 2: Правила (TDD)
8. tests/unit/test_planning_rules.py — 73 теста (красные): 61 реальный + 12 mock
9. tests/unit/test_furniture_rules.py — 68 тестов (красные)
10. rules/rule_engine.py — базовый класс + MockAlwaysPassRule
11. rules/planning_rules.py — 28 реальных валидаторов + 6 mock-правил → тесты зелёные
12. rules/furniture_rules.py — 32 валидатора → тесты зелёные
13. rules/registry.py — реестр

### Фаза 3: Генератор
14. tests/integration/test_generation.py — 10 тестов (красные)
15. generator/solver.py — CSP-солвер
16. generator/layout_engine.py — размещение комнат
17. generator/furniture_placer.py — расстановка мебели
18. generator/factory.py — фабрика → тесты зелёные

### Фаза 4: SVG-рендеринг
19. Извлечение мебели: plan_example.svg → data/furniture_library.json
20. tests/svg/test_svg_output.py — 15 тестов (красные)
21. rendering/svg_builder.py — сборка SVG
22. rendering/furniture_library.py — библиотека сниппетов
23. rendering/style.py — стили → тесты зелёные

### Фаза 5: CLI + Валидация
24. tests/integration/test_validation.py — 4 теста (красные)
25. cli.py — команды generate, validate, rules, extract-furniture → всё зелёное
26. Покрытие ≥ 90%

---

## 12. Критерии приёмки

| Критерий | Метрика |
|---|---|
| Все unit-тесты проходят | 173/173 green (включая 12 mock) |
| Все интеграционные тесты проходят | 14/14 green |
| Все SVG-тесты проходят | 15/15 green |
| Покрытие кода | ≥ 90% |
| Сгенерированный SVG — валидный XML | 100% файлов |
| Обязательные правила соблюдены | 0 нарушений обязательных правил |
| Уникальность планировок | Нет дубликатов в датасете (при разных seed) |
| Воспроизводимость | Одинаковый seed → идентичный результат |
| Структура SVG | Соответствует plan_example.svg |
| CLI работает | generate, validate, rules, extract-furniture |

---

*Документ основан на: apartment-planning-rules.md, equipment-furniture-rules.md, rules.docx, plan_example.svg и плане проекта.*
