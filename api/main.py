import os
import sys
import json
import time
import asyncio
import urllib.request
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

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
load_dotenv()

def _agent_log(hypothesis_id: str, location: str, message: str, data: dict):
    # #region agent log
    try:
        with open("debug-6bb96e.log", "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "sessionId": "6bb96e",
                "runId": "baseline",
                "hypothesisId": hypothesis_id,
                "location": location,
                "message": message,
                "data": data,
                "timestamp": int(time.time() * 1000)
            }) + "\n")
    except Exception:
        pass
    # #endregion

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    _agent_log(
        "H6_REQUEST_REACHABILITY",
        "api/main.py:middleware:before",
        "incoming request",
        {
            "method": request.method,
            "path": request.url.path,
            "query": str(request.url.query),
            "origin": request.headers.get("origin")
        }
    )
    response = await call_next(request)
    _agent_log(
        "H6_REQUEST_REACHABILITY",
        "api/main.py:middleware:after",
        "completed request",
        {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code
        }
    )
    return response

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
    _agent_log("H4_BACKEND_EXCEPTION", "api/main.py:get_user_data", "entered get_user_data", {"guild_id": guild_id, "user_id": user_id})
    xp = await leveling_repo.get_xp(guild_id, user_id)
    balance = await economy_repo.get_balance(guild_id, user_id)
    pet = await tamagotchi_repo.get_pet(user_id)
    tasks = await task_repo.get_tasks(user_id)

    level = int((xp/100) ** 0.5) if xp > 0 else 0

    payload = {
        "id": str(user_id),
        "guild_id": str(guild_id),
        "xp": xp,
        "level": level,
        "balance": balance,
        "pet": pet,
        "tasks": tasks
    }
    _agent_log("H4_BACKEND_EXCEPTION", "api/main.py:get_user_data", "returning get_user_data payload", {"xp": xp, "balance": balance, "tasks_count": len(tasks) if isinstance(tasks, list) else None})
    return payload

@app.get("/api/leaderboard/{guild_id}")
async def get_leaderboard(guild_id: int, type: str = "xp", limit: int = 10):
    _agent_log("H3_ROUTE_OR_STATUS", "api/main.py:get_leaderboard", "entered get_leaderboard", {"guild_id": guild_id, "type": type, "limit": limit})
    if type == "xp":
        all_xp = await leveling_repo.get_all_xp(guild_id)
        sorted_users = sorted(all_xp.items(), key=lambda x:x[1], reverse=True)[:limit]
        result = [{"user_id": u, "xp": x} for u, x in sorted_users]
        _agent_log("H3_ROUTE_OR_STATUS", "api/main.py:get_leaderboard", "leaderboard xp response", {"count": len(result)})
        return result
    elif type == "economy":
        all_balances = await economy_repo.get_all_balances(guild_id)
        sorted_users = sorted(all_balances.items(), key=lambda x:x[1], reverse=True)[:limit]
        result = [{"user_id": u, "balance": b} for u, b in sorted_users]
        _agent_log("H3_ROUTE_OR_STATUS", "api/main.py:get_leaderboard", "leaderboard economy response", {"count": len(result)})
        return result
    else:
        _agent_log("H3_ROUTE_OR_STATUS", "api/main.py:get_leaderboard", "invalid leaderboard type", {"type": type})
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

@app.get("/api/bot/guilds")
async def get_bot_guilds():
    _agent_log("H5_DATA_SOURCE_OR_EMPTY", "api/main.py:get_bot_guilds", "entered get_bot_guilds", {})
    guild_ids = set()
    token = os.getenv("DISCORD_BOT_TOKEN")

    if token:
        try:
            def _fetch_discord_guilds():
                req = urllib.request.Request(
                    "https://discord.com/api/users/@me/guilds",
                    headers={"Authorization": f"Bot {token}"}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    return json.loads(response.read().decode("utf-8"))
            discord_guilds = await asyncio.to_thread(_fetch_discord_guilds)
            if isinstance(discord_guilds, list):
                guild_ids.update(str(g.get("id")) for g in discord_guilds if isinstance(g, dict) and g.get("id"))
                _agent_log("H5_DATA_SOURCE_OR_EMPTY", "api/main.py:get_bot_guilds", "discord guild fetch success", {"discord_count": len(discord_guilds)})
        except Exception as e:
            _agent_log("H5_DATA_SOURCE_OR_EMPTY", "api/main.py:get_bot_guilds", "discord guild fetch failed", {"error": str(e)})
    else:
        _agent_log("H5_DATA_SOURCE_OR_EMPTY", "api/main.py:get_bot_guilds", "missing DISCORD_BOT_TOKEN", {})

    try: 
        xp_data = await leveling_repo.read()
        if isinstance(xp_data, dict):
            guild_ids.update(xp_data.keys())
    except Exception:
        pass

    try:
        settings_data = await settings_repo.read()
        if isinstance(settings_data, dict):
            guild_ids.update(settings_data.keys())
    except Exception:
        pass

    result = list(guild_ids)
    _agent_log("H5_DATA_SOURCE_OR_EMPTY", "api/main.py:get_bot_guilds", "returning get_bot_guilds", {"count": len(result)})
    return result
