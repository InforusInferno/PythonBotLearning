import asyncio
import logging
from typing import Dict, Set
import discord
from discord import app_commands
from discord.ext import commands
from utils.repositories import StudyRepository

logger = logging.getLogger(__name__)

MAX_POMODORO_MINUTES = 180

class GroupPomodoroView(discord.ui.View):
    def __init__(self, host_id: int, cog: "StudyTimer")
        super().__init__(timeout=None)
        self.host_id = host_id
        self.cog = cog

    @discord.ui.button(label="Join session", style=discord.ButtonStyle.success, emoji="⏳")
    async def join_session(self, interaction: discord.Interaction, button: discord.ui.button):
        if self.host_id not in self.cog.active_timers:
            await interaction.response.send_message("This session ended/doesn't exist.", ephemeral=True)
            self.stop()
            return
        
        participants = self.cog.active_timers[self.host_id]["participants"]

        if interaction.user.id in participants:
            await interaction.response.send_message("You are already in this session.", ephemeral=True)
            return
        
        participants.add(interaction.user.id)
        await interaction.response.send_message(f"You joined <@{self.host_id}>'s session,", ephemeral=True)

class StudyTimer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_timers:Dict[int, dict]={}
        self.repo = StudyRepository()

    async def _pomodoro_task(self, host: discord.Member | discord.User, minutes: int, is_group: bool):
        try:
            await asyncio.sleep(minutes * 60)

            session_data = self.active_timers.get(host.id)
            if not session_data:
                return
            
            participants = session_data["participants"]

            for p_id in participants:
                await self.repo.add_study_time(p_id, minutes)
                try:
                    user = self.bot.get_user(p_id) or await self.bot.fetch_user(p_id)
                    await user.send(f"The {minutes}-minute session has ended.")
                except (discord.Forbbiden, discord.HTTPException):
                    pass

        except asyncio.CancelledError:
            pass
        finally:
            if host.id in self.active_timers:
                del self.active_timers[host.id]

    async def _start_session(self, interaction: discord.Interaction, minutes: int, is_group: bool) -> bool:
        if interaction.user.id in self.active_timers:
            msg = "You already are hosting a timer." if is_group else "You already have a timer running."
            await interaction.response.send_message(msg, ephemeral=True)
            return False
        
        if minutes <= 0 or minutes > MAX.POMODORO.MINUTES:
            await interaction.response.send_message(f"Please enter a duration between 1 and {MAX_POMODORO_MINUTES} minutes.", ephemeral=True)
            return False
        
        task = asyncio.create_task(self._pomodoro_task(interaction.user, minutes, is_group=is_group))
        self.active_timers[interaction.user.id] = {
            "task":task,
            "participants":{interaction.user.id},
            "is_group":is_group
        }
        return True
    pomodoro = app_commands.Group(name="pomodoro", description="Timer commands :D")

    @pomodoro.command(name="start", description="Start a solo timer.")
    @app_commands.describe(minutes="Length of timer (in mins, max 180)")
    async def pomodoro_start(self, interaction: discord.Interaction, minutes: int) -> None:
        if await self._start_session(interaction, minutes, is_group=False):
            await interaction.response.send_message(f"Started a timer for {minutes}m. DM will be sent when session ends.")

    @pomodoro.command(name="group", description="Star a group timer.")
    @app_commands.describe(minutes="Length of timer (in mins, max 180)")
    async def pomodoro_group(self, interaction: discord.Interaction, minutes: int) -> None:
        if await self._start_session(interaction, minutes, is_group=True):
            view = GroupPomodoroView(host_id=interaction.user.id, cog=self)
            await interaction.response.send_message(f"Started a group timer for {minutes}m. \nClick the button to join.", view=view)

    @pomodoro.command(name="stop", description="Stop active timer.")
    async def pomodoro_stop(self, interaction: discord.Interaction) -> None:
        if interaction.user.id not in self.active_timers:
            await interaction.response.send_message("You don't have an active timer.", ephemeral=True)
            return
        
        session_data = self.active_timers[interaction.user.id]
        session_data["task"].cancel()
        await interaction.response.send_message("Timer stopped. Incomplete session won't count to totals.")

    @pomodoro.command(name="stats", description="Check statistics.")
    async def pomodoro_stats(self, interaction: discord.Interaction) -> None:
        total_minutes = await self.repo.get_total_study_time(interaction.user.id)

        if total_minutes == 0:
            await interaction.response.send_message("You don't have any time recorded.")
            return
        hours = total_minutes // 60
        mins = total_minutes % 60

        if hours > 0:
            time_str = f"{hours}h and {mins}m"
        else:
            time_str = f"{mins}m"
        await interaction.response.send_message(f"You have spent {time_str}.")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(StudyTimer(bot))
    
     