import json

from pathlib import Path
from typing import List, Optional
from python_json_config import ConfigBuilder, Config

def load_json(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def merge_dicts(dicts: List[dict]) -> Optional[dict]:
    if len(dicts) == 0:
        return None
    
    base_dict = dicts[0]
    if len(dicts) == 1:
        return base_dict
    
    for additional_dict in dicts[1:]:
        for key, value in additional_dict.items():
            if isinstance(value, dict) and key in base_dict:
                base_dict[key] = merge_dicts(base_dict[key], value)
            else:
                base_dict[key] = value
    return base_dict

def get_config_path() -> Path:
    return Path(__file__).parent.parent / 'configs'

def get_config_from_dict(config_dict: dict) -> Config:
    return ConfigBuilder().parse_config(config_dict)