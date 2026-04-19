import json
import asyncio
import pathlib
import copy
from typing import Dict, Any

class BaseJSONRepository:
    # base repo for async ops w in mem cache
    def __init__(self, file_path: str, default_data: Any):
        self.file_path = pathlib.Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.default_data = default_data
        self._cache = None
        self._lock = asyncio.Lock()

        if not self.file_path.exists():
            self._write_sync(self.default_data)
    
    def _read_sync(self) -> Any:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return self.default_data
        
    def _write_sync(self, data: Any) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    async def read(self) -> Any:
        if self._cache is None:
            self._cache = await asyncio.to_thread(self._read_sync)
        return self._cache
    
    async def write(self, data: Any) -> None:
        self._cache = data
        data_copy = copy.deepcopy(data)
        async with self._lock:
            await asyncio.to_thread(self._write_sync, data_copy)

class StudyRepositories(BaseJSONRepository):
    # timer stats repo
    def __init__(self, file_path: str = "data/study_stats.json"):
        super().__init__(file_path, default_data={})

    async def add_study_time(self, user_id: int, minutes: int) -> None:
        stats = await self.read()
        str_id = str(user_id)

        if str_id not in stats:
            stats[str_id] = {"total_minutes": 0}
        stats[str_id]["total_minutes"] += minutes
        await self.write(stats)

    async def get_study_time(self, user_id: int) -> int:
        stats = await self.read()
        str_id = str(user_id)
        return stats.get(str_id, {}).get("total_minutes", 0)

    