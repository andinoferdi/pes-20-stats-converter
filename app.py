import csv
import glob
import json
import math
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

DIRECT_STATS = [
    "offensive_awareness",
    "finishing",
    "ball_control",
    "dribbling",
    "tight_possession",
    "low_pass",
    "lofted_pass",
    "heading",
    "place_kicking",
    "curl",
    "defensive_awareness",
    "aggression",
    "speed",
    "acceleration",
    "kicking_power",
    "jump",
    "balance",
    "stamina",
]

SPECIAL_STATS = [
    "physical_contact",
    "ball_winning",
    "gk_awareness",
    "gk_catching",
    "gk_clearing",
    "gk_reflexes",
    "gk_reach",
]

PES_OUTPUT_ORDER = [
    "offensive_awareness",
    "finishing",
    "kicking_power",
    "weak_foot_usage",
    "weak_foot_accuracy",
    "ball_control",
    "dribbling",
    "tight_possession",
    "balance",
    "low_pass",
    "lofted_pass",
    "place_kicking",
    "curl",
    "heading",
    "jump",
    "defensive_awareness",
    "ball_winning",
    "aggression",
    "speed",
    "acceleration",
    "physical_contact",
    "stamina",
    "form",
    "injury_resistance",
    "gk_awareness",
    "gk_catching",
    "gk_clearing",
    "gk_reflexes",
    "gk_reach",
]

EF_REQUIRED_STATS = [
    "offensive_awareness",
    "ball_control",
    "dribbling",
    "tight_possession",
    "low_pass",
    "lofted_pass",
    "finishing",
    "heading",
    "place_kicking",
    "curl",
    "defensive_awareness",
    "defensive_engagement",
    "tackling",
    "aggression",
    "goalkeeping",
    "gk_catching",
    "gk_parrying",
    "gk_reflexes",
    "gk_reach",
    "speed",
    "acceleration",
    "kicking_power",
    "jump",
    "physical",
    "balance",
    "stamina",
]

FAMILY_DELTA_PROFILES = {
    "ATTACKER": {
        "offensive_awareness": -0.09,
        "finishing": -0.09,
        "ball_control": 9.09,
        "dribbling": 6.73,
        "tight_possession": 8.09,
        "low_pass": 11.45,
        "lofted_pass": 12.82,
        "heading": 11.18,
        "place_kicking": 5.55,
        "curl": 0.27,
        "defensive_awareness": 12.0,
        "aggression": 15.82,
        "speed": 0.64,
        "acceleration": -4.09,
        "kicking_power": 1.36,
        "jump": 11.0,
        "balance": -0.82,
        "stamina": 3.27,
        "physical_contact": 5.12,
        "ball_winning": 10.42,
        "gk_awareness": -10.36,
        "gk_catching": -21.76,
        "gk_clearing": -24.99,
        "gk_reflexes": -18.79,
        "gk_reach": -3.16,
        "weak_foot_usage": 2.55,
        "weak_foot_accuracy": 2.91,
        "form": 6.36,
        "injury_resistance": 1.45,
    },
    "DEFENDER": {
        "offensive_awareness": 5.5,
        "finishing": 13.5,
        "ball_control": 12.5,
        "dribbling": 12.0,
        "tight_possession": 16.5,
        "low_pass": 8.0,
        "lofted_pass": 8.5,
        "heading": 4.0,
        "place_kicking": 19.5,
        "curl": 11.0,
        "defensive_awareness": -3.5,
        "aggression": -3.0,
        "speed": -1.5,
        "acceleration": -2.0,
        "kicking_power": 5.5,
        "jump": 1.0,
        "balance": 1.5,
        "stamina": 2.0,
        "physical_contact": -1.6,
        "ball_winning": -3.83,
        "gk_awareness": -16.35,
        "gk_catching": -20.93,
        "gk_clearing": -29.75,
        "gk_reflexes": -17.92,
        "gk_reach": -3.0,
        "weak_foot_usage": 1.5,
        "weak_foot_accuracy": 2.0,
        "form": 7.5,
        "injury_resistance": 3.0,
    },
    "GOALKEEPER": {
        "offensive_awareness": 10.0,
        "finishing": 8.0,
        "ball_control": 17.0,
        "dribbling": 4.0,
        "tight_possession": -3.0,
        "low_pass": -3.0,
        "lofted_pass": 4.0,
        "heading": 17.0,
        "place_kicking": 5.0,
        "curl": 1.0,
        "defensive_awareness": 10.0,
        "aggression": -9.0,
        "speed": 7.0,
        "acceleration": 3.0,
        "kicking_power": 14.0,
        "jump": 14.0,
        "balance": 16.0,
        "stamina": 10.0,
        "physical_contact": 32.88,
        "ball_winning": -2.65,
        "gk_awareness": 1.15,
        "gk_catching": -0.25,
        "gk_clearing": 1.05,
        "gk_reflexes": -0.05,
        "gk_reach": 0.3,
        "weak_foot_usage": 2.0,
        "weak_foot_accuracy": 3.0,
        "form": 7.0,
        "injury_resistance": 2.0,
    },
    "WIDE": {
        "offensive_awareness": 1.83,
        "finishing": 2.75,
        "ball_control": 0.92,
        "dribbling": 0.08,
        "tight_possession": 1.75,
        "low_pass": 6.67,
        "lofted_pass": 7.67,
        "heading": 13.33,
        "place_kicking": 6.83,
        "curl": 3.42,
        "defensive_awareness": 10.33,
        "aggression": 16.83,
        "speed": 1.25,
        "acceleration": 0.25,
        "kicking_power": -1.42,
        "jump": 14.17,
        "balance": 3.42,
        "stamina": 5.25,
        "physical_contact": 3.3,
        "ball_winning": 10.01,
        "gk_awareness": -10.11,
        "gk_catching": -22.28,
        "gk_clearing": -26.29,
        "gk_reflexes": -19.27,
        "gk_reach": -3.0,
        "weak_foot_usage": 2.0,
        "weak_foot_accuracy": 2.92,
        "form": 6.33,
        "injury_resistance": 1.92,
    },
    "MIDFIELDER": {
        "offensive_awareness": 7.5,
        "finishing": 9.0,
        "ball_control": 6.0,
        "dribbling": 2.5,
        "tight_possession": 6.5,
        "low_pass": 10.5,
        "lofted_pass": 9.5,
        "heading": 9.0,
        "place_kicking": 7.0,
        "curl": 5.5,
        "defensive_awareness": 13.0,
        "aggression": 10.5,
        "speed": -2.0,
        "acceleration": 1.0,
        "kicking_power": 3.0,
        "jump": 10.0,
        "balance": 10.0,
        "stamina": 6.0,
        "physical_contact": 7.5,
        "ball_winning": 11.0,
        "gk_awareness": -10.5,
        "gk_catching": -22.0,
        "gk_clearing": -26.0,
        "gk_reflexes": -19.0,
        "gk_reach": -3.0,
        "weak_foot_usage": 2.5,
        "weak_foot_accuracy": 3.0,
        "form": 6.5,
        "injury_resistance": 2.0,
    },
}

STYLE_RULES = {
    "goal poacher": {"offensive_awareness": 1.0, "finishing": 1.0, "acceleration": 1.0},
    "fox in the box": {"heading": 3.0, "physical_contact": 2.0, "balance": -1.0, "lofted_pass": 1.0},
    "target man": {"heading": 5.0, "physical_contact": 5.0, "speed": -3.0, "acceleration": -2.0, "low_pass": 2.0},
    "prolific winger": {"speed": 1.0, "acceleration": 1.0, "finishing": 1.0, "curl": 1.0},
    "roaming flank": {"finishing": 2.0, "curl": 2.0, "place_kicking": 1.0, "dribbling": 1.0},
    "creative playmaker": {"low_pass": 4.0, "lofted_pass": 4.0, "ball_control": 3.0, "tight_possession": 2.0, "curl": 2.0},
    "cross specialist": {"lofted_pass": 6.0, "low_pass": 2.0, "curl": 3.0, "place_kicking": 2.0},
    "hole player": {"offensive_awareness": 2.0, "finishing": 1.0, "low_pass": 3.0, "physical_contact": 2.0},
    "box-to-box": {"stamina": 3.0, "aggression": 2.0, "ball_winning": 2.0, "low_pass": 1.0},
    "orchestrator": {"low_pass": 4.0, "lofted_pass": 5.0, "tight_possession": 2.0, "balance": 2.0, "speed": -2.0},
    "anchor man": {"defensive_awareness": 4.0, "ball_winning": 4.0, "physical_contact": 3.0, "speed": -1.0},
    "build up": {"defensive_awareness": 4.0, "ball_winning": 4.0, "low_pass": 2.0, "lofted_pass": 3.0, "heading": 2.0},
    "offensive full-back": {"speed": 1.0, "stamina": 2.0, "low_pass": 2.0, "lofted_pass": 3.0, "curl": 2.0},
    "defensive full-back": {"defensive_awareness": 4.0, "ball_winning": 4.0, "aggression": 2.0, "speed": -1.0},
    "offensive goalkeeper": {"gk_clearing": 2.0, "gk_awareness": 1.0, "low_pass": 2.0, "lofted_pass": 2.0},
    "defensive goalkeeper": {"gk_catching": 2.0, "gk_reflexes": 1.0, "gk_reach": 1.0},
}

BOOSTER_HINTS = {
    "striker's instinct": {"offensive_awareness": 1.0, "finishing": 1.0},
    "aerial": {"heading": 2.0, "jump": 2.0},
    "ball-carrying": {"ball_control": 1.0, "dribbling": 1.0, "tight_possession": 1.0},
    "off the ball": {"offensive_awareness": 1.0, "acceleration": 1.0},
    "breakthrough": {"acceleration": 1.0, "speed": 1.0, "dribbling": 1.0},
    "agility": {"balance": 1.0, "acceleration": 1.0, "dribbling": 1.0},
    "shooting": {"finishing": 1.0, "kicking_power": 1.0, "place_kicking": 1.0},
    "offence creator": {"low_pass": 2.0, "lofted_pass": 1.0, "curl": 1.0},
    "saving": {"gk_catching": 1.0, "gk_reflexes": 1.0},
    "goalkeeping": {"gk_awareness": 1.0, "gk_reach": 1.0},
}

DATASET_STATE: Dict[str, Any] = {"path": None, "records": [], "family_counts": {}, "loaded": False}


def clamp(value: float, low: int = 40, high: int = 99) -> int:
    return int(max(low, min(high, round(float(value)))))


def safe_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return float(default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def normalize_key(key: str) -> str:
    key = str(key).strip().lower()
    key = key.replace("pes_", "").replace("ef_", "")
    key = re.sub(r"[^a-z0-9]+", "_", key)
    key = re.sub(r"_+", "_", key).strip("_")
    return key


def normalize_position(value: Any) -> str:
    pos = str(value or "").strip().upper()
    aliases = {
        "CENTER FORWARD": "CF",
        "CENTRE FORWARD": "CF",
        "SECOND STRIKER": "SS",
        "LEFT WING FORWARD": "LWF",
        "RIGHT WING FORWARD": "RWF",
        "LEFT MIDFIELDER": "LMF",
        "RIGHT MIDFIELDER": "RMF",
        "ATTACKING MIDFIELDER": "AMF",
        "CENTRAL MIDFIELDER": "CMF",
        "DEFENSIVE MIDFIELDER": "DMF",
        "LEFT BACK": "LB",
        "RIGHT BACK": "RB",
        "CENTRE BACK": "CB",
        "CENTER BACK": "CB",
        "GOALKEEPER": "GK",
    }
    return aliases.get(pos, pos or "CF")


def family_from_position(position: str) -> str:
    position = normalize_position(position)
    if position in {"CF", "SS"}:
        return "ATTACKER"
    if position in {"LWF", "RWF", "LMF", "RMF"}:
        return "WIDE"
    if position in {"AMF", "CMF", "DMF"}:
        return "MIDFIELDER"
    if position in {"LB", "RB", "CB"}:
        return "DEFENDER"
    if position == "GK":
        return "GOALKEEPER"
    return "ATTACKER"


def find_dataset_path() -> str | None:
    candidate_patterns = [
        "pes-20-21-efootball-dataset*.csv",
        "paired_pes2020_efootball_seed_dataset.csv",
    ]
    search_roots = [
        Path.cwd(),
        Path(__file__).resolve().parent,
        Path("/mnt/data"),
    ]
    matches: List[Path] = []
    for root in search_roots:
        if not root.exists():
            continue
        for pattern in candidate_patterns:
            matches.extend(root.glob(pattern))
    if not matches:
        return None
    matches = sorted(set(matches), key=lambda p: p.stat().st_mtime, reverse=True)
    return str(matches[0])


def build_base_projection(player: Dict[str, Any], use_clamp: bool = True) -> Dict[str, float]:
    stats = player.get("stats", {})
    direct = {
        "offensive_awareness": min(safe_float(stats.get("offensive_awareness")), 99),
        "finishing": min(safe_float(stats.get("finishing")), 99),
        "ball_control": min(safe_float(stats.get("ball_control")), 99),
        "dribbling": min(safe_float(stats.get("dribbling")), 99),
        "tight_possession": min(safe_float(stats.get("tight_possession")), 99),
        "low_pass": min(safe_float(stats.get("low_pass")), 99),
        "lofted_pass": min(safe_float(stats.get("lofted_pass")), 99),
        "heading": min(safe_float(stats.get("heading")), 99),
        "place_kicking": min(safe_float(stats.get("place_kicking")), 99),
        "curl": min(safe_float(stats.get("curl")), 99),
        "defensive_awareness": min(safe_float(stats.get("defensive_awareness")), 99),
        "aggression": min(safe_float(stats.get("aggression")), 99),
        "speed": min(safe_float(stats.get("speed")), 99),
        "acceleration": min(safe_float(stats.get("acceleration")), 99),
        "kicking_power": min(safe_float(stats.get("kicking_power")), 99),
        "jump": min(safe_float(stats.get("jump")), 99),
        "balance": min(safe_float(stats.get("balance")), 99),
        "stamina": min(safe_float(stats.get("stamina")), 99),
    }

    direct["physical_contact"] = (
        0.68 * safe_float(stats.get("physical"))
        + 0.20 * safe_float(stats.get("balance"))
        + 0.12 * safe_float(stats.get("jump"))
    )
    direct["ball_winning"] = (
        0.35 * safe_float(stats.get("defensive_awareness"))
        + 0.35 * safe_float(stats.get("defensive_engagement"))
        + 0.30 * safe_float(stats.get("tackling"))
    )
    direct["gk_awareness"] = (
        0.55 * safe_float(stats.get("goalkeeping"))
        + 0.15 * safe_float(stats.get("gk_reach"))
        + 0.15 * safe_float(stats.get("gk_reflexes"))
        + 0.15 * safe_float(stats.get("defensive_awareness"))
        + 8
    )
    direct["gk_catching"] = (
        0.65 * safe_float(stats.get("gk_catching"))
        + 0.20 * safe_float(stats.get("goalkeeping"))
        + 0.15 * safe_float(stats.get("balance"))
        + 14
    )
    direct["gk_clearing"] = (
        0.35 * safe_float(stats.get("goalkeeping"))
        + 0.25 * safe_float(stats.get("gk_parrying"))
        + 0.20 * safe_float(stats.get("kicking_power"))
        + 0.10 * safe_float(stats.get("lofted_pass"))
        + 0.10 * safe_float(stats.get("aggression"))
        + 10
    )
    direct["gk_reflexes"] = (
        0.60 * safe_float(stats.get("gk_reflexes"))
        + 0.25 * safe_float(stats.get("goalkeeping"))
        + 0.15 * safe_float(stats.get("balance"))
        + 11
    )
    direct["gk_reach"] = (
        0.70 * safe_float(stats.get("gk_reach"))
        + 0.30 * safe_float(stats.get("goalkeeping"))
        + 2
    )

    if not use_clamp:
        return direct

    return {key: clamp(value) for key, value in direct.items()}


def raw_projection_from_row(row: Dict[str, Any]) -> Dict[str, float]:
    return build_base_projection(
        {
            "stats": {stat: safe_float(row.get("ef_" + stat)) for stat in EF_REQUIRED_STATS}
        },
        use_clamp=False,
    )


def load_dataset_records() -> Dict[str, Any]:
    path = find_dataset_path()
    state = {"path": path, "records": [], "family_counts": {}, "loaded": False}
    if not path or not os.path.exists(path):
        return state

    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw_row in reader:
            row = dict(raw_row)
            position = normalize_position(row.get("pes_screenshot_position") or row.get("position"))
            family = family_from_position(position)
            parsed = {
                "player_name": row.get("player_name", ""),
                "position": position,
                "family": family,
                "playing_style": str(row.get("ef_playing_style", "")).strip(),
                "ef_vector": {stat: safe_float(row.get("ef_" + stat)) for stat in EF_REQUIRED_STATS},
                "pes_target": {stat: safe_float(row.get("pes_" + stat)) for stat in PES_OUTPUT_ORDER},
            }
            parsed["raw_projection"] = raw_projection_from_row(row)
            state["records"].append(parsed)

    family_counts: Dict[str, int] = {}
    for record in state["records"]:
        family_counts[record["family"]] = family_counts.get(record["family"], 0) + 1

    state["family_counts"] = family_counts
    state["loaded"] = True
    return state


def find_style_adjustments(player: Dict[str, Any]) -> Tuple[Dict[str, float], List[str]]:
    style_text = " ".join([
        str(player.get("playing_style", "")),
        str(player.get("booster_1", "")),
        str(player.get("booster_2", "")),
    ]).lower()

    delta: Dict[str, float] = {}
    notes: List[str] = []

    for label, rule in STYLE_RULES.items():
        if label in style_text:
            for stat, value in rule.items():
                delta[stat] = delta.get(stat, 0.0) + value
            notes.append(f"Style rule aktif: {label}")

    for label, rule in BOOSTER_HINTS.items():
        if label in style_text:
            for stat, value in rule.items():
                delta[stat] = delta.get(stat, 0.0) + value * 0.5
            notes.append(f"Booster hint aktif: {label}")

    return delta, notes


def weighted_neighbor_delta(player: Dict[str, Any], family: str, top_k: int = 5) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
    if not DATASET_STATE["loaded"] or not DATASET_STATE["records"]:
        return {}, []

    target = player["stats"]
    candidates: List[Tuple[float, Dict[str, Any]]] = []
    for record in DATASET_STATE["records"]:
        distance = 0.0
        for stat in EF_REQUIRED_STATS:
            distance += abs(safe_float(target.get(stat)) - safe_float(record["ef_vector"].get(stat)))

        if record["family"] == family:
            distance *= 0.75
        if str(player.get("playing_style", "")).strip().lower() == str(record.get("playing_style", "")).strip().lower():
            distance *= 0.85

        candidates.append((distance, record))

    candidates.sort(key=lambda item: item[0])
    top = candidates[: max(1, min(top_k, len(candidates)))]
    deltas: Dict[str, float] = {}
    neighbor_meta: List[Dict[str, Any]] = []

    total_weight = 0.0
    for distance, record in top:
        weight = 1.0 / max(distance, 1.0)
        total_weight += weight
        neighbor_meta.append(
            {
                "player_name": record["player_name"],
                "position": record["position"],
                "family": record["family"],
                "distance": round(distance, 2),
            }
        )
        for stat in DIRECT_STATS + SPECIAL_STATS:
            target_stat = safe_float(record["pes_target"].get(stat))
            raw_stat = safe_float(record["raw_projection"].get(stat))
            delta_value = target_stat - raw_stat
            deltas[stat] = deltas.get(stat, 0.0) + (delta_value * weight)

        for stat in ["weak_foot_usage", "weak_foot_accuracy", "form", "injury_resistance"]:
            deltas[stat] = deltas.get(stat, 0.0) + (safe_float(record["pes_target"].get(stat)) * weight)

    if total_weight == 0:
        return {}, neighbor_meta

    normalized = {key: value / total_weight for key, value in deltas.items()}
    return normalized, neighbor_meta


def merge_deltas(
    base: Dict[str, float],
    family_delta: Dict[str, float],
    knn_delta: Dict[str, float],
    style_delta: Dict[str, float],
    family_weight: float = 0.6,
    knn_weight: float = 0.4,
) -> Dict[str, int]:
    output: Dict[str, int] = {}

    for stat in DIRECT_STATS + SPECIAL_STATS:
        value = safe_float(base.get(stat))
        value += family_weight * safe_float(family_delta.get(stat))
        if knn_delta:
            value += knn_weight * safe_float(knn_delta.get(stat))
        value += safe_float(style_delta.get(stat))
        output[stat] = clamp(value)

    output["weak_foot_usage"] = clamp(
        (family_weight * safe_float(family_delta.get("weak_foot_usage", 2.5)))
        + (knn_weight * safe_float(knn_delta.get("weak_foot_usage", 2.5)) if knn_delta else 0)
        + 1.0,
        1,
        4,
    )
    output["weak_foot_accuracy"] = clamp(
        (family_weight * safe_float(family_delta.get("weak_foot_accuracy", 3.0)))
        + (knn_weight * safe_float(knn_delta.get("weak_foot_accuracy", 3.0)) if knn_delta else 0)
        + 1.0,
        1,
        4,
    )
    output["form"] = clamp(
        (family_weight * safe_float(family_delta.get("form", 6.0)))
        + (knn_weight * safe_float(knn_delta.get("form", 6.0)) if knn_delta else 0),
        1,
        8,
    )
    output["injury_resistance"] = clamp(
        (family_weight * safe_float(family_delta.get("injury_resistance", 2.0)))
        + (knn_weight * safe_float(knn_delta.get("injury_resistance", 2.0)) if knn_delta else 0),
        1,
        3,
    )
    return output


def estimate_confidence(family: str, neighbors: List[Dict[str, Any]]) -> Tuple[str, float]:
    family_count = DATASET_STATE["family_counts"].get(family, 0)
    if not neighbors:
        base = 0.45
    else:
        avg_distance = sum(item["distance"] for item in neighbors) / len(neighbors)
        base = max(0.25, 0.85 - min(avg_distance / 150.0, 0.4))
    base += min(family_count / 25.0, 0.2)
    base = min(0.95, max(0.25, base))

    if base >= 0.75:
        label = "tinggi"
    elif base >= 0.55:
        label = "sedang"
    else:
        label = "rendah"

    return label, round(base, 2)


def extract_player_input(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("JSON utama harus berupa object.")

    player = {
        "player_name": payload.get("player_name") or payload.get("name") or "Unknown Player",
        "position": normalize_position(payload.get("position") or payload.get("ef_position") or "CF"),
        "playing_style": payload.get("playing_style") or payload.get("style") or payload.get("ef_playing_style") or "",
        "booster_1": payload.get("booster_1") or payload.get("ef_booster_1") or "",
        "booster_2": payload.get("booster_2") or payload.get("ef_booster_2") or "",
        "age": safe_float(payload.get("age")),
        "height_cm": safe_float(payload.get("height_cm") or payload.get("height")),
        "weight_kg": safe_float(payload.get("weight_kg") or payload.get("weight")),
        "foot": payload.get("foot") or payload.get("ef_foot") or "",
        "condition": payload.get("condition") or payload.get("ef_condition") or "",
        "stats": {},
    }

    stats_block = payload.get("stats", {})
    if not isinstance(stats_block, dict):
        stats_block = {}

    flat_sources = [payload, stats_block]
    for source in flat_sources:
        for key, value in source.items():
            normalized = normalize_key(key)
            if normalized in EF_REQUIRED_STATS:
                player["stats"][normalized] = safe_float(value)

    missing = [stat for stat in EF_REQUIRED_STATS if stat not in player["stats"]]
    if missing:
        raise ValueError(
            "Stat eFootball belum lengkap. Minimal field yang wajib ada: " + ", ".join(missing)
        )

    return player


def convert_player(payload: Dict[str, Any]) -> Dict[str, Any]:
    player = extract_player_input(payload)
    family = family_from_position(player["position"])
    player["family"] = family

    base = build_base_projection(player)
    family_delta = FAMILY_DELTA_PROFILES.get(family, FAMILY_DELTA_PROFILES["ATTACKER"])
    knn_delta, neighbors = weighted_neighbor_delta(player, family)
    style_delta, notes = find_style_adjustments(player)

    pes_stats = merge_deltas(
        base=base,
        family_delta=family_delta,
        knn_delta=knn_delta,
        style_delta=style_delta,
    )

    confidence_label, confidence_score = estimate_confidence(family, neighbors)

    return {
        "input_meta": {
            "player_name": player["player_name"],
            "position": player["position"],
            "family": family,
            "playing_style": player["playing_style"],
            "booster_1": player["booster_1"],
            "booster_2": player["booster_2"],
            "age": player["age"],
            "height_cm": player["height_cm"],
            "weight_kg": player["weight_kg"],
            "foot": player["foot"],
            "condition": player["condition"],
        },
        "projection_meta": {
            "target_format": "PES 2020/2021 style stats",
            "engine_mode": "hybrid rule-based + dataset-guided nearest profile",
            "dataset_loaded": DATASET_STATE["loaded"],
            "dataset_path": DATASET_STATE["path"],
            "dataset_records": len(DATASET_STATE["records"]),
            "family_count": DATASET_STATE["family_counts"].get(family, 0),
            "confidence_label": confidence_label,
            "confidence_score": confidence_score,
        },
        "pes_stats": pes_stats,
        "base_projection_before_adjustment": base,
        "style_adjustments": style_delta,
        "neighbors_used": neighbors,
        "notes": notes or ["Tidak ada style rule tambahan yang aktif."],
    }


@app.route("/", methods=["GET"])
def index() -> str:
    return render_template(
        "index.html",
        dataset_loaded=DATASET_STATE["loaded"],
        dataset_path=DATASET_STATE["path"],
        dataset_records=len(DATASET_STATE["records"]),
        family_counts=DATASET_STATE["family_counts"],
    )


@app.route("/api/convert", methods=["POST"])
def api_convert():
    try:
        payload = request.get_json(force=True, silent=False)
        result = convert_player(payload)
        return jsonify({"ok": True, "result": result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify(
        {
            "ok": True,
            "dataset_loaded": DATASET_STATE["loaded"],
            "dataset_path": DATASET_STATE["path"],
            "dataset_records": len(DATASET_STATE["records"]),
            "family_counts": DATASET_STATE["family_counts"],
        }
    )


DATASET_STATE = load_dataset_records()


if __name__ == "__main__":
    app.run(debug=True)
