import os
from enum import Enum

from sotapapers.utils.config import load_json, merge_dicts, get_config_from_dict, Config

from icecream import ic
from pathlib import Path

class CrawlMode(Enum):
    KEYWORD_SEARCH = 'keyword_search'
    CONFERENCE_PAPERS = 'conference_papers'

class Settings:
    def __init__(self, config_path: Path):
        # look up all json files in the config_path
        config_jsons = []
        for file in os.listdir(config_path):
            if not file.endswith('.json'):
                continue
            
            config_json = load_json(config_path / file)
            config_jsons.append(config_json)
        
        merged_config_json = merge_dicts(config_jsons)

        # Ensure required config sections exist with default empty dicts if not present
        if merged_config_json is None:
            merged_config_json = {}
        if "database" not in merged_config_json:
            merged_config_json["database"] = {}
        if "llm" not in merged_config_json:
            merged_config_json["llm"] = {"clients": {"llama_cpp": {}}, "prompts": {}}
        elif "clients" not in merged_config_json["llm"]:
            merged_config_json["llm"]["clients"] = {"llama_cpp": {}}
        elif "llama_cpp" not in merged_config_json["llm"]["clients"]:
            merged_config_json["llm"]["clients"]["llama_cpp"] = {}
        elif "prompts" not in merged_config_json["llm"]:
            merged_config_json["llm"]["prompts"] = {}
        if "streamlit_app" not in merged_config_json:
            merged_config_json["streamlit_app"] = {}
            
        self.config = get_config_from_dict(merged_config_json)
        self.mode = CrawlMode.KEYWORD_SEARCH

    def to_dict(self):
        return {
            "config": self.config.to_dict(),
            "mode": self.mode.value
        }

    @classmethod
    def from_dict(cls, settings_dict: dict):
        instance = cls.__new__(cls) # Create a new instance without calling __init__
        config_from_dict = settings_dict.get('config', {})
        instance.config = get_config_from_dict(config_from_dict)
        instance.mode = CrawlMode(settings_dict.get('mode'))
        return instance

    def dump(self):
        ic(self.to_dict())