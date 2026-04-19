import discord
from discord import app_commands
from discord.ext import commands
import logging
import random
import math
import time
from typing import Dict
from utils.repostories import LevelingRepository

logger = logging.getLogger(__name__)

# var constants
COOLDOWN_SECONDS = 60
MIN_XP_MESSAGE = 15
MAX_XP_MESSAGE = 30

class Leveling(commands.Cog):
    # managing xp and levels

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.repo = LevelingRepository()
        self.last_message_times: Dict[int, float] = {}

    def _calculate_level(self, xp: int) -> int:
        # calc lvl from formula -> level = 0.1 * sqrt(xp)
        return math.floor(0.1 * math.sqrt(xp))
    
    def _xp_for_next_level(self, level: int) -> int:
        # calc xp for a specific level
        return ((level+1) / 0.1) ** 2
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # ignore self
        if message.author.bot or not message.guild:
            return
        
        user_id = message.author.id
        guild_id = message.guild.id
        current_time = time.time()

        # cooldown check
        if user_id in self.last_message_times:
            if current_time - self.last_message_times[user_id] < COOLDOWN_SECONDS:
                return
            
        # update msg time
        self.last_message_times[user_id] = current_time

        # calc + add xp
        xp_gain = random.randint(MIN_XP_MESSAGE, MAX_XP_MESSAGE)

        old_xp = await self.repo.get_xp(guild_id, user_id)
        old_level = self._calculate_level(old_xp)

        await self.repo.add_xp(guild_id, user_id, xp_gain)

        new_xp = old_xp + xp_gain
        new_level = self._calculate_level(new_xp)

        # lvl up noti
        if new_level > old_level:
            try: 
                await message.channel.send(f"{message.author.mention} has reached level **{new_level}**")
            except discord.Forbidden:
                pass

    @app_commands.command(name="rank", description="Check current level and XP.")
    async def rank(self, interaction: discord.Interaction) -> None:
        # show rank card
        if not interaction.guild_id:
            await interaction.response.send_message("Levels are only in serves.", ephemeral=True)
            return
        
        xp = await self.repo.get_xp(interaction.guild_id, interaction.user.id)
        level = self._calculate_level(xp)
        next_level_xp = int(self._xp_for_next_level(level))

        embed = discord.Embed(
            title=f"Rank - {interaction.user.display_name}",
            color=discord.Color.red()
        )
        embed.set.thumbnail(url=interaction.user.display_avatar.url if interaction.user.display_avatar else None)
        embed.add_field(name="Level", value=f"**{level}**", inline=True)
        embed.add_field(name="XP", value=f"**{xp}** / {next_level_xp}", inline=True)

        # progression
        progress = xp / next_level_xp
        filled_blocks = int(progress*10)
        empty_blocks = 10 - filled_blocks
        bar = "🟩" * filled_blocks + "⬛" * empty_blocks

        embed.add_field(name="Progress", value=bar, inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Leveling(bot))
    
                    