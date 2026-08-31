"""
Colônia Hex - Core Logic Module
Turn-based hex territory strategy game inspired by Antiyoy / Slay.
Pure logic module handling axial hex coordinates, unit fusion,
BFS province discovery, economy/upkeep, starvation collapse,
procedural map generation, and AI bots.
"""

from __future__ import annotations
import math
import random
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Tuple, Optional, Set, Any


# 6 Directions on Axial Coordinate Grid (q, r)
DIRECTIONS: List[Tuple[int, int]] = [
    (1, 0),
    (1, -1),
    (0, -1),
    (-1, 0),
    (-1, 1),
    (0, 1),
]

# Unit Specifications
UNIT_NAMES: Dict[int, str] = {
    1: "Operária",
    2: "Soldado",
    3: "Guardião",
    4: "Elite",
}

UNIT_COSTS: Dict[int, int] = {
    1: 10,
    2: 20,
    3: 30,
    4: 40,
}

UNIT_UPKEEP: Dict[int, int] = {
    1: 2,
    2: 6,
    3: 18,
    4: 54,
}

UNIT_STRENGTH: Dict[int, int] = {
    1: 1,
    2: 2,
    3: 3,
    4: 4,
}

# Building Specifications
BUILDING_COSTS: Dict[str, int] = {
    "castle": 20,
    "farm": 12,
    "tower": 15,
    "strong_tower": 35,
}

BUILDING_UPKEEP: Dict[str, int] = {
    "castle": 0,
    "farm": 0,
    "tower": 1,
    "strong_tower": 6,
}

BUILDING_DEFENSE: Dict[str, int] = {
    "castle": 1,
    "farm": 0,
    "tower": 2,
    "strong_tower": 3,
}

FARM_INCOME = 4
TREE_CHOP_GOLD = 3
MAX_UNIT_LEVEL = 4
STARTING_PROVINCE_GOLD = 10


@dataclass
class HexCell:
    q: int
    r: int
    owner: Optional[int] = None
    unit_level: int = 0
    has_moved: bool = False
    building: Optional[str] = None
    has_tree: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HexCell:
        return cls(**data)


@dataclass
class Province:
    id: str
    owner: int
    cells: List[Tuple[int, int]] = field(default_factory=list)
    gold: int = STARTING_PROVINCE_GOLD
    income: int = 0
    upkeep: int = 0
    castle_pos: Optional[Tuple[int, int]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "owner": self.owner,
            "cells": self.cells,
            "gold": self.gold,
            "income": self.income,
            "upkeep": self.upkeep,
            "castle_pos": self.castle_pos,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Province:
        cells = [tuple(c) for c in data.get("cells", [])]
        castle_pos = tuple(data["castle_pos"]) if data.get("castle_pos") else None
        return cls(
            id=data["id"],
            owner=data["owner"],
            cells=cells,
            gold=data.get("gold", STARTING_PROVINCE_GOLD),
            income=data.get("income", 0),
            upkeep=data.get("upkeep", 0),
            castle_pos=castle_pos,
        )


class HexGame:
    def __init__(
        self,
        map_size: str = "small",
        num_players: int = 2,
        difficulty: str = "medium",
        seed: Optional[int] = None,
        game_id: Optional[str] = None,
    ):
        self.game_id = game_id or str(uuid.uuid4())[:8]
        self.map_size = map_size
        self.num_players = max(2, min(4, num_players))
        self.difficulty = difficulty
        self.seed = seed if seed is not None else random.randint(1, 999999)
        self.rng = random.Random(self.seed)

        self.grid: Dict[Tuple[int, int], HexCell] = {}
        self.provinces: List[Province] = []
        self.current_player: int = 0
        self.turn_number: int = 1
        self.game_over: bool = False
        self.winner: Optional[int] = None
        self.history: List[str] = []

        self.generate_map()
        self.recalculate_provinces()

    # --- Hex Coordinate Mathematics ---

    @staticmethod
    def get_neighbors(q: int, r: int) -> List[Tuple[int, int]]:
        return [(q + dq, r + dr) for dq, dr in DIRECTIONS]

    @staticmethod
    def hex_distance(q1: int, r1: int, q2: int, r2: int) -> int:
        return (abs(q1 - q2) + abs(q1 + r1 - q2 - r2) + abs(r1 - r2)) // 2

    # --- Unit Fusion & Combat Defense Rules ---

    @staticmethod
    def calc_fusion_level(level1: int, level2: int) -> Optional[int]:
        if level1 <= 0 or level2 <= 0:
            return None
        combined = level1 + level2
        if combined <= MAX_UNIT_LEVEL:
            return combined
        return None

    @staticmethod
    def can_conquer(attacker_level: int, target_defense: int) -> bool:
        return attacker_level > target_defense

    def get_cell_defense(self, q: int, r: int) -> int:
        cell = self.grid.get((q, r))
        if not cell or cell.owner is None:
            return 0

        # Unit strength defense on cell
        unit_def = cell.unit_level

        # Structure defense on cell
        building_def = BUILDING_DEFENSE.get(cell.building, 0) if cell.building else 0

        # Tower defense from neighboring allied cells
        tower_def = 0
        for nq, nr in self.get_neighbors(q, r):
            ncell = self.grid.get((nq, nr))
            if ncell and ncell.owner == cell.owner and ncell.building:
                if ncell.building in ("tower", "strong_tower"):
                    bdef = BUILDING_DEFENSE.get(ncell.building, 0)
                    if bdef > tower_def:
                        tower_def = bdef

        return max(unit_def, building_def, tower_def)

    # --- Province & BFS Management ---

    def recalculate_provinces(self) -> None:
        """
        Discovers all contiguous provinces per player using BFS.
        Preserves existing province gold/state where possible or merges/splits cleanly.
        """
        old_provinces_by_owner: Dict[int, List[Province]] = {}
        for p in self.provinces:
            old_provinces_by_owner.setdefault(p.owner, []).append(p)

        new_provinces: List[Province] = []
        visited: Set[Tuple[int, int]] = set()

        for (q, r), cell in self.grid.items():
            if cell.owner is None or (q, r) in visited:
                continue

            owner = cell.owner
            component_cells: List[Tuple[int, int]] = []
            queue = [(q, r)]
            visited.add((q, r))

            while queue:
                curr_q, curr_r = queue.pop(0)
                component_cells.append((curr_q, curr_r))

                for nq, nr in self.get_neighbors(curr_q, curr_r):
                    if (nq, nr) not in visited and (nq, nr) in self.grid:
                        ncell = self.grid[(nq, nr)]
                        if ncell.owner == owner:
                            visited.add((nq, nr))
                            queue.append((nq, nr))

            # Match component with existing province for this owner
            matching_old = []
            cell_set = set(component_cells)
            for old_p in old_provinces_by_owner.get(owner, []):
                overlap = len(cell_set.intersection(set(old_p.cells)))
                if overlap > 0:
                    matching_old.append((overlap, old_p))

            if matching_old:
                matching_old.sort(key=lambda x: x[0], reverse=True)
                primary_old = matching_old[0][1]
                prov_id = primary_old.id
                # Sum gold if multiple provinces merged
                total_gold = sum(p.gold for _, p in matching_old)
            else:
                prov_id = f"prov_{owner}_{uuid.uuid4().hex[:6]}"
                total_gold = STARTING_PROVINCE_GOLD

            # Determine castle position
            castle_pos = None
            for cq, cr in component_cells:
                ccell = self.grid[(cq, cr)]
                if ccell.building == "castle":
                    castle_pos = (cq, cr)
                    break

            if not castle_pos and component_cells:
                # If component has a cell with no building, make it castle, else use first
                free_cells = [c for c in component_cells if self.grid[c].building is None]
                castle_pos = free_cells[0] if free_cells else component_cells[0]
                if self.grid[castle_pos].building is None:
                    self.grid[castle_pos].building = "castle"

            # Compute gross income and upkeep
            farms = sum(1 for cq, cr in component_cells if self.grid[(cq, cr)].building == "farm")
            gross_income = len(component_cells) + (FARM_INCOME * farms)

            upkeep = 0
            for cq, cr in component_cells:
                ccell = self.grid[(cq, cr)]
                if ccell.unit_level > 0:
                    upkeep += UNIT_UPKEEP.get(ccell.unit_level, 0)
                if ccell.building:
                    upkeep += BUILDING_UPKEEP.get(ccell.building, 0)

            net_income = gross_income - upkeep

            province = Province(
                id=prov_id,
                owner=owner,
                cells=component_cells,
                gold=total_gold,
                income=net_income,
                upkeep=upkeep,
                castle_pos=castle_pos,
            )
            new_provinces.append(province)

        self.provinces = new_provinces

    def get_province_by_id(self, prov_id: str) -> Optional[Province]:
        for p in self.provinces:
            if p.id == prov_id:
                return p
        return None

    def get_province_for_cell(self, q: int, r: int) -> Optional[Province]:
        for p in self.provinces:
            if (q, r) in p.cells:
                return p
        return None

    # --- Map Generation ---

    def generate_map(self) -> None:
        radius_map = {"small": 4, "medium": 6, "large": 8}
        radius = radius_map.get(self.map_size, 4)

        # Generate axial hex circle
        all_hexes: List[Tuple[int, int]] = []
        for q in range(-radius, radius + 1):
            r1 = max(-radius, -q - radius)
            r2 = min(radius, -q + radius)
            for r in range(r1, r2 + 1):
                # Filter outer edge corners for organic shape
                dist = self.hex_distance(0, 0, q, r)
                if dist == radius and self.rng.random() < 0.25:
                    continue
                all_hexes.append((q, r))

        for q, r in all_hexes:
            has_tree = self.rng.random() < 0.18
            self.grid[(q, r)] = HexCell(q=q, r=r, owner=None, has_tree=has_tree)

        # Player spawn positions spaced out radially
        angle_step = (2 * math.pi) / self.num_players
        spawn_dist = max(1, radius - 1)

        player_spawns: List[Tuple[int, int]] = []
        for i in range(self.num_players):
            angle = i * angle_step + (math.pi / 6)
            approx_q = int(round(spawn_dist * math.cos(angle)))
            approx_r = int(round(spawn_dist * math.sin(angle)))

            best_hex = min(
                all_hexes,
                key=lambda h: self.hex_distance(h[0], h[1], approx_q, approx_r),
            )
            player_spawns.append(best_hex)

        # Claim starting territory for each player (capital + 2-3 neighbor cells)
        for player_idx, (sq, sr) in enumerate(player_spawns):
            # Set Capital
            self.grid[(sq, sr)].owner = player_idx
            self.grid[(sq, sr)].building = "castle"
            self.grid[(sq, sr)].has_tree = False
            self.grid[(sq, sr)].unit_level = 0

            # Expand starting territory to 2-3 adjacent neighbors
            neighbors = [
                n for n in self.get_neighbors(sq, sr)
                if n in self.grid and self.grid[n].owner is None
            ]
            self.rng.shuffle(neighbors)
            starting_territory = neighbors[:3]

            for idx, npos in enumerate(starting_territory):
                self.grid[npos].owner = player_idx
                self.grid[npos].has_tree = False
                # Give 1 starting Worker on the first neighbor cell
                if idx == 0:
                    self.grid[npos].unit_level = 1
                    self.grid[npos].has_moved = False

    # --- Gameplay Actions ---

    def recruit(self, province_id: str, q: int, r: int, level: int = 1) -> Dict[str, Any]:
        if self.game_over:
            return {"success": False, "reason": "Game is already over"}

        if level not in UNIT_COSTS:
            return {"success": False, "reason": f"Invalid unit level {level}"}

        province = self.get_province_by_id(province_id)
        if not province:
            return {"success": False, "reason": f"Province {province_id} not found"}

        if province.owner != self.current_player:
            return {"success": False, "reason": "Province does not belong to current player"}

        cost = UNIT_COSTS[level]
        if province.gold < cost:
            return {"success": False, "reason": f"Not enough gold: need {cost}, have {province.gold}"}

        target_cell = self.grid.get((q, r))
        if not target_cell:
            return {"success": False, "reason": "Target cell does not exist"}

        # Check if cell is inside province
        if (q, r) in province.cells:
            if target_cell.unit_level == 0:
                province.gold -= cost
                target_cell.unit_level = level
                target_cell.has_moved = False
                if target_cell.has_tree:
                    target_cell.has_tree = False
                    province.gold += TREE_CHOP_GOLD
                self.recalculate_provinces()
                return {"success": True, "message": f"{UNIT_NAMES[level]} recrutada com sucesso."}
            else:
                # Field fusion inside friendly territory
                fused = self.calc_fusion_level(target_cell.unit_level, level)
                if fused is None:
                    return {"success": False, "reason": "Fusão excede o nível máximo 4."}
                province.gold -= cost
                target_cell.unit_level = fused
                target_cell.has_moved = False
                self.recalculate_provinces()
                return {"success": True, "message": f"Unidades fundidas em {UNIT_NAMES[fused]} (Nível {fused})."}

        # Target cell is outside province -> must be adjacent to at least one province cell
        is_adjacent = any(
            (nq, nr) in province.cells
            for nq, nr in self.get_neighbors(q, r)
        )
        if not is_adjacent:
            return {"success": False, "reason": "Recrutamento deve ser no território ou adjacente à fronteira."}

        target_def = self.get_cell_defense(q, r)
        if not self.can_conquer(level, target_def):
            return {
                "success": False,
                "reason": f"Força de ataque ({level}) não supera a defesa do alvo ({target_def}).",
            }

        # Conquering recruitment
        province.gold -= cost
        if target_cell.has_tree:
            target_cell.has_tree = False
            province.gold += TREE_CHOP_GOLD

        target_cell.owner = province.owner
        target_cell.unit_level = level
        target_cell.has_moved = True
        target_cell.building = None  # Destroy any enemy building

        self.recalculate_provinces()
        self.check_game_over()
        return {"success": True, "message": f"Território conquistado com {UNIT_NAMES[level]}!"}

    def move(self, from_q: int, from_r: int, to_q: int, to_r: int) -> Dict[str, Any]:
        if self.game_over:
            return {"success": False, "reason": "Game is already over"}

        if (from_q, from_r) == (to_q, to_r):
            return {"success": False, "reason": "Origem e destino são iguais"}

        from_cell = self.grid.get((from_q, from_r))
        to_cell = self.grid.get((to_q, to_r))

        if not from_cell or not to_cell:
            return {"success": False, "reason": "Célula de origem ou destino inexistente"}

        if from_cell.owner != self.current_player:
            return {"success": False, "reason": "Unidade não pertence ao jogador atual"}

        if from_cell.unit_level <= 0:
            return {"success": False, "reason": "Nenhuma unidade na célula de origem"}

        if from_cell.has_moved:
            return {"success": False, "reason": "Unidade já se moveu neste turno"}

        from_prov = self.get_province_for_cell(from_q, from_r)
        if not from_prov:
            return {"success": False, "reason": "Província de origem não encontrada"}

        # Case 1: Destination is friendly (inside same province)
        if (to_q, to_r) in from_prov.cells:
            if to_cell.unit_level == 0:
                if to_cell.has_tree:
                    to_cell.has_tree = False
                    from_prov.gold += TREE_CHOP_GOLD
                to_cell.unit_level = from_cell.unit_level
                to_cell.has_moved = True
                from_cell.unit_level = 0
                self.recalculate_provinces()
                return {"success": True, "message": "Unidade movimentada."}
            else:
                # In-field fusion
                fused = self.calc_fusion_level(from_cell.unit_level, to_cell.unit_level)
                if fused is None:
                    return {"success": False, "reason": "Fusão excede o nível máximo 4."}
                to_cell.unit_level = fused
                to_cell.has_moved = True
                from_cell.unit_level = 0
                self.recalculate_provinces()
                return {"success": True, "message": f"Unidades fundidas em {UNIT_NAMES[fused]} (Nível {fused})."}

        # Case 2: Destination is outside province -> must be adjacent to province territory
        is_adjacent = any(
            (nq, nr) in from_prov.cells
            for nq, nr in self.get_neighbors(to_q, to_r)
        )
        if not is_adjacent:
            return {"success": False, "reason": "Destino fora do território deve ser adjacente à província."}

        target_def = self.get_cell_defense(to_q, to_r)
        if not self.can_conquer(from_cell.unit_level, target_def):
            return {
                "success": False,
                "reason": f"Força ({from_cell.unit_level}) não supera a defesa do alvo ({target_def}).",
            }

        # Conquering move
        if to_cell.has_tree:
            to_cell.has_tree = False
            from_prov.gold += TREE_CHOP_GOLD

        to_cell.owner = self.current_player
        to_cell.unit_level = from_cell.unit_level
        to_cell.has_moved = True
        to_cell.building = None  # Destroy enemy building
        from_cell.unit_level = 0

        self.recalculate_provinces()
        self.check_game_over()
        return {"success": True, "message": "Hexágono conquistado com sucesso!"}

    def build(self, province_id: str, q: int, r: int, building: str) -> Dict[str, Any]:
        if self.game_over:
            return {"success": False, "reason": "Game is already over"}

        if building not in BUILDING_COSTS:
            return {"success": False, "reason": f"Estrutura inválida: {building}"}

        province = self.get_province_by_id(province_id)
        if not province:
            return {"success": False, "reason": f"Província {province_id} não encontrada"}

        if province.owner != self.current_player:
            return {"success": False, "reason": "Província não pertence ao jogador atual"}

        cell = self.grid.get((q, r))
        if not cell or (q, r) not in province.cells:
            return {"success": False, "reason": "Célula deve pertencer à província selecionada"}

        cost = BUILDING_COSTS[building]
        # Tower upgrade to strong tower discount
        if cell.building == "tower" and building == "strong_tower":
            cost = BUILDING_COSTS["strong_tower"] - BUILDING_COSTS["tower"]
        elif cell.building is not None and cell.building != building:
            return {"success": False, "reason": f"Célula já possui {cell.building}"}
        elif cell.building == building:
            return {"success": False, "reason": f"Célula já possui {building}"}

        if province.gold < cost:
            return {"success": False, "reason": f"Ouro insuficiente: necessário {cost}, possui {province.gold}"}

        province.gold -= cost
        cell.building = building
        if cell.has_tree:
            cell.has_tree = False

        self.recalculate_provinces()
        return {"success": True, "message": f"{building.capitalize()} construído com sucesso."}

    def end_turn(self) -> Dict[str, Any]:
        if self.game_over:
            return {"success": False, "reason": "Game is already over"}

        # 1. Update economy for current player's provinces
        curr_provinces = [p for p in self.provinces if p.owner == self.current_player]
        for prov in curr_provinces:
            farms = sum(1 for c in prov.cells if self.grid.get(c) and self.grid[c].building == "farm")
            gross_income = len(prov.cells) + (FARM_INCOME * farms)

            upkeep = 0
            for c in prov.cells:
                cell = self.grid.get(c)
                if cell:
                    if cell.unit_level > 0:
                        upkeep += UNIT_UPKEEP.get(cell.unit_level, 0)
                    if cell.building:
                        upkeep += BUILDING_UPKEEP.get(cell.building, 0)

            net_income = gross_income - upkeep
            new_gold = prov.gold + net_income

            if new_gold < 0:
                # Starvation / Bankruptcy
                for c in prov.cells:
                    cell = self.grid.get(c)
                    if cell and cell.unit_level > 0:
                        cell.unit_level = 0
                        cell.has_tree = True  # Tombstone / overgrown tree
                prov.gold = 0
                self.history.append(f"Província do Jogador {self.current_player} faliu! Tropas pereceram de fome.")
            else:
                prov.gold = new_gold

        # 2. Reset has_moved on all units
        for cell in self.grid.values():
            cell.has_moved = False

        # 3. Advance to next active player
        attempts = 0
        while attempts < self.num_players:
            self.current_player = (self.current_player + 1) % self.num_players
            if self.current_player == 0:
                self.turn_number += 1

            self.recalculate_provinces()
            self.check_game_over()
            if self.game_over:
                break

            # Check if this player is alive (has at least 1 cell)
            has_cells = any(c.owner == self.current_player for c in self.grid.values())
            if has_cells:
                break
            attempts += 1

        # 4. If next player is an AI bot (player > 0), run AI turn automatically
        if not self.game_over and self.current_player > 0:
            self.run_ai_turn(self.current_player, self.difficulty)
            # Recalculate and end turn for bot to continue chain
            return self.end_turn()

        return {
            "success": True,
            "turn_number": self.turn_number,
            "current_player": self.current_player,
            "game_over": self.game_over,
            "winner": self.winner,
        }

    def check_game_over(self) -> None:
        active_owners = {cell.owner for cell in self.grid.values() if cell.owner is not None}
        if len(active_owners) == 1:
            self.game_over = True
            self.winner = list(active_owners)[0]
        elif len(active_owners) == 0:
            self.game_over = True
            self.winner = None

    # --- AI Bot Logic ---

    def run_ai_turn(self, player_id: int, difficulty: str = "medium") -> None:
        if self.game_over:
            return

        provinces = [p for p in self.provinces if p.owner == player_id]
        for prov in provinces:
            if difficulty == "easy":
                self._run_easy_ai(prov)
            elif difficulty == "hard":
                self._run_hard_ai(prov)
            else:
                self._run_medium_ai(prov)

    def _run_easy_ai(self, prov: Province) -> None:
        # Move idle units to adjacent trees or neutral cells
        for q, r in list(prov.cells):
            cell = self.grid.get((q, r))
            if cell and cell.unit_level > 0 and not cell.has_moved:
                neighbors = self.get_neighbors(q, r)
                # Prioritize chopping trees
                tree_targets = [n for n in neighbors if n in self.grid and self.grid[n].has_tree and self.grid[n].owner is None]
                if tree_targets:
                    tq, tr = tree_targets[0]
                    self.move(q, r, tq, tr)
                    continue

                # Expand to neutral cells
                neutral_targets = [n for n in neighbors if n in self.grid and self.grid[n].owner is None]
                if neutral_targets:
                    tq, tr = neutral_targets[0]
                    self.move(q, r, tq, tr)

        # Recruit worker if gold >= 10
        if prov.gold >= 10:
            for q, r in prov.cells:
                if prov.gold < 10:
                    break
                neighbors = self.get_neighbors(q, r)
                for nq, nr in neighbors:
                    if (nq, nr) in self.grid and self.grid[(nq, nr)].owner is None:
                        res = self.recruit(prov.id, nq, nr, level=1)
                        if res.get("success"):
                            break

    def _run_medium_ai(self, prov: Province) -> None:
        # 1. Move units: attack enemy or expand, merge if needed
        for q, r in list(prov.cells):
            cell = self.grid.get((q, r))
            if not cell or cell.unit_level <= 0 or cell.has_moved:
                continue

            neighbors = self.get_neighbors(q, r)
            # Look for conquerable enemy cells
            enemy_targets = [
                n for n in neighbors
                if n in self.grid and self.grid[n].owner is not None and self.grid[n].owner != prov.owner
                and self.can_conquer(cell.unit_level, self.get_cell_defense(n[0], n[1]))
            ]
            if enemy_targets:
                self.move(q, r, enemy_targets[0][0], enemy_targets[0][1])
                continue

            # Neutral targets or tree chopping
            neutral_targets = [
                n for n in neighbors
                if n in self.grid and self.grid[n].owner is None
                and self.can_conquer(cell.unit_level, self.get_cell_defense(n[0], n[1]))
            ]
            if neutral_targets:
                self.move(q, r, neutral_targets[0][0], neutral_targets[0][1])
                continue

            # In-field fusion if adjacent to enemy defense
            if cell.unit_level < 3:
                allied_units = [
                    n for n in neighbors
                    if n in self.grid and self.grid[n].owner == prov.owner
                    and 0 < self.grid[n].unit_level <= (4 - cell.unit_level)
                ]
                if allied_units:
                    self.move(q, r, allied_units[0][0], allied_units[0][1])

        # 2. Economy & Building
        # Build farm if economy is safe (gold >= 15 and positive income buffer)
        if prov.gold >= 15 and prov.income >= 2:
            safe_cells = [
                c for c in prov.cells
                if self.grid[c].building is None
                and all(
                    n in self.grid and self.grid[n].owner == prov.owner
                    for n in self.get_neighbors(c[0], c[1])
                )
            ]
            if safe_cells:
                self.build(prov.id, safe_cells[0][0], safe_cells[0][1], "farm")

        # Build tower on border if threatened
        if prov.gold >= 25:
            border_cells = [
                c for c in prov.cells
                if self.grid[c].building is None
                and any(
                    n in self.grid and self.grid[n].owner is not None and self.grid[n].owner != prov.owner
                    for n in self.get_neighbors(c[0], c[1])
                )
            ]
            if border_cells:
                self.build(prov.id, border_cells[0][0], border_cells[0][1], "tower")

        # 3. Recruitment: recruit workers or soldiers without risking starvation
        if prov.gold >= 20 and prov.income > 4:
            # Recruit Soldier (level 2) on border
            for c in prov.cells:
                for nq, nr in self.get_neighbors(c[0], c[1]):
                    if (nq, nr) in self.grid and self.grid[(nq, nr)].owner is not None and self.grid[(nq, nr)].owner != prov.owner:
                        if self.can_conquer(2, self.get_cell_defense(nq, nr)):
                            self.recruit(prov.id, nq, nr, level=2)
                            break
        elif prov.gold >= 10 and prov.income >= 0:
            for c in prov.cells:
                for nq, nr in self.get_neighbors(c[0], c[1]):
                    if (nq, nr) in self.grid and self.grid[(nq, nr)].owner is None:
                        self.recruit(prov.id, nq, nr, level=1)
                        break

    def _run_hard_ai(self, prov: Province) -> None:
        # Hard AI: High strategic value targeting (capitals, farms, cutting moves)
        for q, r in list(prov.cells):
            cell = self.grid.get((q, r))
            if not cell or cell.unit_level <= 0 or cell.has_moved:
                continue

            neighbors = self.get_neighbors(q, r)
            # Prioritize high-value targets (Castle > Farm > Tower > Neutral)
            high_val_targets = []
            for nq, nr in neighbors:
                ncell = self.grid.get((nq, nr))
                if ncell and ncell.owner is not None and ncell.owner != prov.owner:
                    ndef = self.get_cell_defense(nq, nr)
                    if self.can_conquer(cell.unit_level, ndef):
                        score = 1
                        if ncell.building == "castle":
                            score = 10
                        elif ncell.building == "farm":
                            score = 7
                        elif ncell.building == "tower":
                            score = 5
                        high_val_targets.append((score, nq, nr))

            if high_val_targets:
                high_val_targets.sort(key=lambda x: x[0], reverse=True)
                _, tq, tr = high_val_targets[0]
                self.move(q, r, tq, tr)
                continue

            # Neutral expansion
            neutral_targets = [
                n for n in neighbors
                if n in self.grid and self.grid[n].owner is None
                and self.can_conquer(cell.unit_level, self.get_cell_defense(n[0], n[1]))
            ]
            if neutral_targets:
                self.move(q, r, neutral_targets[0][0], neutral_targets[0][1])

        # Aggressive recruitment with level 2 or 3 if gold is abundant
        if prov.gold >= 30 and prov.income > 5:
            # Try recruiting Guardian (level 3)
            for c in prov.cells:
                for nq, nr in self.get_neighbors(c[0], c[1]):
                    if (nq, nr) in self.grid and self.grid[(nq, nr)].owner is not None and self.grid[(nq, nr)].owner != prov.owner:
                        if self.can_conquer(3, self.get_cell_defense(nq, nr)):
                            self.recruit(prov.id, nq, nr, level=3)
                            break

        # Economy investments
        if prov.gold >= 12:
            safe_cells = [
                c for c in prov.cells
                if self.grid[c].building is None
                and all(
                    n in self.grid and self.grid[n].owner == prov.owner
                    for n in self.get_neighbors(c[0], c[1])
                )
            ]
            if safe_cells:
                self.build(prov.id, safe_cells[0][0], safe_cells[0][1], "farm")

    # --- Serialization ---

    def to_dict(self) -> Dict[str, Any]:
        grid_data = {f"{q},{r}": cell.to_dict() for (q, r), cell in self.grid.items()}
        return {
            "game_id": self.game_id,
            "map_size": self.map_size,
            "num_players": self.num_players,
            "difficulty": self.difficulty,
            "seed": self.seed,
            "turn_number": self.turn_number,
            "current_player": self.current_player,
            "game_over": self.game_over,
            "winner": self.winner,
            "history": self.history,
            "provinces": [p.to_dict() for p in self.provinces],
            "grid": grid_data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HexGame:
        game = cls(
            map_size=data.get("map_size", "small"),
            num_players=data.get("num_players", 2),
            difficulty=data.get("difficulty", "medium"),
            seed=data.get("seed", 42),
            game_id=data.get("game_id"),
        )
        game.turn_number = data.get("turn_number", 1)
        game.current_player = data.get("current_player", 0)
        game.game_over = data.get("game_over", False)
        game.winner = data.get("winner")
        game.history = data.get("history", [])

        # Restore Grid
        game.grid = {}
        for key, cell_data in data.get("grid", {}).items():
            q_str, r_str = key.split(",")
            q, r = int(q_str), int(r_str)
            game.grid[(q, r)] = HexCell.from_dict(cell_data)

        # Restore Provinces
        game.provinces = [Province.from_dict(p_data) for p_data in data.get("provinces", [])]
        return game
