from dataclasses import dataclass
from pathlib import Path

@dataclass
class FetcherConfig:
    force_update: bool = False
    max_concurrent_requests: int = 10
    max_workers: int = 4
    assets_path: Path = Path(__file__).parent.parent.parent / 'assets'
    rate_limit_delay: int = 2  # seconds