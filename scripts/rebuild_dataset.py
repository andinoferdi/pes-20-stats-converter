import csv
import html
import http.cookiejar
import json
import math
import re
import sys
import time
import unicodedata
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT_DIR / "dataset" / "pes-20-21-efootball-dataset.csv"
BACKUP_DATASET_PATH = ROOT_DIR / "dataset" / "backup" / "pes-20-21-efootball-dataset-backup.csv"

POSITION_ORDER = ["CF", "SS", "LWF", "RWF", "AMF", "LMF", "CMF", "DMF", "RMF", "LB", "CB", "RB", "GK"]
FAMILY_POSITIONS = {
    "ATTACKER": {"CF", "SS"},
    "WIDE": {"LWF", "RWF", "LMF", "RMF"},
    "MIDFIELDER": {"AMF", "CMF", "DMF"},
    "DEFENDER": {"LB", "CB", "RB"},
    "GOALKEEPER": {"GK"},
}
FAMILY_TARGETS = {family: 95 for family in FAMILY_POSITIONS}
POSITION_CANDIDATE_LIMIT = {
    "CF": 90,
    "SS": 80,
    "LWF": 80,
    "RWF": 80,
    "AMF": 80,
    "LMF": 70,
    "CMF": 80,
    "DMF": 70,
    "RMF": 70,
    "LB": 70,
    "CB": 90,
    "RB": 70,
    "GK": 95,
}
POSITION_PAGE_LIMIT = {
    "CF": 14,
    "SS": 12,
    "LWF": 10,
    "RWF": 10,
    "AMF": 10,
    "LMF": 8,
    "CMF": 10,
    "DMF": 8,
    "RMF": 8,
    "LB": 8,
    "CB": 12,
    "RB": 8,
    "GK": 12,
}
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
PES_STATS_FROM_LEVEL = [
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
    "speed",
    "acceleration",
    "kicking_power",
    "jump",
    "physical_contact",
    "balance",
    "stamina",
    "defensive_awareness",
    "ball_winning",
    "aggression",
    "gk_awareness",
    "gk_catching",
    "gk_clearing",
    "gk_reflexes",
    "gk_reach",
]
PES_HTML_STAT_MAP = {
    "weak_foot_usage": "weak_foot_usage",
    "weak_foot_accuracy": "weak_foot_acc",
    "form": "form",
    "injury_resistance": "injury_resistance",
}
STYLE_NORMALIZATION = {
    "box to box": "Box-to-Box",
    "the destroyer": "The Destroyer",
    "destroyer": "The Destroyer",
    "offensive wingback": "Offensive Full-back",
    "offensive full back": "Offensive Full-back",
    "defensive full back": "Defensive Full-back",
    "fox in the box": "Fox In The Box",
    "deep lying forward": "Deep-Lying Forward",
    "anchor man": "Anchor Man",
    "full back finisher": "Full-back Finisher",
}
CONDITION_BY_INDEX = {0: "E", 1: "D", 2: "C", 3: "B", 4: "A"}


def log(message: str) -> None:
    print(message, flush=True)


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def strip_accents(value: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", value) if not unicodedata.combining(ch))


def normalize_token_text(value: str) -> str:
    cleaned = strip_accents(value or "").lower()
    cleaned = re.sub(r"[^a-z0-9\s-]+", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def short_name_key(value: str) -> str:
    cleaned = normalize_token_text(value).replace("-", " ")
    tokens = [token for token in cleaned.split() if token]
    if not tokens:
        return ""
    first = tokens[0][0]
    rest = tokens[1:] or [tokens[0]]
    return " ".join([first] + rest)


def position_sort_key(position: str) -> Tuple[int, str]:
    try:
        return (POSITION_ORDER.index(position), position)
    except ValueError:
        return (len(POSITION_ORDER), position)


def family_from_position(position: str) -> str:
    for family, positions in FAMILY_POSITIONS.items():
        if position in positions:
            return family
    return "ATTACKER"


def style_key(style: str) -> str:
    return normalize_token_text(style)


def canonical_style(style: str) -> str:
    cleaned = normalize_whitespace(style)
    if not cleaned:
        return ""
    return STYLE_NORMALIZATION.get(style_key(cleaned), cleaned)


def dataset_row_key(row: Dict[str, Any]) -> Tuple[str, str, str]:
    return (
        normalize_token_text(row.get("player_name", "")),
        normalize_whitespace(row.get("pes_screenshot_position", "")).upper(),
        style_key(canonical_style(str(row.get("ef_playing_style", "")))),
    )


def normalize_dataset_row(row: Dict[str, Any], fieldnames: List[str]) -> Dict[str, Any]:
    normalized = {field: row.get(field, "") for field in fieldnames}
    normalized["player_name"] = normalize_whitespace(str(normalized.get("player_name", "")))
    normalized["pes_screenshot_position"] = normalize_whitespace(str(normalized.get("pes_screenshot_position", ""))).upper()
    normalized["ef_screenshot_position"] = normalize_whitespace(str(normalized.get("ef_screenshot_position", ""))).upper()
    normalized_style = canonical_style(str(normalized.get("ef_playing_style", "")))
    normalized["ef_playing_style"] = normalized_style
    position = normalized["pes_screenshot_position"]
    if normalized_style and position:
        normalized["archetype"] = f"{normalized_style} {position}"
    return normalized


def load_dataset_rows(path: Path, fieldnames: List[str]) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [normalize_dataset_row(dict(row), fieldnames) for row in reader]


def load_fieldnames() -> List[str]:
    with DATASET_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        return next(csv.reader(handle))


def make_request(url: str, opener: urllib.request.OpenerDirector | None = None) -> str:
    req = urllib.request.Request(url, headers=REQUEST_HEADERS)
    opener = opener or urllib.request.build_opener()
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with opener.open(req, timeout=45) as response:
                return response.read().decode("utf-8", "ignore")
        except Exception as exc:
            last_error = exc
            time.sleep(0.6 * (attempt + 1))
    raise RuntimeError(f"Gagal fetch {url}: {last_error}")


def json_request(url: str, opener: urllib.request.OpenerDirector | None = None) -> Any:
    return json.loads(make_request(url, opener=opener))


def extract_int(value: Any, default: int = 0) -> int:
    match = re.search(r"-?\d+", str(value or ""))
    return int(match.group(0)) if match else default


def extract_between(value: str, start_marker: str, end_marker: str) -> str:
    start = value.find(start_marker)
    if start == -1:
        return ""
    start += len(start_marker)
    end = value.find(end_marker, start)
    if end == -1:
        return ""
    return value[start:end]


def html_unescape_strip(value: str) -> str:
    return normalize_whitespace(re.sub(r"<[^>]+>", " ", html.unescape(value)))


def parse_pes_search_rows_2020(page_html: str) -> Tuple[int, List[Dict[str, Any]]]:
    count_match = re.search(r'id="search-count">(\d+)</span>', page_html)
    total_count = int(count_match.group(1)) if count_match else 0
    tbody = extract_between(page_html, "<tbody>", "</tbody>")
    rows: List[Dict[str, Any]] = []
    for chunk in re.findall(r"<tr id=\"table-row-\d+\">(.*?)</tr>", tbody, re.S):
        href_match = re.search(r'<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>', chunk)
        age_match = re.search(r'squad-table-age[^>]*>(\d+)<', chunk)
        height_match = re.search(r'squad-table-height[^>]*>(\d+)<', chunk)
        pos_match = re.search(r'squad-table-pos[^>]*><span[^>]*title="([^"]+)">([A-Z]+)', chunk)
        ovr_match = re.search(r'squad-table-stat-col[^>]*><span[^>]*>(\d+)</span>', chunk)
        if not href_match or not pos_match or not ovr_match:
            continue
        rows.append(
            {
                "name": html_unescape_strip(href_match.group(2)),
                "url": "https://www.pesmaster.com" + href_match.group(1),
                "age": extract_int(age_match.group(1) if age_match else ""),
                "height_cm": extract_int(height_match.group(1) if height_match else ""),
                "position": pos_match.group(2).strip(),
                "position_long": html_unescape_strip(pos_match.group(1)),
                "ovr": extract_int(ovr_match.group(1)),
            }
        )
    return total_count, rows


def fetch_pes_rows_2020() -> List[Dict[str, Any]]:
    log("Scrape list PES 2020 per posisi...")
    rows: List[Dict[str, Any]] = []
    for position in POSITION_ORDER:
        pos_id = POSITION_ORDER.index(position)
        max_pages = POSITION_PAGE_LIMIT[position]
        collected = 0
        for page in range(1, max_pages + 1):
            url = (
                "https://www.pesmaster.com/pes-2020/search/search.php"
                f"?myclub=yes&sort=ovr&sort_order=desc&pos={pos_id}&page={page}"
            )
            _, page_rows = parse_pes_search_rows_2020(make_request(url))
            rows.extend(page_rows)
            collected += len(page_rows)
            if not page_rows:
                break
        log(f"PES 2020 {position}: {collected} rows")
    return rows


def fetch_pes_rows_2021() -> List[Dict[str, Any]]:
    log("Scrape list PES 2021 per posisi...")
    rows: List[Dict[str, Any]] = []
    for position in POSITION_ORDER:
        pos_id = POSITION_ORDER.index(position)
        max_pages = POSITION_PAGE_LIMIT[position]
        collected = 0
        for page in range(1, max_pages + 1):
            url = f"https://www.pesmaster.com/pes-2021/search/api.php?game=2021&myclub=yes&pos={pos_id}&page={page}"
            payload = json_request(url)
            page_rows = []
            for item in payload.get("data", []):
                page_rows.append(
                    {
                        "name": normalize_whitespace(item.get("name_display") or item.get("name") or ""),
                        "url": "https://www.pesmaster.com" + str(item.get("url") or ""),
                        "age": extract_int(item.get("age")),
                        "height_cm": extract_int(item.get("height")),
                        "position": normalize_whitespace(item.get("pos") or ""),
                        "position_long": normalize_whitespace(item.get("pos_name") or ""),
                        "ovr": extract_int(item.get("ovr")),
                    }
                )
            rows.extend(page_rows)
            collected += len(page_rows)
            if not page_rows:
                break
        log(f"PES 2021 {position}: {collected} rows")
    return rows


def collapse_pes_rows(rows: Iterable[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[Tuple[str, str, int, int], Dict[str, Any]] = {}
    for row in rows:
        key = (short_name_key(row["name"]), row["position"], int(row["age"]), int(row["height_cm"]))
        best = grouped.get(key)
        if best is None or row["ovr"] > best["ovr"]:
            grouped[key] = dict(row)
    output: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in grouped.values():
        output[short_name_key(item["name"])].append(item)
    for bucket in output.values():
        bucket.sort(key=lambda item: (-item["ovr"], position_sort_key(item["position"]), item["name"]))
    return output


def pair_year_records(
    rows_2020: Dict[str, List[Dict[str, Any]]],
    rows_2021: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    log("Pairing PES 2020 dan PES 2021...")
    candidates: List[Dict[str, Any]] = []
    for short_key_value in sorted(set(rows_2020) & set(rows_2021)):
        left = rows_2020[short_key_value]
        right = rows_2021[short_key_value]
        used_right: set[int] = set()
        for left_item in left:
            best_index = -1
            best_score = -10_000
            for idx, right_item in enumerate(right):
                if idx in used_right:
                    continue
                score = 0
                if left_item["position"] == right_item["position"]:
                    score += 40
                elif family_from_position(left_item["position"]) == family_from_position(right_item["position"]):
                    score += 20
                score -= abs(left_item["height_cm"] - right_item["height_cm"]) * 4
                score -= abs(left_item["age"] - right_item["age"]) * 5
                score += min(left_item["ovr"], right_item["ovr"])
                if score > best_score:
                    best_score = score
                    best_index = idx
            if best_index == -1 or best_score < 50:
                continue
            used_right.add(best_index)
            right_item = right[best_index]
            canonical_year = "2021" if right_item["ovr"] >= left_item["ovr"] else "2020"
            canonical_position = right_item["position"] if canonical_year == "2021" else left_item["position"]
            candidates.append(
                {
                    "short_key": short_key_value,
                    "pes_2020": left_item,
                    "pes_2021": right_item,
                    "canonical_position": canonical_position,
                    "family": family_from_position(canonical_position),
                    "pair_score": best_score,
                }
            )
    log(f"Paired candidates: {len(candidates)}")
    return candidates


def build_efhub_opener() -> urllib.request.OpenerDirector:
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    opener.addheaders = list(REQUEST_HEADERS.items())
    opener.open("https://efhub.com/players", timeout=45).read()
    return opener


def fetch_efhub_index(opener: urllib.request.OpenerDirector) -> Dict[str, List[Dict[str, Any]]]:
    log("Scrape index eFHUB...")
    payload = json_request("https://efhub.com/search/player-index.json", opener=opener)
    buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in payload:
        full_name = normalize_whitespace(item.get("e") or "")
        short_key_value = short_name_key(full_name)
        if not short_key_value:
            continue
        buckets[short_key_value].append(
            {
                "id": str(item.get("i")),
                "name": full_name,
                "max_overall": extract_int(item.get("o")),
            }
        )
    for bucket in buckets.values():
        bucket.sort(key=lambda item: (-item["max_overall"], item["name"], item["id"]))
    log(f"eFHUB indexed names: {len(buckets)}")
    return buckets


def preselect_candidates(
    paired_candidates: List[Dict[str, Any]],
    efhub_buckets: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    by_position: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in paired_candidates:
        efhub_candidates = efhub_buckets.get(item["short_key"], [])
        if not efhub_candidates:
            continue
        enriched = dict(item)
        enriched["efhub_candidates"] = efhub_candidates[:5]
        enriched["efhub_max_overall"] = efhub_candidates[0]["max_overall"]
        by_position[item["canonical_position"]].append(enriched)

    selected: List[Dict[str, Any]] = []
    for position in POSITION_ORDER:
        pool = by_position.get(position, [])
        pool.sort(
            key=lambda item: (
                -max(item["pes_2020"]["ovr"], item["pes_2021"]["ovr"]),
                -item["efhub_max_overall"],
                -item["pair_score"],
                item["short_key"],
            )
        )
        limit = POSITION_CANDIDATE_LIMIT[position]
        selected.extend(pool[:limit])
        log(f"Preselect {position}: {min(limit, len(pool))}/{len(pool)}")
    return selected


def extract_pes_level_stats(page_html: str) -> Dict[str, Any]:
    match = re.search(r"const levelStats = (\[.*?\]);", page_html, re.S)
    if not match:
        raise RuntimeError("levelStats PES tidak ditemukan")
    level_stats = json.loads(match.group(1))
    return level_stats[-1]


def extract_pes_meta(page_html: str) -> Dict[str, str]:
    rows = dict(re.findall(r"<tr>\s*<td>([^<]+)</td>\s*<td>(.*?)</td>\s*</tr>", page_html, re.S))
    meta: Dict[str, str] = {}
    for key, value in rows.items():
        meta[normalize_whitespace(key)] = html_unescape_strip(value)
    return meta


def parse_pes_detail(url: str, cache: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    if url in cache:
        return cache[url]
    page_html = make_request(url)
    title_match = re.search(r"<title>(.*?) PES \d{4} Stats</title>", page_html, re.S)
    if not title_match:
        raise RuntimeError(f"Title PES tidak ditemukan: {url}")
    full_name = html_unescape_strip(title_match.group(1))
    max_stats = extract_pes_level_stats(page_html)
    meta = extract_pes_meta(page_html)
    result = {
        "player_name": full_name,
        "position": normalize_whitespace(meta.get("Position", "").split()[0]),
        "age": extract_int(meta.get("Age")),
        "height_cm": extract_int(meta.get("Height (cm)")),
        "weight_kg": extract_int(meta.get("Weight")),
        "foot": normalize_whitespace(meta.get("Stronger Foot")),
        "condition": normalize_whitespace(meta.get("Condition")),
        "ovr": extract_int(max_stats.get("ovr")),
        "stats": {},
        "url": url,
    }
    for stat in PES_STATS_FROM_LEVEL:
        result["stats"][stat] = extract_int(max_stats.get(stat))
    for field, html_class in PES_HTML_STAT_MAP.items():
        stat_match = re.search(rf"<span class='{re.escape(html_class)}'>(\d+)</span>", page_html, re.S)
        result["stats"][field] = extract_int(stat_match.group(1) if stat_match else 0)
    cache[url] = result
    return result


def parse_efhub_detail(
    player_id: str,
    max_overall: int,
    opener: urllib.request.OpenerDirector,
    cache: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    cache_key = f"{player_id}:{max_overall}"
    if cache_key in cache:
        return cache[cache_key]

    page_html = make_request(f"https://efhub.com/players/{player_id}", opener=opener)
    base_patterns = [
        r'baseStats\\\\\\":(\{.*?\}),\\\\\\\"position\\\\\\":',
        r'baseStats\\\":(\{.*?\}),\\\"position\\\":',
    ]
    player_patterns = [
        r'\\\\\\\"player\\\\\\\":(\{.*?\\\\\\\"levelCap\\\\\\\":\d+\})',
        r'\\\"player\\\":(\{.*?\\\"levelCap\\\":\d+\})',
    ]
    base_match = None
    player_match = None
    for pattern in base_patterns:
        base_match = re.search(pattern, page_html, re.S)
        if base_match:
            break
    for pattern in player_patterns:
        player_match = re.search(pattern, page_html, re.S)
        if player_match:
            break
    if not base_match or not player_match:
        raise RuntimeError(f"Payload eFHUB tidak lengkap: {player_id}")

    base_stats = json.loads(base_match.group(1).replace('\\"', '"'))
    player_json = player_match.group(1).replace('\\"', '"').replace("\\/", "/")
    player_json = re.sub(r'"additionalPositions":"\$[^"]+"', '"additionalPositions":[]', player_json)
    player_json = re.sub(r'"stats":"\$[^"]+"', '"stats":{}', player_json)
    player = json.loads(player_json)

    detail = {
        "player_name": normalize_whitespace(player.get("name") or ""),
        "position": normalize_whitespace(player.get("position") or ""),
        "playing_style": canonical_style(normalize_whitespace(player.get("playingStyle") or "")),
        "current_overall": extract_int(player.get("overallRating")),
        "max_overall": max_overall,
        "age": extract_int(player.get("age")),
        "height_cm": extract_int(player.get("height")),
        "weight_kg": extract_int(player.get("weight")),
        "foot": normalize_whitespace(player.get("preferredFoot") or ""),
        "condition": CONDITION_BY_INDEX.get(extract_int(player.get("condition")), "C"),
        "stats": {
            "ef_offensive_awareness": extract_int(base_stats.get("offensiveAwareness")),
            "ef_ball_control": extract_int(base_stats.get("ballControl")),
            "ef_dribbling": extract_int(base_stats.get("dribbling")),
            "ef_tight_possession": extract_int(base_stats.get("tightPossession")),
            "ef_low_pass": extract_int(base_stats.get("lowPass")),
            "ef_lofted_pass": extract_int(base_stats.get("loftedPass")),
            "ef_finishing": extract_int(base_stats.get("finishing")),
            "ef_heading": extract_int(base_stats.get("heading")),
            "ef_place_kicking": extract_int(base_stats.get("setPieceTaking")),
            "ef_curl": extract_int(base_stats.get("curl")),
            "ef_defensive_awareness": extract_int(base_stats.get("defensiveAwareness")),
            "ef_defensive_engagement": extract_int(base_stats.get("trackingBack")),
            "ef_tackling": extract_int(base_stats.get("ballWinning")),
            "ef_aggression": extract_int(base_stats.get("aggression")),
            "ef_goalkeeping": extract_int(base_stats.get("gkAwareness")),
            "ef_gk_catching": extract_int(base_stats.get("gkCatching")),
            "ef_gk_parrying": extract_int(base_stats.get("gkClearing")),
            "ef_gk_reflexes": extract_int(base_stats.get("gkReflexes")),
            "ef_gk_reach": extract_int(base_stats.get("gkReach")),
            "ef_speed": extract_int(base_stats.get("speed")),
            "ef_acceleration": extract_int(base_stats.get("acceleration")),
            "ef_kicking_power": extract_int(base_stats.get("kickingPower")),
            "ef_jump": extract_int(base_stats.get("jump")),
            "ef_physical": extract_int(base_stats.get("physicalContact")),
            "ef_balance": extract_int(base_stats.get("balance")),
            "ef_stamina": extract_int(base_stats.get("stamina")),
        },
        "booster_1": "",
        "booster_2": "",
        "id": player_id,
    }
    cache[cache_key] = detail
    return detail


def is_valid_efhub_match(pes_detail: Dict[str, Any], efhub_detail: Dict[str, Any]) -> bool:
    if short_name_key(pes_detail["player_name"]) != short_name_key(efhub_detail["player_name"]):
        return False
    if abs(int(pes_detail["height_cm"]) - int(efhub_detail["height_cm"])) > 4:
        return False
    pes_family = family_from_position(pes_detail["position"])
    efhub_family = family_from_position(efhub_detail["position"])
    if pes_family != efhub_family and pes_detail["position"] != efhub_detail["position"]:
        return False
    if pes_detail.get("foot") and efhub_detail.get("foot") and pes_detail["foot"][:1].lower() != efhub_detail["foot"][:1].lower():
        return False
    return True


def validate_candidates(
    candidates: List[Dict[str, Any]],
    efhub_opener: urllib.request.OpenerDirector,
) -> List[Dict[str, Any]]:
    log("Fetch detail pemain yang lolos preselect...")
    pes_cache: Dict[str, Dict[str, Any]] = {}
    efhub_cache: Dict[str, Dict[str, Any]] = {}
    validated: List[Dict[str, Any]] = []
    total = len(candidates)

    for index, candidate in enumerate(candidates, start=1):
        try:
            pes_2020 = parse_pes_detail(candidate["pes_2020"]["url"], pes_cache)
            pes_2021 = parse_pes_detail(candidate["pes_2021"]["url"], pes_cache)
        except Exception:
            continue
        if short_name_key(pes_2020["player_name"]) != short_name_key(pes_2021["player_name"]):
            continue
        if abs(pes_2020["height_cm"] - pes_2021["height_cm"]) > 4:
            continue

        canonical_pes = pes_2021 if pes_2021["ovr"] >= pes_2020["ovr"] else pes_2020
        efhub_detail = None
        for efhub_candidate in candidate["efhub_candidates"]:
            try:
                detail = parse_efhub_detail(efhub_candidate["id"], efhub_candidate["max_overall"], efhub_opener, efhub_cache)
            except Exception:
                continue
            if is_valid_efhub_match(canonical_pes, detail):
                efhub_detail = detail
                break
        if not efhub_detail:
            continue

        validated.append(
            {
                "player_name": canonical_pes["player_name"],
                "pes_2020": pes_2020,
                "pes_2021": pes_2021,
                "pes": canonical_pes,
                "efhub": efhub_detail,
                "position": canonical_pes["position"],
                "family": family_from_position(canonical_pes["position"]),
                "playing_style": canonical_style(efhub_detail["playing_style"]),
                "combined_ovr": canonical_pes["ovr"] + efhub_detail["max_overall"],
            }
        )
        if index % 50 == 0 or index == total:
            log(f"Validated {len(validated)} / processed {index}/{total}")

    log(f"Validated clean candidates: {len(validated)}")
    return validated


def select_family_records(validated: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    log("Seleksi final per family dengan prioritas posisi dan playing style...")
    by_family: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in validated:
        by_family[item["family"]].append(item)

    selected: List[Dict[str, Any]] = []
    for family, target in FAMILY_TARGETS.items():
        pool = by_family.get(family, [])
        pool.sort(key=lambda item: (-item["combined_ovr"], position_sort_key(item["position"]), item["player_name"]))
        selected_keys: set[Tuple[str, str, str]] = set()
        style_counts: Counter[str] = Counter()
        position_counts: Counter[str] = Counter()
        family_selected: List[Dict[str, Any]] = []

        while pool and len(family_selected) < target:
            best_idx = -1
            best_score = -10_000.0
            for idx, item in enumerate(pool):
                dedupe_key = (normalize_token_text(item["player_name"]), item["position"], style_key(item["playing_style"]))
                if dedupe_key in selected_keys:
                    continue
                score = 0.0
                if position_counts[item["position"]] == 0:
                    score += 80.0
                if style_counts[item["playing_style"]] == 0:
                    score += 60.0
                score += 18.0 / (1 + position_counts[item["position"]])
                score += 16.0 / (1 + style_counts[item["playing_style"]])
                score += item["combined_ovr"] * 0.25
                score += item["efhub"]["max_overall"] * 0.15
                if score > best_score:
                    best_score = score
                    best_idx = idx
            if best_idx == -1:
                break
            chosen = pool.pop(best_idx)
            dedupe_key = (normalize_token_text(chosen["player_name"]), chosen["position"], style_key(chosen["playing_style"]))
            selected_keys.add(dedupe_key)
            position_counts[chosen["position"]] += 1
            style_counts[chosen["playing_style"]] += 1
            family_selected.append(chosen)

        selected.extend(family_selected)
        log(f"{family}: {len(family_selected)} selected")
    return selected


def build_csv_row(record: Dict[str, Any], fieldnames: List[str]) -> Dict[str, Any]:
    pes = record["pes"]
    efhub = record["efhub"]
    row = {field: "" for field in fieldnames}
    row["player_name"] = record["player_name"]
    row["archetype"] = f"{record['playing_style']} {record['position']}".strip()
    row["data_origin"] = "scraped from PES Master 2020 + PES Master 2021 + eFHUB Smart max"
    row["pes_public_base_ovr"] = pes["ovr"]
    row["ef_public_base_ovr"] = efhub["max_overall"]
    row["pes_screenshot_ovr"] = pes["ovr"]
    row["pes_screenshot_position"] = record["position"]
    row["pes_age"] = pes["age"]
    row["pes_height_cm"] = pes["height_cm"]
    row["pes_weight_kg"] = pes["weight_kg"]
    row["pes_offensive_awareness"] = pes["stats"]["offensive_awareness"]
    row["pes_finishing"] = pes["stats"]["finishing"]
    row["pes_kicking_power"] = pes["stats"]["kicking_power"]
    row["pes_weak_foot_usage"] = pes["stats"]["weak_foot_usage"]
    row["pes_weak_foot_accuracy"] = pes["stats"]["weak_foot_accuracy"]
    row["pes_ball_control"] = pes["stats"]["ball_control"]
    row["pes_dribbling"] = pes["stats"]["dribbling"]
    row["pes_tight_possession"] = pes["stats"]["tight_possession"]
    row["pes_balance"] = pes["stats"]["balance"]
    row["pes_low_pass"] = pes["stats"]["low_pass"]
    row["pes_lofted_pass"] = pes["stats"]["lofted_pass"]
    row["pes_place_kicking"] = pes["stats"]["place_kicking"]
    row["pes_curl"] = pes["stats"]["curl"]
    row["pes_heading"] = pes["stats"]["heading"]
    row["pes_jump"] = pes["stats"]["jump"]
    row["pes_defensive_awareness"] = pes["stats"]["defensive_awareness"]
    row["pes_ball_winning"] = pes["stats"]["ball_winning"]
    row["pes_aggression"] = pes["stats"]["aggression"]
    row["pes_speed"] = pes["stats"]["speed"]
    row["pes_acceleration"] = pes["stats"]["acceleration"]
    row["pes_physical_contact"] = pes["stats"]["physical_contact"]
    row["pes_stamina"] = pes["stats"]["stamina"]
    row["pes_form"] = pes["stats"]["form"]
    row["pes_injury_resistance"] = pes["stats"]["injury_resistance"]
    row["pes_gk_awareness"] = pes["stats"]["gk_awareness"]
    row["pes_gk_catching"] = pes["stats"]["gk_catching"]
    row["pes_gk_clearing"] = pes["stats"]["gk_clearing"]
    row["pes_gk_reflexes"] = pes["stats"]["gk_reflexes"]
    row["pes_gk_reach"] = pes["stats"]["gk_reach"]
    row["ef_screenshot_ovr"] = efhub["max_overall"]
    row["ef_screenshot_position"] = efhub["position"]
    row["ef_playing_style"] = record["playing_style"]
    row["ef_booster_1"] = efhub["booster_1"]
    row["ef_booster_2"] = efhub["booster_2"]
    row["ef_age"] = efhub["age"]
    row["ef_height_cm"] = efhub["height_cm"]
    row["ef_weight_kg"] = efhub["weight_kg"]
    row["ef_foot"] = efhub["foot"]
    row["ef_condition"] = efhub["condition"]
    for key, value in efhub["stats"].items():
        row[key] = value
    return row


def write_dataset(rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    rows.sort(key=lambda row: (position_sort_key(row["pes_screenshot_position"]), normalize_token_text(row["player_name"])))
    with DATASET_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize_rows(rows: List[Dict[str, Any]]) -> None:
    family_counts = Counter(family_from_position(row["pes_screenshot_position"]) for row in rows)
    position_counts = Counter(row["pes_screenshot_position"] for row in rows)
    style_counts = Counter(row["ef_playing_style"] for row in rows)
    log("Ringkasan final:")
    log("Family counts: " + ", ".join(f"{family} {family_counts.get(family, 0)}" for family in FAMILY_TARGETS))
    log("Position counts: " + ", ".join(f"{pos} {position_counts.get(pos, 0)}" for pos in POSITION_ORDER if position_counts.get(pos, 0)))
    log("Top styles: " + ", ".join(f"{style} {count}" for style, count in style_counts.most_common(12)))


def merge_backup_into_dataset() -> int:
    fieldnames = load_fieldnames()
    active_rows = load_dataset_rows(DATASET_PATH, fieldnames)
    backup_rows = load_dataset_rows(BACKUP_DATASET_PATH, fieldnames)

    merged_rows = list(active_rows)
    active_keys = {dataset_row_key(row) for row in active_rows}
    missing_backup_rows: List[Dict[str, Any]] = []
    for row in backup_rows:
        if dataset_row_key(row) not in active_keys:
            missing_backup_rows.append(row)

    added_count = 0
    for row in missing_backup_rows:
        row_key = dataset_row_key(row)
        if row_key in active_keys:
            continue
        merged_rows.append(row)
        active_keys.add(row_key)
        added_count += 1

    write_dataset(merged_rows, fieldnames)
    log(f"Active rows: {len(active_rows)}")
    log(f"Backup rows: {len(backup_rows)}")
    log(f"Missing backup rows before normalized merge: {len(missing_backup_rows)}")
    log(f"Rows added after normalized merge: {added_count}")
    summarize_rows(merged_rows)
    log(f"Dataset merge selesai ke {DATASET_PATH}")
    return 0


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "merge-backup":
        return merge_backup_into_dataset()

    fieldnames = load_fieldnames()
    efhub_opener = build_efhub_opener()

    rows_2020 = fetch_pes_rows_2020()
    rows_2021 = fetch_pes_rows_2021()
    paired = pair_year_records(collapse_pes_rows(rows_2020), collapse_pes_rows(rows_2021))
    efhub_buckets = fetch_efhub_index(efhub_opener)
    preselected = preselect_candidates(paired, efhub_buckets)
    validated = validate_candidates(preselected, efhub_opener)
    final_records = select_family_records(validated)
    output_rows = [build_csv_row(record, fieldnames) for record in final_records]
    write_dataset(output_rows, fieldnames)
    summarize_rows(output_rows)
    log(f"Dataset ditulis ulang ke {DATASET_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
