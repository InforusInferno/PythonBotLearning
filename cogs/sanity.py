import discord
from discord import app_commands
from discord.ext import commands

class Sanity(commands.Cog):
    # Make sure it works
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="ping", description="Check latency.")
    async def ping(self, interaction: discord.Interaction) -> None:
        latency_ms = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Pong! Bot latency is {latency_ms}ms.")

    @app_commands.command(name="hello", description="Says hi!")
    async def hello(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"Hi, {interaction.user.mention}.")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Sanity(bot))