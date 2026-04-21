import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import Optional
from utils.repositories import SettingsRepository

logger = logging.getLogger(__name__)

class ServerEvents(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings = SettingsRepository()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild

        auto_role_id = await self.settings.get_setting(guild.id, "auto_role_id")
        if auto_role_id:
            role = guild.get_role(auto_role_id)
            if role:
                try:
                    await member.add_roles(role, reason="Auto-role on join")
                except discord.Forbidden:
                    logger.error(f"Failed to auto-role {member} in {guild.name}")
        
        welcome_channel_id = await self.settings.get_setting(guild.id, "welcome_channel_id")
        if welcome_channel_id:
            channel = guild.get_channel(welcome_channel_id)
            if channel:
                welcome_msg = await self.settings.get_setting(guild.id, "welcome_message", "Welcome {user} to {server}!")
                formatted_msg = welcome_msg.replace("{user}", member.mention).replace("{server}", guild.name)
                try:
                    await channel.send(formatted_msg)
                except discord.Forbidden:
                    pass

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or not before.guild:
            return
        if before.content == after.content:
            return
        
        log_channel_id = await self.settings.get_setting(before.guild.id, "log_channel_id")
        if log_channel_id:
            channel = before.guild.get_channel(log_channel_id)
            if channel:
                embed = discord.Embed(
                    title="Message Edited",
                    description=f"User: {before.author.mention}\n Channel: {before.channel.mention}",
                    color=discord.Color.blue(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(name="Before", value=before.content[:1024] or "(Empty)", inline=False)
                embed.add_field(name="After", value=after.content[:1024] or "(Empty)", inline=False)
                embed.set_footer(text=f"User ID: {before.author.id}")
                try:
                    await channel.send(embed=embed)
                except discord.Forbbiden:
                    pass

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        
        log_channel_id = await self.settings.get_setting(message.guild.id, "log_channel_id")
        if log_channel_id:
            channel = message.guild.get_channel(log_channel_id)
            if channel:
                embed = discord.Embed(
                    title="Message Deleted",
                    description=f"User: {message.author.mention}\n Channel: {message.channel.mention}",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(name="Content", value=message.content[:1024] or ("Empty"), inline=False)
                embed.set_footer(text=f"User ID: {message.author.id}")
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass

    config = app_commands.Group(name="config", description="Change server settings")

    @config.command(name="logs", description="Set log channel")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def config_logs(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        await self.settings.set_setting(interaction.guild_id, "log_channel_id", channel.id)
        await interaction.response.send_message(f"Set log channel to {channel.mention}", ephemeral=True)

    @config.command(name="welcome_channel", description="Set the welcome channel")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def config_welcome_msg(self, interaction: discord.Interaction, channel = discord.TextChannel) -> None:
        await self.settings.set_setting(interaction.guild_id, "welcome_channel_id", channel.id)
        await interaction.response.send_message(f"Set welcome channel to {channel.mention}", ephemeral=True)

    @config.command(name="welcome_message", description="Set welcome message")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def config_welcome_msg(self, interaction: discord.Interaction, message: str) -> None:
        await self.settings.set_setting(interaction.guild_id, "welcome_message", message)
        await interaction.response.send_message("Welcome message updated", ephemeral=True)

    @config.command(name="autorole", description="Set the role given to new members")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def config_autorole(self, interaction: discord.Interaction, role: discord.Role) -> None:
        await self.settings.set_setting(interaction.guild_id, "auto_role_id", role.id)
        await interaction.response.send_message(f"Autorole set to {role.name}", ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ServerEvents(bot))
