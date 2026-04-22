import json
import asyncio
import pathlib
import copy
import time
import os
from typing import Any

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

class StudyRepository(BaseJSONRepository):
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

class TriviaRepository(BaseJSONRepository):
    # repo for managing trvia scores
    def __init__(self, file_path: str = "data/trivia_scores.json"):
        super().__init__(file_path, default_data={})

    async def add_score(self, guild_id: int, user_id: int, points: int) -> None:
        scores = await self.read()
        str_guild = str(guild_id)
        str_user = str(user_id)

        scores.setdefault(str_guild, {}).setdefault(str_user, 0)
        scores[str_guild][str_user] += points
        await self.write(scores)

    async def get_guild_scores(self, guild_id: int) -> dict[str, int]:
        scores = await self.read()
        str_guild = str(guild_id)
        return scores.get(str_guild, {})
    
class LevelingRepository(BaseJSONRepository):
    # xp and levels
    def __init__(self, file_path: str = "data/xp_stats.json"):
        super().__init__(file_path, default_data={})

    async def add_xp(self, guild_id: int, user_id: int, xp: int)-> None:
        stats = await self.read()
        str_guild = str(guild_id)
        str_user = str(user_id)

        stats.setdefault(str_guild, {}).setdefault(str_user, 0)
        stats[str_guild][str_user] += xp
        await self.write(stats)

    async def get_xp(self, guild_id: int, user_id: int) -> int:
        stats = await self.read()
        str_guild = str(guild_id)
        str_user = str(user_id)
        return stats.get(str_guild, {}).get(str_user, 0)
    
    async def get_all_xp(self, guild_id: int) -> dict[str, int]:
        stats = await self.read()
        str_guild = str(guild_id)
        return stats.get(str_guild, {})
    
    async def set_boost(self, guild_id: int, user_id: int, multiplier: float, duration_seconds: int) -> None:
        data = await self.read()
        pass
    
class ModerationRepository(BaseJSONRepository):
    # mod specific stuffs
    def __init__(self, file_path: str = "data/automod_settings.json"):
        super().__init__(file_path, default_data = {})

    async def add_banned_word(self, guild_id: int, word: str) -> None:
        data = await self.read()
        str_guild = str(guild_id)

        data.setdefault(str_guild, [])
        word_lower = word.lower()
        if word_lower not in data[str_guild]:
            data[str_guild].append(word_lower)
            await self.write(data)

    async def remove_banned_word(self, guild_id: int, word: str) -> None:
        data = await self.read()
        str_guild = str(guild_id)

        if str_guild in data:
            word_lower = word.lower()
            if word_lower in data[str_guild]:
                data[str_guild].remove(word_lower)
                await self.write(data)

    async def get_banned_words(self, guild_id: int) -> list[str]:
        data = await self.read()
        str_guild = str(guild_id)
        return data.get(str_guild, [])
    
class CustomTriviaRepository(BaseJSONRepository):
    # custom questions
    def __init__(self, file_path: str = "data/custom_trivia.json"):
        super().__init__(file_path, default_data={})

    async def add_question(self, guild_id: int, question: str, correct_answer: str, incorrect_answers: list[str], author_id: int) -> None:
        data = await self.read()
        str_guild = str(guild_id)

        data.setdefault(str_guild, [])
        data[str_guild].append({
            "question":question,
            "correct_answer":correct_answer,
            "incorrect_answers":incorrect_answers,
            "author_id": author_id
        })
        await self.write(data)

    async def get_questions(self, guild_id: int) -> list[dict[str, Any]]:
        data = await self.read()
        str_guild = str(guild_id)
        return data.get(str_guild, [])
    
class EconomyRepository(BaseJSONRepository):
    def __init__(self, file_path : str = "data/economy.json"):
        super().__init__(file_path, default_data={})
    
    async def get_balance(self, guild_id: int, user_id: int) -> int:
        data = await self.read()
        str_guild = str(guild_id)
        str_user = str(user_id)
        return data.get(str_guild, {}).get(str_user, {}).get("balance", 0)
    
    async def add_balance(self, guild_id: int, user_id: int, amount: int) -> int:
        data = await self.read()
        str_guild = str(guild_id)
        str_user = str(user_id)

        data.setdefault(str_guild, {}).setdefault(str_user, {"balance": 0, "last_daily": 0, "last_message": 0})
        data[str_guild][str_user]["balance"] += amount
        await self.write(data)
        return data[str_guild][str_user]["balance"]
    
    async def set_cooldown(self, guild_id: int, user_id: int, cooldown_type: str, timestamp: float) -> None:
        data = await self.read()
        str_guild = str(guild_id)
        str_user = str(user_id)

        data.setdefault(str_guild, {}).setdefault(str_user, {"balance": 0, "last_daily":0, "last_message":0})
        data[str_guild][str_user][f"last_{cooldown_type}"] = timestamp
        await self.write(data)

    async def get_cooldown(self, guild_id: int, user_id: int, cooldown_type: str) -> float:
        data = await self.read()
        str_guild = str(guild_id)
        str_user = str(user_id)
        return data.get(str_guild, {}).get(str_user, {}).get(f"last_{cooldown_type}", 0)
    
class SettingsRepository(BaseJSONRepository):
    def __init__(self, file_path: str = "data/settings.json"):
        super().__init__(file_path, default_data={})

    async def set_setting(self, guild_id: int, key: str, value: Any) -> None:
        data = await self.read()
        str_guild = str(guild_id)
        data.setdefault(str_guild, {})[key] = value
        await self.write(data)

    async def get_setting(self, guild_id: int, key: str, default: Any = None) -> Any:
        data = await self.read()
        str_guild = str(guild_id)
        return data.get(str_guild, {}).get(key, default)
    
    async def add_role_reward(self, guild_id: int, level: int, role_id: int) -> None:
        rewards = await self.get_setting(guild_id, "role_rewards", {})
        rewards[str(level)] = role_id
        await self.set_setting(guild_id, "role_rewards", rewards)

    async def get_role_rewards(self, guild_id: int) -> dict[str, int]:
        return await self.get_setting(guild_id, "role_rewards", {})
    
class BoostRepository(BaseJSONRepository):
    def __init__(self, file_path: str = "data/boosts.json"):
        super().__init__(file_path, default_data={})

    async def add_boost(self, guild_id: int, user_id: int, boost_type: str, multiplier: float, end_time: float) -> None:
        data = await self.read()
        str_guild = str(guild_id)
        str_user = str(user_id)

        data.setdefault(str_guild, {}).setdefault(str_user, {}).setdefault(boost_type, [])
        data[str_guild][str_user][boost_type].append({
            "multiplier": multiplier,
            "end_time": end_time
        })
        await self.write(data)

    async def get_active_multiplier(self, guild_id: int, user_id: int, boost_type: str) -> float:
        data = await self.read()
        str_guild = str(guild_id)
        str_user = str(user_id)
        current_time = time.time()

        boosts = data.get(str_guild, {}).get(str_user, {}).get(boost_type, [])
        if not boosts:
            return 1.0
        
        total_multiplier = 1.0
        active_boosts = []
        for boost in boosts:
            if boost["end_time"] > current_time:
                total_multiplier *= boost["multiplier"]
                active_boosts.append(boost)

        if len(active_boosts) != len(boosts):
            data[str_guild][str_user][boost_type] = active_boosts
            await self.write(data)

        return total_multiplier
    
class TaskRepository(BaseJSONRepository):
    def __init__(self, file_path: str = "data/tasks.json"):
        super().__init__(file_path, default_data={})

    async def add_task(self, user_id: int, content: str, due_time: float | None = None) -> int:
        data = await self.read()
        str_user = str(user_id)

        data.setdefault(str_user, [])
        task_id = len(data[str_user]) + 1
        data[str_user].append({
            "id": task_id,
            "content": content,
            "due_time": due_time,
            "completed": False,
            "created_at": time.time()
        })
        await self.write(data)
        return task_id
    
    async def get_tasks(self, user_id: int, include_completed: bool = False) -> list[dict[str, Any]]:
        data = await self.read()
        str_user = str(user_id)
        tasks = data.get(str_user, [])
        if not include_completed:
            return [t for t in tasks if not t["completed"]]
        return tasks
    
    async def complete_task(self, user_id: int, task_id: int) -> bool:
        data = await self.read()
        str_user = str(user_id)
        tasks = data.get[str_user, []]
        for task in tasks:
            if task["id"] == task_id:
                task["completed"] = True
                await self.write(data)
                return True
            return False
        
    async def get_all_due_tasks(self) -> list[dict[str, Any]]:
        data = await self.read()
        current_time = time.time()
        due_tasks = []
        for user_id_str, tasks in data.items():
            for task in tasks:
                if not task["completed"] and task["due_time"] and task ["due_time"] <= current_time:
                    if not task.get("notified", False):
                        due_tasks.append[{**task, "user_id": int(user_id_str)}]
                        task["notified"] = True

        if due_tasks:
            await self.write(data)
        return due_tasks

class TamagotchiRepository(BaseJSONRepository):
    """Repository for managing Tamagotchi pet stats and history."""
    
    def __init__(self, file_path: str = "data/tamagotchi.json"):
        super().__init__(file_path, default_data={})

    async def _get_raw_user_data(self, user_id: int) -> dict[str, Any]:
        """Internal helper to get or initialize user data structure."""
        data = await self.read()
        str_id = str(user_id)
        
        if str_id not in data:
            data[str_id] = {"active": None, "history": []}
            return data[str_id]
            
        # Migration logic for old structure
        if isinstance(data[str_id], dict) and "active" not in data[str_id]:
            old_pet = data[str_id]
            data[str_id] = {"active": old_pet, "history": []}
            
        return data[str_id]

    async def get_pet(self, user_id: int) -> dict[str, Any] | None:
        user_data = await self._get_raw_user_data(user_id)
        return user_data.get("active")

    async def save_pet(self, user_id: int, pet_data: dict[str, Any] | None) -> None:
        data = await self.read()
        user_data = await self._get_raw_user_data(user_id)
        user_data["active"] = pet_data
        data[str(user_id)] = user_data
        await self.write(data)

    async def add_to_history(self, user_id: int, pet_data: dict[str, Any]) -> None:
        data = await self.read()
        user_data = await self._get_raw_user_data(user_id)
        user_data["history"].append(pet_data)
        data[str(user_id)] = user_data
        await self.write(data)

    async def get_history(self, user_id: int) -> list[dict[str, Any]]:
        user_data = await self._get_raw_user_data(user_id)
        return user_data.get("history", [])

    async def create_pet(self, user_id: int, name: str) -> dict[str, Any]:
        pet_data = {
            "name": name,
            "satiety": 100.0,
            "energy": 100.0,
            "happiness": 100.0,
            "hygiene": 100.0,
            "discipline": 50.0,
            "last_update": time.time(),
            "born_at": time.time(),
            "died_at": None,
            "leave_reason": None
        }
        await self.save_pet(user_id, pet_data)
        return pet_data
    