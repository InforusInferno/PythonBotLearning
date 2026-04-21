import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
import time
import re
from typing import Optional
from utils.repositories import TaskRepository

logger = logging.getLogger(__name__)

class TaskManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.repo = TaskRepository()
        self.reminder_check.start()

    def cog_unload(self):
        self.reminder_check.cancel()

    def parse_duration(self, duration_str : str) -> int | None:
        total_seconds = 0
        patterns = {
            'd' : 86400,
            'h' : 3600,
            'm' : 60,
            's' : 1
        }

        matches = re.findall(r'(\d+)([dhms])', duration_str.lower())
        if not matches:
            return None
        
        for amount, unit in matches:
            total_seconds += int(amount) * patterns[unit]

        return total_seconds
    
    @tasks.loop(minutes=1.0)
    async def reminder_check(self):
        due_tasks = await self.repo.get_all_due_tasks()
        for task in due_tasks:
            try:
                user = self.bot.get_user(task["user_id"]) or await self.bot.fetch_user(task["user_id"])
                if user:
                    embed = discord.Embed(
                        title = "Reminder",
                        description= task["content"],
                        color=discord.Color.orange()
                    )
                    await user.send(embed=embed)
            except Exception as e:
                logger.error(f"Failed to send reminder to {task['user_id']}: {e}")

    @reminder_check.before_loop
    async def before_reminder_check(self):
        await self.bot.wait_until_ready()

    task_group = app_commands.Group(name="task", description="Manage your tasks")

    @task_group.command(name="add", description="add a new task to your list")
    async def task_add(self, interaction: discord.Interaction, content: str) -> None:
        task_id = await self.repo.add_task(interaction.user.id, content)
        await interaction.response.send_message(f"Added task #{task_id}: {content}", ephemeral=True)

    @task_group.command(name="list", description="list active tasks")
    async def task_list(self, interaction: discord.Interaction) -> None:
        tasks = await self.repo.get_tasks(interaction.user.id)
        if not tasks:
            await interaction.response.send_message("You don't have any active tasks", ephemeral=True)
            return
        
        embed = discord.Embed(title="Your tasks", color=discord.Color.blue())
        desc = ""
        for t in tasks:
            due_str = f"(Due: <t:{int(t['due_time'])}:R>)" if t["due_time"] else ""
            desc += f"{t['id']}: {t['content']}{due_str}\n"

        embed.description = desc
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @task_group.command(name="complete", description="mark a task as completed")
    async def task_complete(self, interaction: discord.Interaction, task_id : int) -> None:
        success = await self.repo.complete_task(interaction.user.id, task_id)
        if success:
            await interaction.response.send_message(f"Task #{task_id} marked complete", ephemeral=True)
        else:
            await interaction.response.send_message(f"Task #{task_id} not found", ephemeral=True)
            
    @app_commands.command(name="remind", description="set a reminder")
    @app_commands.describe(duration="How long should this last? (1h, 1d, 1m)", content="Reminder is for: ")
    async def remind(self, interaction: discord.Interaction, duration: str, content: str) -> None:
        seconds = self.parse_duration(duration)
        if not seconds:
            await interaction.response.send_message("Invalid duration", ephemeral=True)
            return
        
        due_time = time.time() + seconds
        task_id = await self.repo.add_task(interaction.user.id, content, due_time=due_time)

        await interaction.response.send_message(f"You'll get a reminder for '{content}' in {duration} (<t{int(due_time)}:F).",ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TaskManager(bot))