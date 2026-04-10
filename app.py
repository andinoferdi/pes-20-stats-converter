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

STAT_DISTANCE_WEIGHTS = {
    "ATTACKER": {
        "offensive_awareness": 2.6,
        "finishing": 2.8,
        "ball_control": 1.8,
        "dribbling": 1.4,
        "tight_possession": 1.7,
        "low_pass": 0.9,
        "lofted_pass": 0.8,
        "heading": 1.8,
        "place_kicking": 0.8,
        "curl": 0.7,
        "defensive_awareness": 0.4,
        "defensive_engagement": 0.3,
        "tackling": 0.3,
        "aggression": 0.7,
        "goalkeeping": 0.1,
        "gk_catching": 0.1,
        "gk_parrying": 0.1,
        "gk_reflexes": 0.1,
        "gk_reach": 0.1,
        "speed": 1.6,
        "acceleration": 1.8,
        "kicking_power": 1.4,
        "jump": 1.0,
        "physical": 1.4,
        "balance": 1.0,
        "stamina": 1.0,
    },
    "WIDE": {
        "offensive_awareness": 1.7,
        "finishing": 1.5,
        "ball_control": 2.0,
        "dribbling": 2.4,
        "tight_possession": 2.2,
        "low_pass": 1.3,
        "lofted_pass": 1.2,
        "heading": 0.6,
        "place_kicking": 1.0,
        "curl": 1.3,
        "defensive_awareness": 0.5,
        "defensive_engagement": 0.5,
        "tackling": 0.4,
        "aggression": 0.6,
        "goalkeeping": 0.1,
        "gk_catching": 0.1,
        "gk_parrying": 0.1,
        "gk_reflexes": 0.1,
        "gk_reach": 0.1,
        "speed": 1.9,
        "acceleration": 2.0,
        "kicking_power": 1.2,
        "jump": 0.7,
        "physical": 1.0,
        "balance": 1.3,
        "stamina": 1.2,
    },
    "MIDFIELDER": {
        "offensive_awareness": 1.5,
        "finishing": 1.0,
        "ball_control": 1.9,
        "dribbling": 1.5,
        "tight_possession": 1.8,
        "low_pass": 2.2,
        "lofted_pass": 2.0,
        "heading": 0.7,
        "place_kicking": 1.1,
        "curl": 1.2,
        "defensive_awareness": 1.3,
        "defensive_engagement": 1.3,
        "tackling": 1.2,
        "aggression": 1.0,
        "goalkeeping": 0.1,
        "gk_catching": 0.1,
        "gk_parrying": 0.1,
        "gk_reflexes": 0.1,
        "gk_reach": 0.1,
        "speed": 1.0,
        "acceleration": 1.0,
        "kicking_power": 1.1,
        "jump": 0.8,
        "physical": 1.0,
        "balance": 1.4,
        "stamina": 1.5,
    },
    "DEFENDER": {
        "offensive_awareness": 0.4,
        "finishing": 0.3,
        "ball_control": 1.0,
        "dribbling": 0.7,
        "tight_possession": 0.9,
        "low_pass": 1.3,
        "lofted_pass": 1.4,
        "heading": 1.7,
        "place_kicking": 0.5,
        "curl": 0.4,
        "defensive_awareness": 2.4,
        "defensive_engagement": 2.2,
        "tackling": 2.3,
        "aggression": 1.4,
        "goalkeeping": 0.1,
        "gk_catching": 0.1,
        "gk_parrying": 0.1,
        "gk_reflexes": 0.1,
        "gk_reach": 0.1,
        "speed": 1.1,
        "acceleration": 1.0,
        "kicking_power": 0.9,
        "jump": 1.5,
        "physical": 1.9,
        "balance": 0.8,
        "stamina": 1.1,
    },
    "GOALKEEPER": {
        "offensive_awareness": 0.1,
        "finishing": 0.1,
        "ball_control": 0.4,
        "dribbling": 0.3,
        "tight_possession": 0.3,
        "low_pass": 0.6,
        "lofted_pass": 0.8,
        "heading": 0.3,
        "place_kicking": 0.3,
        "curl": 0.1,
        "defensive_awareness": 1.0,
        "defensive_engagement": 0.9,
        "tackling": 0.7,
        "aggression": 0.6,
        "goalkeeping": 3.0,
        "gk_catching": 3.0,
        "gk_parrying": 3.0,
        "gk_reflexes": 3.0,
        "gk_reach": 3.0,
        "speed": 0.6,
        "acceleration": 0.6,
        "kicking_power": 0.9,
        "jump": 1.1,
        "physical": 1.0,
        "balance": 0.8,
        "stamina": 0.7,
    },
}

DIRECT_HIGH_STAT_GUARDRAILS = {
    "offensive_awareness": [(96, 0), (92, 1), (88, 2)],
    "finishing": [(96, 0), (92, 1), (88, 2)],
    "ball_control": [(96, 0), (92, 1), (88, 2)],
    "dribbling": [(96, 0), (92, 1), (88, 2)],
    "tight_possession": [(96, 0), (92, 1), (88, 2)],
    "low_pass": [(96, 1), (92, 2), (88, 3)],
    "lofted_pass": [(96, 1), (92, 2), (88, 3)],
    "heading": [(95, 0), (91, 1), (87, 2)],
    "place_kicking": [(96, 1), (92, 2), (88, 3)],
    "curl": [(96, 1), (92, 2), (88, 3)],
    "defensive_awareness": [(96, 0), (92, 1), (88, 2)],
    "aggression": [(96, 0), (92, 1), (88, 2)],
    "speed": [(96, 0), (92, 1), (88, 2)],
    "acceleration": [(96, 0), (92, 1), (88, 2)],
    "kicking_power": [(96, 0), (92, 1), (88, 2)],
    "jump": [(95, 0), (91, 1), (87, 2)],
    "balance": [(96, 0), (92, 1), (88, 2)],
    "stamina": [(96, 0), (92, 1), (88, 2)],
}

OVERFLOW_REDISTRIBUTION_PRIORITY = {
    "offensive_awareness": ["finishing", "acceleration", "ball_control", "speed"],
    "finishing": ["offensive_awareness", "kicking_power", "curl", "ball_control"],
    "ball_control": ["dribbling", "tight_possession", "low_pass", "balance"],
    "dribbling": ["ball_control", "tight_possession", "speed", "acceleration"],
    "tight_possession": ["ball_control", "dribbling", "low_pass", "balance"],
    "low_pass": ["lofted_pass", "ball_control", "tight_possession", "place_kicking"],
    "lofted_pass": ["low_pass", "curl", "place_kicking", "ball_control"],
    "heading": ["jump", "physical_contact", "offensive_awareness", "kicking_power"],
    "place_kicking": ["curl", "kicking_power", "low_pass", "lofted_pass"],
    "curl": ["place_kicking", "lofted_pass", "finishing", "low_pass"],
    "defensive_awareness": ["ball_winning", "aggression", "physical_contact", "stamina"],
    "aggression": ["ball_winning", "defensive_awareness", "stamina", "physical_contact"],
    "speed": ["acceleration", "dribbling", "balance", "stamina"],
    "acceleration": ["speed", "dribbling", "balance", "offensive_awareness"],
    "kicking_power": ["finishing", "place_kicking", "curl", "heading"],
    "jump": ["heading", "physical_contact", "balance", "stamina"],
    "balance": ["acceleration", "dribbling", "tight_possession", "stamina"],
    "stamina": ["speed", "balance", "aggression", "low_pass"],
    "physical_contact": ["jump", "ball_winning", "defensive_awareness", "heading"],
    "ball_winning": ["defensive_awareness", "aggression", "physical_contact", "stamina"],
    "gk_awareness": ["gk_catching", "gk_reflexes", "gk_reach", "gk_clearing"],
    "gk_catching": ["gk_awareness", "gk_reflexes", "gk_reach", "balance"],
    "gk_clearing": ["gk_awareness", "gk_reach", "gk_reflexes", "lofted_pass"],
    "gk_reflexes": ["gk_awareness", "gk_catching", "gk_reach", "balance"],
    "gk_reach": ["gk_awareness", "gk_reflexes", "gk_catching", "jump"],
}

FAMILY_REDISTRIBUTION_FALLBACKS = {
    "ATTACKER": [
        "offensive_awareness", "finishing", "kicking_power", "ball_control", "dribbling",
        "tight_possession", "speed", "acceleration", "balance", "heading", "jump",
        "low_pass", "curl", "place_kicking", "stamina", "physical_contact",
    ],
    "WIDE": [
        "speed", "acceleration", "dribbling", "ball_control", "tight_possession",
        "low_pass", "lofted_pass", "curl", "place_kicking", "stamina", "balance",
        "offensive_awareness", "finishing",
    ],
    "MIDFIELDER": [
        "low_pass", "lofted_pass", "ball_control", "tight_possession", "dribbling",
        "balance", "stamina", "defensive_awareness", "ball_winning", "aggression",
        "kicking_power", "offensive_awareness", "speed", "acceleration",
    ],
    "DEFENDER": [
        "defensive_awareness", "ball_winning", "physical_contact", "aggression", "jump",
        "heading", "stamina", "low_pass", "lofted_pass", "speed", "acceleration",
        "balance", "kicking_power",
    ],
    "GOALKEEPER": [
        "gk_awareness", "gk_catching", "gk_clearing", "gk_reflexes", "gk_reach",
        "jump", "physical_contact", "balance", "lofted_pass", "low_pass",
    ],
}

CONDITION_MAP = {"E": 0, "D": 1, "C": 2, "B": 3, "A": 4}

DATASET_STATE: Dict[str, Any] = {"path": None, "records": [], "family_counts": {}, "loaded": False}
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


def find_dataset_paths() -> List[str]:
    candidate_patterns = [
        "pes-20-21-efootball-dataset*.csv",
        "paired_pes2020_efootball_seed_dataset.csv",
    ]
    search_roots = [
        Path.cwd() / "dataset",
        Path.cwd(),
        Path(__file__).resolve().parent / "dataset",
        Path(__file__).resolve().parent,
        Path("/mnt/data"),
    ]
    matches: List[Path] = []
    for root in search_roots:
        if not root.exists():
            continue
        for pattern in candidate_patterns:
            for candidate in root.glob(pattern):
                if candidate.name.lower().endswith("-backup.csv"):
                    continue
                matches.append(candidate)
    unique_matches = sorted(set(matches), key=lambda p: (p.stat().st_mtime, str(p)), reverse=True)
    return [str(item) for item in unique_matches]


def is_valid_dataset_row(row: Dict[str, Any]) -> bool:
    if not str(row.get("player_name", "")).strip():
        return False
    if not normalize_position(row.get("pes_screenshot_position") or row.get("position")):
        return False
    present_stats = sum(1 for stat in EF_REQUIRED_STATS if str(row.get("ef_" + stat, "")).strip() != "")
    return present_stats >= 20


def dataset_record_key(row: Dict[str, Any]) -> Tuple[str, str, str, str, int]:
    player_name = str(row.get("player_name", "")).strip().lower()
    pes_position = normalize_position(row.get("pes_screenshot_position") or row.get("position"))
    ef_position = normalize_position(row.get("ef_screenshot_position") or row.get("position"))
    style = str(row.get("ef_playing_style", "")).strip().lower()
    ef_ovr = int(safe_float(row.get("ef_screenshot_ovr"), -1))
    return (player_name, pes_position, ef_position, style, ef_ovr)


def summarize_dataset_paths(paths: List[str]) -> str | None:
    if not paths:
        return None
    if len(paths) == 1:
        return paths[0]
    return paths[0] + f" | +{len(paths) - 1} file lain"


def normalize_style_text(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").strip().lower()).strip()


def metadata_distance(player: Dict[str, Any], record: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
    distance = 0.0
    breakdown: Dict[str, Any] = {}

    same_name = str(player.get("player_name", "")).strip().lower() == str(record.get("player_name", "")).strip().lower()
    same_position = normalize_position(player.get("position")) == normalize_position(record.get("position"))
    same_style = normalize_style_text(player.get("playing_style")) == normalize_style_text(record.get("playing_style"))

    if not same_position:
        distance += 12.0
    if same_style:
        distance -= 2.0
    elif player.get("playing_style") and record.get("playing_style"):
        distance += 6.0
    if same_name:
        distance -= 6.0

    height_penalty = abs(safe_float(player.get("height_cm")) - safe_float(record.get("height_cm"))) * 0.22
    weight_penalty = abs(safe_float(player.get("weight_kg")) - safe_float(record.get("weight_kg"))) * 0.18
    age_penalty = abs(safe_float(player.get("age")) - safe_float(record.get("age"))) * 0.20

    distance += height_penalty + weight_penalty + age_penalty

    if str(player.get("foot", "")).strip().lower() != str(record.get("foot", "")).strip().lower():
        distance += 3.0

    condition_gap = abs(CONDITION_MAP.get(str(player.get("condition", "C")).strip().upper(), 2) - CONDITION_MAP.get(str(record.get("condition", "C")).strip().upper(), 2))
    distance += condition_gap * 1.5

    for booster_key in ("booster_1", "booster_2"):
        player_booster = normalize_style_text(player.get(booster_key))
        record_booster = normalize_style_text(record.get(booster_key))
        if player_booster != record_booster:
            if player_booster and record_booster:
                distance += 1.8
            elif player_booster or record_booster:
                distance += 0.9

    distance = max(distance, 0.0)
    breakdown["same_name"] = same_name
    breakdown["same_position"] = same_position
    breakdown["same_style"] = same_style
    breakdown["height_penalty"] = round(height_penalty, 2)
    breakdown["weight_penalty"] = round(weight_penalty, 2)
    breakdown["age_penalty"] = round(age_penalty, 2)
    breakdown["metadata_distance"] = round(distance, 2)
    return distance, breakdown


def get_family_stat_weights(family: str) -> Dict[str, float]:
    return STAT_DISTANCE_WEIGHTS.get(family, STAT_DISTANCE_WEIGHTS["ATTACKER"])


def derive_empirical_delta_profiles(records: List[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, float]], Dict[str, int], Dict[str, int]]:
    family_sums: Dict[str, Dict[str, float]] = {}
    family_counts: Dict[str, int] = {}
    position_sums: Dict[str, Dict[str, float]] = {}
    position_counts: Dict[str, int] = {}

    tracked_stats = DIRECT_STATS + SPECIAL_STATS + ["weak_foot_usage", "weak_foot_accuracy", "form", "injury_resistance"]

    for record in records:
        family = record["family"]
        position = record["position"]
        family_sums.setdefault(family, {})
        position_sums.setdefault(position, {})
        family_counts[family] = family_counts.get(family, 0) + 1
        position_counts[position] = position_counts.get(position, 0) + 1

        for stat in DIRECT_STATS + SPECIAL_STATS:
            delta_value = safe_float(record["pes_target"].get(stat)) - safe_float(record["raw_projection"].get(stat))
            family_sums[family][stat] = family_sums[family].get(stat, 0.0) + delta_value
            position_sums[position][stat] = position_sums[position].get(stat, 0.0) + delta_value

        for stat in ["weak_foot_usage", "weak_foot_accuracy", "form", "injury_resistance"]:
            target_value = safe_float(record["pes_target"].get(stat))
            family_sums[family][stat] = family_sums[family].get(stat, 0.0) + target_value
            position_sums[position][stat] = position_sums[position].get(stat, 0.0) + target_value

    family_profiles = {family: {stat: values.get(stat, 0.0) / family_counts[family] for stat in tracked_stats} for family, values in family_sums.items()}
    position_profiles = {position: {stat: values.get(stat, 0.0) / position_counts[position] for stat in tracked_stats} for position, values in position_sums.items()}
    return family_profiles, position_profiles, family_counts, position_counts


def resolve_delta_profile(player: Dict[str, Any], family: str, position: str) -> Tuple[Dict[str, float], List[str]]:
    notes: List[str] = []
    fallback = FAMILY_DELTA_PROFILES.get(family, FAMILY_DELTA_PROFILES["ATTACKER"])
    family_profiles = DATASET_STATE.get("family_delta_profiles", {})
    position_profiles = DATASET_STATE.get("position_delta_profiles", {})
    family_counts = DATASET_STATE.get("family_counts", {})
    position_counts = DATASET_STATE.get("position_counts", {})

    family_empirical = family_profiles.get(family)
    position_empirical = position_profiles.get(position)
    family_count = family_counts.get(family, 0)
    position_count = position_counts.get(position, 0)

    tracked_stats = DIRECT_STATS + SPECIAL_STATS + ["weak_foot_usage", "weak_foot_accuracy", "form", "injury_resistance"]
    profile: Dict[str, float] = {}

    if position_empirical and position_count >= 5:
        for stat in tracked_stats:
            profile[stat] = (0.75 * safe_float(position_empirical.get(stat))) + (0.25 * safe_float(fallback.get(stat)))
        notes.append(f"Profil posisi aktif: {position} berbasis {position_count} data")
        return profile, notes

    if family_empirical and family_count >= 8:
        for stat in tracked_stats:
            profile[stat] = (0.70 * safe_float(family_empirical.get(stat))) + (0.30 * safe_float(fallback.get(stat)))
        notes.append(f"Profil family aktif: {family} berbasis {family_count} data")
        return profile, notes

    notes.append(f"Fallback family profile aktif: {family}")
    return dict(fallback), notes


def apply_high_stat_guardrails(player: Dict[str, Any], output: Dict[str, int]) -> Dict[str, int]:
    protected = dict(output)
    for stat, rules in DIRECT_HIGH_STAT_GUARDRAILS.items():
        ef_value = clamp(min(safe_float(player["stats"].get(stat)), 99))
        for threshold, tolerance in rules:
            if ef_value >= threshold:
                floor_value = max(40, ef_value - tolerance)
                protected[stat] = max(protected.get(stat, 40), floor_value)
                break

    if player.get("family") == "GOALKEEPER":
        for stat in ["gk_awareness", "gk_catching", "gk_clearing", "gk_reflexes", "gk_reach"]:
            ef_source_key = stat.replace("gk_awareness", "goalkeeping") if stat == "gk_awareness" else stat
            if stat == "gk_clearing":
                ef_value = max(safe_float(player["stats"].get("goalkeeping")), safe_float(player["stats"].get("gk_parrying")))
            elif stat == "gk_awareness":
                ef_value = safe_float(player["stats"].get("goalkeeping"))
            else:
                ef_value = safe_float(player["stats"].get(ef_source_key))
            ef_value = clamp(min(ef_value, 99))
            if ef_value >= 95:
                protected[stat] = max(protected.get(stat, 40), ef_value - 1)
    return protected


def choose_family_weight(family: str, family_count: int) -> Tuple[float, float]:
    if family_count >= 40:
        return 0.35, 0.65
    if family_count >= 15:
        return 0.45, 0.55
    if family_count >= 8:
        return 0.55, 0.45
    return 0.70, 0.30


def build_base_projection(player: Dict[str, Any], use_clamp: bool = True) -> Dict[str, float]:
    stats = player.get("stats", {})
    direct = {
        "offensive_awareness": safe_float(stats.get("offensive_awareness")),
        "finishing": safe_float(stats.get("finishing")),
        "ball_control": safe_float(stats.get("ball_control")),
        "dribbling": safe_float(stats.get("dribbling")),
        "tight_possession": safe_float(stats.get("tight_possession")),
        "low_pass": safe_float(stats.get("low_pass")),
        "lofted_pass": safe_float(stats.get("lofted_pass")),
        "heading": safe_float(stats.get("heading")),
        "place_kicking": safe_float(stats.get("place_kicking")),
        "curl": safe_float(stats.get("curl")),
        "defensive_awareness": safe_float(stats.get("defensive_awareness")),
        "aggression": safe_float(stats.get("aggression")),
        "speed": safe_float(stats.get("speed")),
        "acceleration": safe_float(stats.get("acceleration")),
        "kicking_power": safe_float(stats.get("kicking_power")),
        "jump": safe_float(stats.get("jump")),
        "balance": safe_float(stats.get("balance")),
        "stamina": safe_float(stats.get("stamina")),
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
    paths = find_dataset_paths()
    state = {
        "path": summarize_dataset_paths(paths),
        "paths": paths,
        "records": [],
        "family_counts": {},
        "position_counts": {},
        "family_delta_profiles": {},
        "position_delta_profiles": {},
        "loaded": False,
    }
    if not paths:
        return state

    seen_keys = set()
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for raw_row in reader:
                row = dict(raw_row)
                if not is_valid_dataset_row(row):
                    continue
                dedupe_key = dataset_record_key(row)
                if dedupe_key in seen_keys:
                    continue
                seen_keys.add(dedupe_key)

                position = normalize_position(row.get("pes_screenshot_position") or row.get("position"))
                family = family_from_position(position)
                parsed = {
                    "player_name": row.get("player_name", ""),
                    "position": position,
                    "family": family,
                    "playing_style": str(row.get("ef_playing_style", "")).strip(),
                    "booster_1": str(row.get("ef_booster_1", "")).strip(),
                    "booster_2": str(row.get("ef_booster_2", "")).strip(),
                    "age": safe_float(row.get("ef_age") or row.get("pes_age")),
                    "height_cm": safe_float(row.get("ef_height_cm") or row.get("pes_height_cm")),
                    "weight_kg": safe_float(row.get("ef_weight_kg") or row.get("pes_weight_kg")),
                    "foot": str(row.get("ef_foot", "")).strip(),
                    "condition": str(row.get("ef_condition", "")).strip(),
                    "ef_position": normalize_position(row.get("ef_screenshot_position") or row.get("position")),
                    "ef_vector": {stat: safe_float(row.get("ef_" + stat)) for stat in EF_REQUIRED_STATS},
                    "pes_target": {stat: safe_float(row.get("pes_" + stat)) for stat in PES_OUTPUT_ORDER},
                }
                parsed["raw_projection"] = raw_projection_from_row(row)
                state["records"].append(parsed)

    family_profiles, position_profiles, family_counts, position_counts = derive_empirical_delta_profiles(state["records"])
    state["family_counts"] = family_counts
    state["position_counts"] = position_counts
    state["family_delta_profiles"] = family_profiles
    state["position_delta_profiles"] = position_profiles
    state["loaded"] = len(state["records"]) > 0
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


def weighted_neighbor_delta(player: Dict[str, Any], family: str, top_k: int = 7) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
    if not DATASET_STATE["loaded"] or not DATASET_STATE["records"]:
        return {}, []

    target = player["stats"]
    stat_weights = get_family_stat_weights(family)
    candidates: List[Tuple[float, float, float, Dict[str, Any], Dict[str, Any]]] = []

    for record in DATASET_STATE["records"]:
        stat_distance = 0.0
        for stat in EF_REQUIRED_STATS:
            weight = safe_float(stat_weights.get(stat), 1.0)
            diff = abs(safe_float(target.get(stat)) - safe_float(record["ef_vector"].get(stat)))
            stat_distance += diff * weight

        meta_distance, meta_breakdown = metadata_distance(player, record)
        total_distance = stat_distance + meta_distance

        if record["family"] != family:
            total_distance += 18.0
        candidates.append((total_distance, stat_distance, meta_distance, record, meta_breakdown))

    candidates.sort(key=lambda item: item[0])
    top = candidates[: max(1, min(top_k, len(candidates)))]
    deltas: Dict[str, float] = {}
    neighbor_meta: List[Dict[str, Any]] = []

    total_weight = 0.0
    for total_distance, stat_distance, meta_distance, record, meta_breakdown in top:
        weight = 1.0 / max(total_distance, 0.25)
        total_weight += weight
        neighbor_meta.append(
            {
                "player_name": record["player_name"],
                "position": record["position"],
                "family": record["family"],
                "distance": round(total_distance, 2),
                "distance_stats": round(stat_distance, 2),
                "distance_meta": round(meta_distance, 2),
                "same_name": meta_breakdown.get("same_name", False),
                "same_style": meta_breakdown.get("same_style", False),
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


def merge_deltas_raw(
    player: Dict[str, Any],
    base: Dict[str, float],
    family_delta: Dict[str, float],
    knn_delta: Dict[str, float],
    style_delta: Dict[str, float],
    family_count: int = 0,
) -> Dict[str, float]:
    output: Dict[str, float] = {}
    family_weight, knn_weight = choose_family_weight(player.get("family", "ATTACKER"), family_count)

    for stat in DIRECT_STATS + SPECIAL_STATS:
        value = safe_float(base.get(stat))
        value += family_weight * safe_float(family_delta.get(stat))
        if knn_delta:
            value += knn_weight * safe_float(knn_delta.get(stat))
        value += safe_float(style_delta.get(stat))
        output[stat] = value

    output["weak_foot_usage"] = (
        (family_weight * safe_float(family_delta.get("weak_foot_usage", 2.5)))
        + (knn_weight * safe_float(knn_delta.get("weak_foot_usage", 2.5)) if knn_delta else 0)
        + 1.0
    )
    output["weak_foot_accuracy"] = (
        (family_weight * safe_float(family_delta.get("weak_foot_accuracy", 3.0)))
        + (knn_weight * safe_float(knn_delta.get("weak_foot_accuracy", 3.0)) if knn_delta else 0)
        + 1.0
    )
    output["form"] = (
        (family_weight * safe_float(family_delta.get("form", 6.0)))
        + (knn_weight * safe_float(knn_delta.get("form", 6.0)) if knn_delta else 0)
    )
    output["injury_resistance"] = (
        (family_weight * safe_float(family_delta.get("injury_resistance", 2.0)))
        + (knn_weight * safe_float(knn_delta.get("injury_resistance", 2.0)) if knn_delta else 0)
    )
    return output


def redistribute_overflow(
    player: Dict[str, Any],
    base_projection: Dict[str, float],
    raw_output: Dict[str, float],
    high: int = 99,
) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
    working = {stat: safe_float(raw_output.get(stat)) for stat in raw_output}
    transferable_stats = DIRECT_STATS + SPECIAL_STATS
    family = player.get("family", "ATTACKER")
    fallback_targets = FAMILY_REDISTRIBUTION_FALLBACKS.get(family, [])
    transfers_log: List[Dict[str, Any]] = []

    donor_candidates = []
    for stat in transferable_stats:
        source_overflow = max(0.0, safe_float(base_projection.get(stat)) - high)
        merged_overflow = max(0.0, safe_float(raw_output.get(stat)) - high)
        overflow_pool = max(source_overflow, merged_overflow)
        if overflow_pool > 0:
            donor_candidates.append((stat, overflow_pool, source_overflow, merged_overflow))

    donor_candidates = sorted(donor_candidates, key=lambda item: item[1], reverse=True)

    for donor, overflow_pool, source_overflow, merged_overflow in donor_candidates:
        if overflow_pool <= 0:
            continue

        if source_overflow > 0 or safe_float(working.get(donor)) > high:
            working[donor] = float(high)

        remaining = overflow_pool
        transfer_steps: List[Dict[str, float]] = []
        attempted = set()
        ordered_targets = OVERFLOW_REDISTRIBUTION_PRIORITY.get(donor, []) + fallback_targets + transferable_stats

        for receiver in ordered_targets:
            if receiver == donor or receiver in attempted:
                continue
            attempted.add(receiver)

            receiver_value = safe_float(working.get(receiver))
            if receiver_value >= high:
                continue

            capacity = high - receiver_value
            if capacity <= 0:
                continue

            transfer_value = min(remaining, capacity)
            working[receiver] = receiver_value + transfer_value
            remaining -= transfer_value
            transfer_steps.append({"to": receiver, "amount": round(transfer_value, 2)})

            if remaining <= 1e-9:
                remaining = 0.0
                break

        transfers_log.append(
            {
                "from": donor,
                "overflow_pool": round(overflow_pool, 2),
                "source_overflow": round(source_overflow, 2),
                "merged_overflow": round(merged_overflow, 2),
                "distributed": round(overflow_pool - remaining, 2),
                "undistributed": round(max(remaining, 0.0), 2),
                "targets": transfer_steps,
            }
        )

    return working, transfers_log


def finalize_pes_stats(
    player: Dict[str, Any],
    base_projection: Dict[str, float],
    raw_output: Dict[str, float],
) -> Tuple[Dict[str, int], List[Dict[str, Any]]]:
    redistributed_output, overflow_log = redistribute_overflow(player, base_projection, raw_output)
    finalized: Dict[str, int] = {}

    for stat in DIRECT_STATS + SPECIAL_STATS:
        finalized[stat] = clamp(redistributed_output.get(stat))

    finalized["weak_foot_usage"] = clamp(redistributed_output.get("weak_foot_usage"), 1, 4)
    finalized["weak_foot_accuracy"] = clamp(redistributed_output.get("weak_foot_accuracy"), 1, 4)
    finalized["form"] = clamp(redistributed_output.get("form"), 1, 8)
    finalized["injury_resistance"] = clamp(redistributed_output.get("injury_resistance"), 1, 3)
    return apply_high_stat_guardrails(player, finalized), overflow_log


def estimate_confidence(family: str, position: str, neighbors: List[Dict[str, Any]]) -> Tuple[str, float]:
    family_count = DATASET_STATE["family_counts"].get(family, 0)
    position_count = DATASET_STATE.get("position_counts", {}).get(position, 0)

    if not neighbors:
        base = 0.35
    else:
        distances = [safe_float(item.get("distance"), 999.0) for item in neighbors]
        avg_distance = sum(distances) / len(distances)
        nearest_distance = min(distances)
        same_style_ratio = sum(1 for item in neighbors if item.get("same_style")) / len(neighbors)
        same_name_hit = any(item.get("same_name") for item in neighbors)

        if nearest_distance <= 1.0:
            base = 0.90
        else:
            nearest_score = 1.0 / (1.0 + (nearest_distance / 24.0) ** 1.7)
            avg_score = 1.0 / (1.0 + (avg_distance / 42.0) ** 1.5)
            family_score = min(math.log1p(family_count) / math.log1p(80), 1.0)
            position_score = min(math.log1p(position_count) / math.log1p(40), 1.0)
            base = (
                0.38 * nearest_score
                + 0.22 * avg_score
                + 0.16 * family_score
                + 0.12 * position_score
                + 0.07 * same_style_ratio
                + 0.05 * (1.0 if same_name_hit else 0.0)
            )

    base = min(0.97, max(0.28, base))

    if base >= 0.78:
        label = "tinggi"
    elif base >= 0.56:
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

    base_raw = build_base_projection(player, use_clamp=False)
    base = {key: clamp(value) for key, value in base_raw.items()}
    family_delta, profile_notes = resolve_delta_profile(player, family, player["position"])
    knn_delta, neighbors = weighted_neighbor_delta(player, family)
    style_delta, style_notes = find_style_adjustments(player)

    raw_pes_stats = merge_deltas_raw(
        player=player,
        base=base_raw,
        family_delta=family_delta,
        knn_delta=knn_delta,
        style_delta=style_delta,
        family_count=DATASET_STATE.get("family_counts", {}).get(family, 0),
    )
    pes_stats, overflow_log = finalize_pes_stats(player, base_raw, raw_pes_stats)

    confidence_label, confidence_score = estimate_confidence(family, player["position"], neighbors)

    notes = []
    notes.extend(profile_notes)
    notes.extend(style_notes or ["Tidak ada style rule tambahan yang aktif."])
    notes.append("Guardrail high-stat aktif untuk mencegah stat top turun terlalu jauh dari input eFootball.")
    if overflow_log:
        moved_total = round(sum(item.get("distributed", 0.0) for item in overflow_log), 2)
        leftover_total = round(sum(item.get("undistributed", 0.0) for item in overflow_log), 2)
        notes.append(f"Overflow redistribution aktif: {moved_total} poin kelebihan stat >99 dialihkan ke atribut relevan lain, sisa yang tidak punya kapasitas = {leftover_total}.")
    if DATASET_STATE.get("loaded"):
        notes.append(f"Dataset aktif: {len(DATASET_STATE['records'])} record gabungan dari {len(DATASET_STATE.get('paths', []))} file.")

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
            "position_count": DATASET_STATE.get("position_counts", {}).get(player["position"], 0),
            "confidence_label": confidence_label,
            "confidence_score": confidence_score,
        },
        "pes_stats": pes_stats,
        "base_projection_before_adjustment": base,
        "style_adjustments": style_delta,
        "overflow_redistribution": overflow_log,
        "neighbors_used": neighbors,
        "notes": notes,
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
