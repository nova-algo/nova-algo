import ujson
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class BlacklistManager:
    def __init__(self):
        self.pools: List[str] = []
        self.tokens: List[str] = []
        self.arbs: List[str] = []
        
    def load_blacklists(self, data_dir: Path = Path(".")) -> None:
        """Load all blacklist data from JSON files"""
        self.pools = self._load_blacklist(data_dir / "ethereum_blacklisted_pools.json")
        self.tokens = self._load_blacklist(data_dir / "ethereum_blacklisted_tokens.json")
        self.arbs = self._load_blacklist(data_dir / "ethereum_blacklisted_arbs.json")
        
        logger.info(f"Loaded blacklists: {len(self.pools)} pools, "
                   f"{len(self.tokens)} tokens, {len(self.arbs)} arbs")

    def _load_blacklist(self, filename: Path) -> List[str]:
        """Load a single blacklist file"""
        try:
            with open(filename, encoding="utf-8") as f:
                data = ujson.load(f)
            return data
        except FileNotFoundError:
            with open(filename, "w", encoding="utf-8") as f:
                ujson.dump([], f, indent=2)
            return []

    def is_pool_blacklisted(self, pool_address: str) -> bool:
        return pool_address in self.pools

    def is_token_blacklisted(self, token_address: str) -> bool:
        return token_address in self.tokens

    def is_arb_blacklisted(self, arb_id: str) -> bool:
        return arb_id in self.arbs 