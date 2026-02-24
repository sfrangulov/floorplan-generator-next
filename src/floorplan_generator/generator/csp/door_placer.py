"""Door placement on shared walls using spanning tree selection."""

from __future__ import annotations

import heapq
import random
import uuid
from collections import defaultdict

from floorplan_generator.core.dimensions import ADJACENCY_MATRIX, DOOR_SIZES
from floorplan_generator.core.enums import DoorType, RoomType, SwingDirection
from floorplan_generator.core.geometry import Point, Rectangle, Segment
from floorplan_generator.core.models import Door, Room
from floorplan_generator.generator.types import SharedWall
from floorplan_generator.rules.geometry_helpers import wall_segments

_BATHROOM_TYPES = frozenset({
    RoomType.BATHROOM,
    RoomType.TOILET,
    RoomType.COMBINED_BATHROOM,
})

# Forbidden direct connections
_FORBIDDEN_PAIRS = frozenset({
    (RoomType.KITCHEN, RoomType.TOILET),
    (RoomType.TOILET, RoomType.KITCHEN),
})

# Room type classifications for spanning tree
_HUB_TYPES = frozenset({RoomType.HALLWAY, RoomType.CORRIDOR, RoomType.HALL})

_SINGLE_DOOR_TYPES = frozenset({
    RoomType.STORAGE, RoomType.WARDROBE, RoomType.BATHROOM,
    RoomType.TOILET, RoomType.COMBINED_BATHROOM, RoomType.LAUNDRY,
})

_LIVING_AREA_TYPES = frozenset({
    RoomType.LIVING_ROOM, RoomType.BEDROOM, RoomType.CHILDREN, RoomType.CABINET,
})


def _determine_door_type(type_a: RoomType, type_b: RoomType) -> DoorType:
    """Determine door type based on connected rooms."""
    if type_a in _BATHROOM_TYPES:
        return DoorType.BATHROOM
    if type_b in _BATHROOM_TYPES:
        return DoorType.BATHROOM
    if RoomType.KITCHEN in (type_a, type_b):
        return DoorType.KITCHEN
    return DoorType.INTERIOR


def _door_swing(type_from: RoomType, type_to: RoomType) -> SwingDirection:
    """Determine swing direction. Bathroom doors swing outward."""
    if type_to in _BATHROOM_TYPES:
        return SwingDirection.OUTWARD
    return SwingDirection.INWARD


def _is_adjacency_allowed(type_a: RoomType, type_b: RoomType) -> bool:
    """Check if a door connection between two room types is allowed."""
    if (type_a, type_b) in _FORBIDDEN_PAIRS:
        return False
    if type_a in ADJACENCY_MATRIX and type_b in ADJACENCY_MATRIX.get(type_a, {}):
        return ADJACENCY_MATRIX[type_a][type_b] != "-"
    if type_b in ADJACENCY_MATRIX and type_a in ADJACENCY_MATRIX.get(type_b, {}):
        return ADJACENCY_MATRIX[type_b][type_a] != "-"
    return True


def _min_wall_for_door(type_a: RoomType, type_b: RoomType) -> float:
    """Minimum wall length needed to place a door between two room types."""
    door_type = _determine_door_type(type_a, type_b)
    door_width = DOOR_SIZES[door_type][0]
    return door_width + 200  # door + 100mm gap on each side


def _build_adjacency_graph(
    shared_walls: list[SharedWall],
    room_map: dict[str, Room],
) -> dict[str, list[tuple[str, SharedWall]]]:
    """Build adjacency graph from shared walls.

    Filters forbidden adjacencies and walls that are too short for a door.
    Keeps the longest wall per room pair.
    """
    best_walls: dict[tuple[str, str], SharedWall] = {}

    for sw in shared_walls:
        room_a = room_map.get(sw.room_a_id)
        room_b = room_map.get(sw.room_b_id)
        if room_a is None or room_b is None:
            continue
        if not _is_adjacency_allowed(room_a.room_type, room_b.room_type):
            continue
        # Pre-filter: wall must be long enough for a door
        min_len = _min_wall_for_door(room_a.room_type, room_b.room_type)
        if sw.segment.length < min_len:
            continue

        key = (min(sw.room_a_id, sw.room_b_id), max(sw.room_a_id, sw.room_b_id))
        if key not in best_walls or sw.segment.length > best_walls[key].segment.length:
            best_walls[key] = sw

    graph: dict[str, list[tuple[str, SharedWall]]] = defaultdict(list)
    for (a_id, b_id), sw in best_walls.items():
        graph[a_id].append((b_id, sw))
        graph[b_id].append((a_id, sw))
    return dict(graph)


def _find_root(rooms: list[Room]) -> str:
    """Find the root room (hallway preferred) for spanning tree."""
    for r in rooms:
        if r.room_type == RoomType.HALLWAY:
            return r.id
    for r in rooms:
        if r.room_type in (RoomType.CORRIDOR, RoomType.HALL):
            return r.id
    return rooms[0].id


def _edge_weight(
    from_id: str,
    to_id: str,
    room_map: dict[str, Room],
    sw: SharedWall,
) -> float:
    """Compute edge weight for spanning tree (lower = preferred)."""
    from_type = room_map[from_id].room_type
    to_type = room_map[to_id].room_type

    weight = 0.0

    # Strongly prefer hub rooms as parent
    if from_type in _HUB_TYPES:
        weight -= 1000.0

    # Prefer hub-to-hub connections (hallway-corridor link)
    if from_type in _HUB_TYPES and to_type in _HUB_TYPES:
        weight -= 500.0

    # Prefer living room connected to hallway (P27)
    if from_type == RoomType.HALLWAY and to_type == RoomType.LIVING_ROOM:
        weight -= 200.0

    # Penalize kitchen connecting to living areas (P37 risk)
    if from_type == RoomType.KITCHEN and to_type in _LIVING_AREA_TYPES:
        weight += 100.0
    if to_type == RoomType.KITCHEN and from_type in _LIVING_AREA_TYPES:
        weight += 100.0

    # Prefer longer walls (easier to place doors)
    weight -= sw.segment.length * 0.1

    return weight


# Rooms that must have exactly 1 door — never used as transit nodes.
# Bedrooms are NOT included: they prefer 1 door via edge weights,
# but CAN be transit if layout requires it (P17 catches violations).
_DEAD_END_TYPES = _SINGLE_DOOR_TYPES


def _count_living_connections(
    room_id: str,
    tree_edges: list[tuple[str, str, SharedWall]],
    room_map: dict[str, Room],
) -> int:
    """Count how many living areas a room connects to in the tree."""
    count = 0
    for from_id, to_id, _ in tree_edges:
        if from_id == room_id and room_map[to_id].room_type in _LIVING_AREA_TYPES:
            count += 1
        elif to_id == room_id and room_map[from_id].room_type in _LIVING_AREA_TYPES:
            count += 1
    return count


def _can_accept_edge(
    from_id: str,
    to_id: str,
    room_map: dict[str, Room],
    door_count: dict[str, int],
    tree_edges: list[tuple[str, str, SharedWall]],
) -> bool:
    """Check if edge (from_id → to_id) satisfies all constraints."""
    from_type = room_map[from_id].room_type
    to_type = room_map[to_id].room_type

    # Single-door rooms: max 1 edge total
    if to_type in _SINGLE_DOOR_TYPES and door_count[to_id] >= 1:
        return False
    if from_type in _SINGLE_DOOR_TYPES and door_count[from_id] >= 1:
        return False

    # Dead-end rooms (bedrooms): don't use as transit (max 1 edge)
    if from_type in _DEAD_END_TYPES and door_count[from_id] >= 1:
        return False
    if to_type in _DEAD_END_TYPES and door_count[to_id] >= 1:
        return False

    # P37: kitchen max 1 living-area connection
    if to_type == RoomType.KITCHEN and from_type in _LIVING_AREA_TYPES:
        if _count_living_connections(to_id, tree_edges, room_map) >= 1:
            return False
    if from_type == RoomType.KITCHEN and to_type in _LIVING_AREA_TYPES:
        if _count_living_connections(from_id, tree_edges, room_map) >= 1:
            return False

    return True


def _seed_heap(
    heap: list,
    counter: list[int],
    node_id: str,
    graph: dict[str, list[tuple[str, SharedWall]]],
    room_map: dict[str, Room],
    visited: set[str],
    rng: random.Random,
) -> None:
    """Add all neighbors of node_id to the heap."""
    for neighbor_id, sw in graph.get(node_id, []):
        if neighbor_id not in visited:
            w = _edge_weight(node_id, neighbor_id, room_map, sw)
            w += rng.random() * 0.01
            heapq.heappush(heap, (w, counter[0], node_id, neighbor_id, sw))
            counter[0] += 1


def _build_spanning_tree(
    graph: dict[str, list[tuple[str, SharedWall]]],
    room_map: dict[str, Room],
    root_id: str,
    rng: random.Random,
) -> list[tuple[str, str, SharedWall]]:
    """Build spanning tree via Prim's with constraints and component bridging.

    Handles disconnected components by finding bridge edges when the
    main heap is exhausted but unvisited rooms remain.
    """
    tree_edges: list[tuple[str, str, SharedWall]] = []
    visited: set[str] = {root_id}
    door_count: dict[str, int] = defaultdict(int)
    all_ids = set(room_map.keys())

    heap: list[tuple[float, int, str, str, SharedWall]] = []
    counter = [0]  # mutable for _seed_heap

    _seed_heap(heap, counter, root_id, graph, room_map, visited, rng)

    while visited != all_ids:
        # Process heap (Prim's expansion)
        while heap:
            _weight, _, from_id, to_id, sw = heapq.heappop(heap)

            if to_id in visited:
                continue

            if not _can_accept_edge(
                from_id, to_id, room_map, door_count, tree_edges,
            ):
                continue

            # Accept edge
            tree_edges.append((from_id, to_id, sw))
            visited.add(to_id)
            door_count[from_id] += 1
            door_count[to_id] += 1

            _seed_heap(heap, counter, to_id, graph, room_map, visited, rng)

        # Heap exhausted — check for disconnected components
        unvisited = all_ids - visited
        if not unvisited:
            break

        # Find best bridge from any unvisited room to any visited room
        best_bridge = None
        best_weight = float("inf")

        for room_id in unvisited:
            for neighbor_id, sw in graph.get(room_id, []):
                if neighbor_id not in visited:
                    continue
                if not _can_accept_edge(
                    neighbor_id, room_id, room_map, door_count, tree_edges,
                ):
                    continue
                w = _edge_weight(neighbor_id, room_id, room_map, sw)
                if w < best_weight:
                    best_weight = w
                    best_bridge = (neighbor_id, room_id, sw)

        if best_bridge is None:
            break  # Truly disconnected — no valid bridge

        # Add bridge edge and continue Prim's from the new node
        from_id, to_id, sw = best_bridge
        tree_edges.append(best_bridge)
        visited.add(to_id)
        door_count[from_id] += 1
        door_count[to_id] += 1

        _seed_heap(heap, counter, to_id, graph, room_map, visited, rng)

    return tree_edges


def _try_place_door_on_wall(
    sw: SharedWall,
    room_a: Room,
    room_b: Room,
    placed_arcs: list[Rectangle],
    rng: random.Random,
) -> dict | None:
    """Attempt to place a door on a shared wall. Returns door dict or None."""
    door_type = _determine_door_type(room_a.room_type, room_b.room_type)
    door_width = DOOR_SIZES[door_type][0]
    swing = _door_swing(room_a.room_type, room_b.room_type)

    wall = sw.segment
    if wall.length < door_width + 200:
        return None

    is_vertical = abs(wall.start.x - wall.end.x) < 1

    wall_start = (
        min(wall.start.y, wall.end.y)
        if is_vertical
        else min(wall.start.x, wall.end.x)
    )
    wall_end = (
        max(wall.start.y, wall.end.y)
        if is_vertical
        else max(wall.start.x, wall.end.x)
    )

    step = 50.0
    min_pos = wall_start + 100
    max_pos = wall_end - door_width - 100

    if min_pos > max_pos:
        return None

    positions: list[float] = []
    pos = min_pos
    while pos <= max_pos:
        positions.append(pos)
        pos += step
    rng.shuffle(positions)

    for pos in positions:
        if is_vertical:
            door_pos = Point(x=wall.start.x, y=pos)
            arc = Rectangle(
                x=(
                    door_pos.x - door_width
                    if swing == SwingDirection.OUTWARD
                    else door_pos.x
                ),
                y=door_pos.y,
                width=door_width,
                height=door_width,
            )
        else:
            door_pos = Point(x=pos, y=wall.start.y)
            arc = Rectangle(
                x=door_pos.x,
                y=(
                    door_pos.y - door_width
                    if swing == SwingDirection.OUTWARD
                    else door_pos.y
                ),
                width=door_width,
                height=door_width,
            )

        if any(arc.overlaps(a) for a in placed_arcs):
            continue

        orientation = "vertical" if is_vertical else "horizontal"
        door = Door(
            id=uuid.uuid4().hex[:8],
            position=door_pos,
            width=door_width,
            door_type=door_type,
            swing=swing,
            room_from=sw.room_a_id,
            room_to=sw.room_b_id,
            wall_orientation=orientation,
        )

        return {
            "door": door,
            "shared_wall": wall,
            "room_a_id": sw.room_a_id,
            "room_b_id": sw.room_b_id,
        }

    return None


def place_doors(
    rooms: list[Room],
    shared_walls: list[SharedWall],
    rng: random.Random,
) -> list[dict]:
    """Place doors on shared walls using spanning tree selection.

    Builds a spanning tree from the hallway to ensure all rooms are reachable
    with minimum doors, respecting architectural constraints (P17, P35, P37).

    Returns list of {"door": Door, "shared_wall": Segment, "room_a_id", "room_b_id"}.
    """
    if not rooms or not shared_walls:
        return []

    room_map = {r.id: r for r in rooms}

    # Phase 1: Build adjacency graph (filter forbidden, deduplicate)
    graph = _build_adjacency_graph(shared_walls, room_map)

    # Phase 2: Find root (hallway)
    root_id = _find_root(rooms)

    # Phase 3: Build spanning tree (handles disconnected components)
    tree_edges = _build_spanning_tree(graph, room_map, root_id, rng)

    # Phase 4: Place physical doors on selected tree edges
    placed_doors: list[dict] = []
    placed_arcs: list[Rectangle] = []
    connected: set[str] = set()

    for from_id, to_id, sw in tree_edges:
        room_a = room_map[from_id]
        room_b = room_map[to_id]
        result = _try_place_door_on_wall(sw, room_a, room_b, placed_arcs, rng)
        if result is not None:
            placed_doors.append(result)
            placed_arcs.append(result["door"].swing_arc)
            connected.add(from_id)
            connected.add(to_id)

    # Phase 5: Fallback — try alternative edges for rooms without doors
    #          Respects single-door/dead-end constraints.
    all_ids = set(room_map.keys())
    doorless = all_ids - connected
    if doorless:
        # Count doors per room from placed doors
        fb_door_count: dict[str, int] = defaultdict(int)
        for dr in placed_doors:
            fb_door_count[dr["room_a_id"]] += 1
            fb_door_count[dr["room_b_id"]] += 1

        for sw in shared_walls:
            if not doorless:
                break
            room_a = room_map.get(sw.room_a_id)
            room_b = room_map.get(sw.room_b_id)
            if room_a is None or room_b is None:
                continue
            # One side doorless, other connected
            if not ({sw.room_a_id, sw.room_b_id} & doorless):
                continue
            if not ({sw.room_a_id, sw.room_b_id} & connected):
                continue
            if not _is_adjacency_allowed(room_a.room_type, room_b.room_type):
                continue
            # Enforce single-door/dead-end constraints
            a_type = room_a.room_type
            b_type = room_b.room_type
            if a_type in _DEAD_END_TYPES and fb_door_count[sw.room_a_id] >= 1:
                continue
            if b_type in _DEAD_END_TYPES and fb_door_count[sw.room_b_id] >= 1:
                continue

            result = _try_place_door_on_wall(sw, room_a, room_b, placed_arcs, rng)
            if result is not None:
                placed_doors.append(result)
                placed_arcs.append(result["door"].swing_arc)
                connected.add(sw.room_a_id)
                connected.add(sw.room_b_id)
                fb_door_count[sw.room_a_id] += 1
                fb_door_count[sw.room_b_id] += 1
                doorless = all_ids - connected

    return placed_doors


def place_entrance_door(
    rooms: list[Room],
    canvas: Rectangle,
    rng: random.Random,
    existing_arcs: list[Rectangle] | None = None,
) -> Door | None:
    """Place entrance door on an external wall of the hallway."""
    hallway = next(
        (r for r in rooms if r.room_type == RoomType.HALLWAY), None,
    )
    if hallway is None:
        return None

    door_width = DOOR_SIZES[DoorType.ENTRANCE][0]
    eps = 250.0
    arcs = existing_arcs or []

    # Find external wall segments of the hallway
    ext_walls: list[Segment] = []
    for seg in wall_segments(hallway):
        if seg.length < door_width + 200:
            continue
        is_vert = abs(seg.start.x - seg.end.x) < 1
        is_horiz = abs(seg.start.y - seg.end.y) < 1
        if is_vert:
            x = seg.start.x
            if abs(x - canvas.x) < eps or abs(x - (canvas.x + canvas.width)) < eps:
                ext_walls.append(seg)
        elif is_horiz:
            y = seg.start.y
            if abs(y - canvas.y) < eps or abs(y - (canvas.y + canvas.height)) < eps:
                ext_walls.append(seg)

    if not ext_walls:
        return None

    # Sort walls by length (prefer longest), try each
    ext_walls.sort(key=lambda s: s.length, reverse=True)

    for wall in ext_walls:
        is_vertical = abs(wall.start.x - wall.end.x) < 1
        wall_start = (
            min(wall.start.y, wall.end.y) if is_vertical
            else min(wall.start.x, wall.end.x)
        )
        wall_end = (
            max(wall.start.y, wall.end.y) if is_vertical
            else max(wall.start.x, wall.end.x)
        )

        # Try positions with 50mm step
        min_pos = wall_start + 100
        max_pos = wall_end - door_width - 100
        if min_pos > max_pos:
            continue

        positions = []
        p = min_pos
        while p <= max_pos:
            positions.append(p)
            p += 50.0
        # Prefer center
        mid = (min_pos + max_pos) / 2
        positions.sort(key=lambda v: abs(v - mid))

        for pos in positions:
            if is_vertical:
                door_pos = Point(x=wall.start.x, y=pos)
                arc = Rectangle(
                    x=door_pos.x, y=door_pos.y,
                    width=door_width, height=door_width,
                )
            else:
                door_pos = Point(x=pos, y=wall.start.y)
                arc = Rectangle(
                    x=door_pos.x, y=door_pos.y,
                    width=door_width, height=door_width,
                )

            if any(arc.overlaps(a) for a in arcs):
                continue

            orientation = "vertical" if is_vertical else "horizontal"
            return Door(
                id=uuid.uuid4().hex[:8],
                position=door_pos,
                width=door_width,
                door_type=DoorType.ENTRANCE,
                swing=SwingDirection.INWARD,
                room_from=hallway.id,
                room_to=hallway.id,
                wall_orientation=orientation,
            )

    return None
