from typing import Dict, Set, FrozenSet, List, Tuple, Any

all_waypoints: list[list[str]] = list()

waypoint_distances: Dict[FrozenSet[str], float] = {}
waypoint_durations: Dict[FrozenSet[str], float] = {}
all_waypoints_set: Set[list[str]] = set()  # Fix: not sure about the type
