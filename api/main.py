import os
import sys
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.repositories import (
    LevelingRepository,
    EconomyRepository,
    TamagotchiRepository,
    TaskRepository,
    ModerationRepository,
    SettingsRepository
)

app = FastAPI(title="HorizonBot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

leveling_repo = LevelingRepository()
economy_repo = EconomyRepository()
tamagotchi_repo = TamagotchiRepository()
task_repo = TaskRepository()
moderation_repo = ModerationRepository()
settings_repo = SettingsRepository()

class UserStats(BaseModel):
    id: str
    xp: int
    balance: int
    level: int

class Task(BaseModel):
    id: int
    content: str
    completed: bool
    due_time: Optional[float]

@app.get("/")
async def root():
    return {"message": "HorizonBot API is online"}

@app.get("/api/user/{guild_id}/{user_id}")
async def get_user_data(guild_id: int, user_id: int):
    xp = await leveling_repo.get_xp(guild_id, user_id)
    balance = await economy_repo.get_balance(guild_id, user_id)
    pet = await tamagotchi_repo.get_pet(user_id)
    tasks = await task_repo.get_tasks(user_id)

    level = int((xp/100) ** 0.5) if xp > 0 else 0

    return {
        "id": str(user_id),
        "guild_id": str(guild_id),
        "xp": xp,
        "level": level,
        "balance": balance,
        "pet": pet,
        "tasks": tasks
    }

@app.get("/api/leaderboard/{guild_id}")
async def get_leaderboard(guild_id: int, type: str = "xp", limit: int = 10):
    if type == "xp":
        all_xp = await leveling_repo.get_all_xp(guild_id)
        sorted_users = sorted(all_xp.items(), key=lambda x:x[1], reverse=True)[:limit]
        return [{"user_id": u, "xp": x} for u, x in sorted_users]
    elif type == "economy":
        all_balances = await economy_repo.get_all_balances(guild_id)
        sorted_users = sorted(all_balances.items(), key=lambda x:x[1], reverse=True)[:limit]
        return [{"user_id": u, "balance": b} for u, b in sorted_users]
    else:
        raise HTTPException(status_code=400, detail="Invalid leaderboard type")
    
@app.get("/api/setings/{guild_id}")
async def get_guild_settings(guild_id: int):
    banned_words = await moderation_repo.get_banned_words(guild_id)
    role_rewards = await settings_repo.get_role_rewards(guild_id)
    return {
        "banned_words": banned_words,
        "role_rewards": role_rewards
    }

@app.post("/api/tasks/{user_id}/{task_id}/complete")
async def complete_task(user_id: int, task_id: int):
    success = await task_repo.complete_task(user_id, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True}

@app.get("/api/bot/guilds")
async def get_bot_guilds():
    data_path = os.path.join(os.path.dirname(__file__), "..", "data")
    if not os.path.exists(data_path):
        return []
    
    return [d for d in os.listdir(data_path) if os.path.isdir(os.path.join(data_path, d))]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

