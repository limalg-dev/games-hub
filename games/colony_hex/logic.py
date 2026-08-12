from typing import List, Dict, Any, Tuple, Optional
from games.colony_hex.mapgen import generate_map, NEST_COORDS

def get_distance(q1: int, r1: int, q2: int, r2: int) -> int:
    return (abs(q1 - q2) + abs(q1 + r1 - q2 - r2) + abs(r1 - r2)) // 2

class GameState:
    def __init__(self, game_id: str, players_setup: List[Dict[str, Any]]):
        self.game_id = game_id
        self.status = "lobby"
        self.turn_number = 1
        self.turn_index = 0
        self.actions_left = 2
        self.winner = None
        self.ranking = None
        
        self.players = []
        for i, p in enumerate(players_setup):
            self.players.append({
                "color": p["color"],
                "leaves": 10,
                "alive": True,
                "is_ai": p["is_ai"],
                "nest": NEST_COORDS[i]
            })
            
        self.map = generate_map(len(players_setup))
        # Nests owned by default
        for i, p in enumerate(self.players):
            nq, nr = p["nest"]
            for cell in self.map:
                if cell["q"] == nq and cell["r"] == nr:
                    cell["owner"] = p["color"]
                    
        # Initial units: 1 worker on each alive player nest
        self.units = []
        for i, p in enumerate(self.players):
            self.units.append({
                "id": f"u_{p['color']}_0",
                "owner": p["color"],
                "type": "worker",
                "q": p["nest"][0],
                "r": p["nest"][1]
            })
        self.next_unit_id = 1

    def start_game(self) -> Tuple[bool, Optional[str]]:
        if len(self.players) < 2:
            return False, "Requer pelo menos 2 jogadores"
        if self.status != "lobby":
            return False, "O jogo já foi iniciado"
        self.status = "active"
        
        # Give initial income to the first player
        active_player = self.players[self.turn_index]
        owned_count = sum(1 for c in self.map if c["owner"] == active_player["color"])
        active_player["leaves"] += owned_count
        
        return True, None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.game_id,
            "status": self.status,
            "map": self.map,
            "units": self.units,
            "players": self.players,
            "turn_index": self.turn_index,
            "turn_number": self.turn_number,
            "actions_left": self.actions_left,
            "winner": self.winner,
            "ranking": self.ranking
        }

    def execute_action(self, color: str, action: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        if self.status != "active":
            return False, "O jogo não está ativo"
        active_player = self.players[self.turn_index]
        if active_player["color"] != color:
            return False, "Não é a sua vez"
        if self.actions_left <= 0:
            return False, "Sem ações restantes"

        kind = action.get("kind")
        if kind == "end_turn":
            self.actions_left = 0
            self._next_turn()
            return True, None

        if kind == "expand":
            q, r = action.get("q"), action.get("r")
            if q is None or r is None:
                return False, "Coordenadas ausentes"
            cell = next((c for c in self.map if c["q"] == q and c["r"] == r), None)
            if not cell or cell["terrain"] == "rock" or cell["owner"] is not None:
                return False, "Célula inválida ou já ocupada"
            # Adjacency check
            adjacent = False
            for c in self.map:
                if c["owner"] == color and get_distance(q, r, c["q"], c["r"]) == 1:
                    adjacent = True
                    break
            if not adjacent:
                return False, "Célula não é adjacente ao seu território"
            # Unit block check
            if any(u["q"] == q and u["r"] == r for u in self.units):
                return False, "Célula contém uma unidade"
            if active_player["leaves"] < 3:
                return False, "Folhas insuficientes (custa 3)"
            active_player["leaves"] -= 3
            cell["owner"] = color
            self.actions_left -= 1
            if self.actions_left <= 0:
                self._next_turn()
            return True, None

        if kind == "recruit":
            u_type = action.get("unit_type")
            if u_type not in ("worker", "soldier"):
                return False, "Tipo de unidade inválido"
            cost = 2 if u_type == "worker" else 5
            if active_player["leaves"] < cost:
                return False, "Folhas insuficientes"
            nq, nr = active_player["nest"]
            # Nest occupied
            if any(u["q"] == nq and u["r"] == nr for u in self.units):
                return False, "Ninho ocupado"
            active_player["leaves"] -= cost
            self.units.append({
                "id": f"u_{color}_{self.next_unit_id}",
                "owner": color,
                "type": u_type,
                "q": nq,
                "r": nr
            })
            self.next_unit_id += 1
            self.actions_left -= 1
            if self.actions_left <= 0:
                self._next_turn()
            return True, None

        if kind == "move":
            u_id = action.get("unit_id")
            to_q, to_r = action.get("to_q"), action.get("to_r")
            unit = next((u for u in self.units if u["id"] == u_id and u["owner"] == color), None)
            if not unit:
                return False, "Unidade não encontrada ou não é sua"
            if get_distance(unit["q"], unit["r"], to_q, to_r) != 1:
                return False, "Destino não é adjacente"
            target_cell = next((c for c in self.map if c["q"] == to_q and c["r"] == to_r), None)
            if not target_cell or target_cell["terrain"] == "rock":
                return False, "Destino inválido (obstáculo)"
            # Target empty or owned by me
            if target_cell["owner"] is not None and target_cell["owner"] != color:
                return False, "Destino pertence ao oponente"
            if any(u["q"] == to_q and u["r"] == to_r for u in self.units):
                return False, "Destino ocupado por outra unidade"
            unit["q"] = to_q
            unit["r"] = to_r
            self.actions_left -= 1
            if self.actions_left <= 0:
                self._next_turn()
            return True, None

        if kind == "attack":
            u_id = action.get("unit_id")
            to_q, to_r = action.get("to_q"), action.get("to_r")
            unit = next((u for u in self.units if u["id"] == u_id and u["owner"] == color), None)
            if not unit or unit["type"] != "soldier":
                return False, "Apenas soldados podem atacar"
            if get_distance(unit["q"], unit["r"], to_q, to_r) != 1:
                return False, "Alvo não é adjacente"
            target_cell = next((c for c in self.map if c["q"] == to_q and c["r"] == to_r), None)
            if not target_cell or target_cell["terrain"] == "rock":
                return False, "Alvo inválido"
            
            # Resolve attack
            enemy_unit = next((u for u in self.units if u["q"] == to_q and u["r"] == to_r), None)
            if enemy_unit:
                if enemy_unit["owner"] == color:
                    return False, "Não pode atacar sua própria unidade"
                # Combat resolution: Soldier wins, attacker always wins soldier vs soldier
                self.units.remove(enemy_unit)
                unit["q"] = to_q
                unit["r"] = to_r
                target_cell["owner"] = color
            elif target_cell["owner"] is not None and target_cell["owner"] != color:
                # Capture empty territory
                unit["q"] = to_q
                unit["r"] = to_r
                target_cell["owner"] = color
            else:
                return False, "Nenhum alvo de ataque válido na célula"

            # Check nest capture (elimination)
            for p in self.players:
                if p["alive"] and p["nest"] == (to_q, to_r) and p["color"] != color:
                    p["alive"] = False
                    # Remove all their units
                    self.units = [u for u in self.units if u["owner"] != p["color"]]
                    # Neutralize other hexes
                    for c in self.map:
                        if c["owner"] == p["color"]:
                            c["owner"] = None
            
            self._check_victory()
            self.actions_left -= 1
            if self.actions_left <= 0:
                self._next_turn()
            return True, None

        return False, "Ação desconhecida"

    def _next_turn(self):
        # Find next alive player
        attempts = 0
        while attempts < len(self.players):
            self.turn_index = (self.turn_index + 1) % len(self.players)
            if self.turn_index == 0:
                self.turn_number += 1
            if self.players[self.turn_index]["alive"]:
                break
            attempts += 1
            
        if not self._check_victory():
            self.actions_left = 2
            # Add income
            active_player = self.players[self.turn_index]
            owned_count = sum(1 for c in self.map if c["owner"] == active_player["color"])
            active_player["leaves"] += owned_count

    def _check_victory(self) -> bool:
        alive_players = [p for p in self.players if p["alive"]]
        if len(alive_players) <= 1:
            self.status = "finished"
            self.winner = alive_players[0]["color"] if alive_players else None
            self._calculate_ranking()
            return True
        if self.turn_number > 20:
            self.status = "finished"
            self._calculate_ranking()
            self.winner = self.ranking[0]["color"] if self.ranking else None
            return True
        return False

    def _calculate_ranking(self):
        ranked = []
        for i, p in enumerate(self.players):
            owned = sum(1 for c in self.map if c["owner"] == p["color"])
            score = (owned * 10) + p["leaves"] if p["alive"] else 0
            soldiers = sum(1 for u in self.units if u["owner"] == p["color"] and u["type"] == "soldier")
            workers = sum(1 for u in self.units if u["owner"] == p["color"] and u["type"] == "worker")
            ranked.append({
                "color": p["color"],
                "score": score,
                "alive": p["alive"],
                "soldiers": soldiers,
                "workers": workers,
                "seat_index": i
            })
        # Sort desc: alive first, then score desc, soldiers desc, workers desc, seat_index asc
        ranked.sort(key=lambda x: (
            0 if x["alive"] else 1,
            -x["score"],
            -x["soldiers"],
            -x["workers"],
            x["seat_index"]
        ))
        self.ranking = ranked

    def run_ai_turn(self):
        # Fast greedy AI logic
        ai_color = self.players[self.turn_index]["color"]
        while self.actions_left > 0 and self.status == "active" and self.players[self.turn_index]["color"] == ai_color:
            ai_player = self.players[self.turn_index]
            # 1. Attack adjacent enemy if possible
            attack_made = False
            for u in self.units:
                if u["owner"] == ai_color and u["type"] == "soldier":
                    for c in self.map:
                        if get_distance(u["q"], u["r"], c["q"], c["r"]) == 1:
                            target_unit = next((tu for tu in self.units if tu["q"] == c["q"] and tu["r"] == c["r"]), None)
                            if (target_unit and target_unit["owner"] != ai_color) or (c["owner"] is not None and c["owner"] != ai_color):
                                success, _ = self.execute_action(ai_color, {"kind": "attack", "unit_id": u["id"], "to_q": c["q"], "to_r": c["r"]})
                                if success:
                                    attack_made = True
                                    break
                    if attack_made:
                         break
            if attack_made:
                continue

            # 2. Expand if leaves >= 3
            expand_made = False
            if ai_player["leaves"] >= 3:
                for c in self.map:
                    if c["owner"] is None and c["terrain"] != "rock":
                        # adjacent to mine?
                        for owned in self.map:
                            if owned["owner"] == ai_color and get_distance(c["q"], c["r"], owned["q"], owned["r"]) == 1:
                                success, _ = self.execute_action(ai_color, {"kind": "expand", "q": c["q"], "r": c["r"]})
                                if success:
                                    expand_made = True
                                    break
                        if expand_made:
                            break
            if expand_made:
                continue

            # 3. Recruit
            rec_made = False
            nq, nr = ai_player["nest"]
            nest_free = not any(u["q"] == nq and u["r"] == nr for u in self.units)
            if nest_free:
                # Check for adjacent threat to nest
                has_threat = False
                for u in self.units:
                    if u["owner"] != ai_color and get_distance(nq, nr, u["q"], u["r"]) == 1:
                        has_threat = True
                        break
                
                if has_threat and ai_player["leaves"] >= 5:
                    success, _ = self.execute_action(ai_color, {"kind": "recruit", "unit_type": "soldier"})
                    if success: rec_made = True
                elif ai_player["leaves"] >= 2:
                    success, _ = self.execute_action(ai_color, {"kind": "recruit", "unit_type": "worker"})
                    if success: rec_made = True
            if rec_made:
                continue

            # 4. Move soldier toward nearest enemy border
            move_made = False
            for u in self.units:
                if u["owner"] == ai_color and u["type"] == "soldier":
                    # Find all enemy targets (cells owned by enemy or containing enemy units)
                    targets = []
                    for c in self.map:
                        if c["owner"] is not None and c["owner"] != ai_color:
                            targets.append((c["q"], c["r"]))
                    for tu in self.units:
                        if tu["owner"] != ai_color:
                            targets.append((tu["q"], tu["r"]))
                    
                    if not targets:
                        continue
                    
                    best_target = min(targets, key=lambda t: get_distance(u["q"], u["r"], t[0], t[1]))
                    current_dist = get_distance(u["q"], u["r"], best_target[0], best_target[1])
                    
                    possible_moves = []
                    for c in self.map:
                        if get_distance(u["q"], u["r"], c["q"], c["r"]) == 1:
                            if c["terrain"] != "rock" and (c["owner"] is None or c["owner"] == ai_color):
                                if not any(tu["q"] == c["q"] and tu["r"] == c["r"] for tu in self.units):
                                    dist_to_target = get_distance(c["q"], c["r"], best_target[0], best_target[1])
                                    possible_moves.append((dist_to_target, c["q"], c["r"]))
                    
                    if possible_moves:
                        possible_moves.sort()
                        best_move_dist, to_q, to_r = possible_moves[0]
                        if best_move_dist < current_dist:
                            success, _ = self.execute_action(ai_color, {
                                "kind": "move",
                                "unit_id": u["id"],
                                "to_q": to_q,
                                "to_r": to_r
                            })
                            if success:
                                move_made = True
                                break
            if move_made:
                continue

            # 5. End turn
            self.execute_action(ai_color, {"kind": "end_turn"})
