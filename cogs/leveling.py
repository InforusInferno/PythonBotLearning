import discord
from discord import app_commands
from discord.ext import commands
import logging
import random
import math
import time
from utils.repositories import LevelingRepository, SettingsRepository, BoostRepository

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
        self.settings_repo = SettingsRepository()
        self.boost_repo = BoostRepository()
        self.last_message_times: dict[int, float] = {}

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
        multiplier = await self.boost_repo.get_active_multiplier(guild_id, user_id, "xp")
        xp_gain = int(random.randint(MIN_XP_MESSAGE, MAX_XP_MESSAGE)* multiplier)

        old_xp = await self.repo.get_xp(guild_id, user_id)
        old_level = self._calculate_level(old_xp)

        await self.repo.add_xp(guild_id, user_id, xp_gain)

        new_xp = old_xp + xp_gain
        new_level = self._calculate_level(new_xp)

        # lvl up noti
        if new_level > old_level:
            try: 
                await message.channel.send(f"{message.author.mention} has reached level **{new_level}**")

                rewards = await self.settings_repo.get_role_rewards(guild_id)
                for lvl_str, role_id, in rewards.items():
                    if new_level >= int(lvl_str):
                        role = message.guild.get_role(role_id)
                        if role and role not in message.author.roles:
                            try:
                                await message.author.add_roles(role, reason=f"Level {new_level} achievement")
                                await message.channel.send(f"You got the {role.name} role!")
                            except discord.Forbidden:
                                logger.error(f"Missing perms to add role {role.name} in {message.guild.name}")
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
        embed.set_thumbnail(url=interaction.user.display_avatar.url if interaction.user.display_avatar else None)
        embed.add_field(name="Level", value=f"**{level}**", inline=True)
        embed.add_field(name="XP", value=f"**{xp}** / {next_level_xp}", inline=True)

        # progression
        progress = xp / next_level_xp
        filled_blocks = int(progress*10)
        empty_blocks = 10 - filled_blocks
        bar = "🟩" * filled_blocks + "⬛" * empty_blocks

        embed.add_field(name="Progress", value=bar, inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Show server leaderboard")
    async def leaderboard(self, interaction:discord.Interaction) -> None:
        if not interaction.guild.id:
            await interaction.response.send_message("Leaderboard is only available in servers", ephemeral=True)
            return
        
        all_xp = await self.repo.get_all_xp(interaction.guild_id)
        if not all_xp:
            await interaction.response.send_message("No one has any XP yet.")
            return
        
        sorted_xp = sorted(all_xp.items(), key=lambda x: x[1], reverse=True)[:10]

        embed = discord.Embed(
            title=f"XP Leaderboard for {interaction.guild.name}",
            color=discord.Color.gold()
        )

        desc = " "
        for i, (user_id_str, xp) in enumerate(sorted_xp, 1):
            level = self._calculate_level(xp)
            desc += f"**{i}.** <@{user_id_str}> - Level {level} ({xp} XP)\n"

        embed.description = desc
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="add_reward", description="ADMIN: Add role reward fo a level")
    @app_commands.describe(level="Level needed", role="Role awarded")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def add_reward(self, interaction:discord.Interaction, level: int, role: discord.Role) -> None:
        if not interaction.guild.id:
            return
        
        await self.settings_repo.add_role_reward(interaction.guild_id, level, role.id)
        await interaction.response.send_message(f"Added reward. {role.name} will be awarded at {level}", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Leveling(bot))
    
                    