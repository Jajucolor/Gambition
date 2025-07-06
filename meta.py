import json
from pathlib import Path
from typing import Dict, Any

META_FILE = Path(__file__).with_suffix('').parent / 'save_meta.json'

# Default meta structure
DEFAULT_META: Dict[str, Any] = {
    'runs_played': 0,
    'runs_won': 0,
    'total_gold_earned': 0,
    'permanent_hp_bonus': 0,
    'unlocked_jokers': [],  # list of joker keys permanently unlocked
}


def load_meta() -> Dict[str, Any]:
    if META_FILE.exists():
        try:
            with META_FILE.open('r', encoding='utf-8') as fp:
                return json.load(fp)
        except json.JSONDecodeError:
            print('Corrupted meta file – resetting.')
    return DEFAULT_META.copy()


def save_meta(data: Dict[str, Any]):
    META_FILE.write_text(json.dumps(data, indent=2))


def add_permanent_hp(meta: Dict[str, Any], amount: int):
    meta['permanent_hp_bonus'] += amount


def record_run(meta: Dict[str, Any], won: bool, gold_earned: int):
    meta['runs_played'] += 1
    if won:
        meta['runs_won'] += 1
    meta['total_gold_earned'] += gold_earned 