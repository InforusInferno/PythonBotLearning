import discord
from discord import app_commands
from discord.ext import commands
from utils.repositories import ModerationRepository

class Moderation(commands.Cog):
    # mod commands, very small

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.repo = ModerationRepository()

    def  __check_hierarchy(self, interaction: discord.Interaction, member: discord.Member) -> bool:
        # ability to moderate
        if interaction.guild.owner_id == interaction.user.id:
            return True
        return member.top_role < interaction.user.top_role
    
    @app_commands.command(name="clear", description="Delete the chosen number of messages.")
    @app_commands.describe(amount="The number of messages to delete (max 100)")
    @app_commands.default_permissions(manage_messages=True)
    async def clear_messages(self, interaction: discord.Interaction, amount: int) -> None:
        if amount <= 0 or amount > 100:
            await interaction.response.send_message("Invalid input. Specifcy between 1-100.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"Success. Deleted {len(deleted)} messages.")

    @app_commands.command(name="kick", description="Kick a member from the server.")
    @app_commands.describe(member="The member to kick", reason="Reason for kick (optional)")
    @app_commands.default_permissions(kick_members=True)
    async def kick_member(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided") -> None:
        if not self.__check_hierarchy(interaction, member):
            await interaction.response.send_message("You can't kick someone with a higher or equal role as you.", ephemeral=True)
            return
        try:
            await member.kick(reason=f"Kicked by {interaction.user}: {reason}")
            await interaction.response.send_message(f"{member.display_name} has been kicked. Reason: {reason}")
        except discord.Forbidden:
            await interaction.response.send_message("I do not have permission to kick.", ephemeral=True)
    
    @app_commands.command(name="ban", description="Ban a member from the server.")
    @app_commands.describe(member="Member to ban", reason="Reason for ban (optional)")
    @app_commands.default_permissions(ban_members=True)
    async def ban_member(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided") -> None:
        if not self.__check_hierarchy(interaction, member):
            await interaction.response.send_message("You can't ban someone with a higher or equal role as you.", ephemeral=True)
            return
        try:
            await member.ban(reason=f"Banned by {interaction.user}: {reason}")
            await interaction.response.send_message(f"{member.display_name} has been banned. Reason: {reason}")
        except discord.Forbidden:
            await interaction.response.send_message("I do not have permission to ban.", ephemeral=True)
    
    automod = app_commands.Group(name="automod", description="Automod settings.")
    
    @automod.command(name="add", description="Add a word to the automod filter.")
    @app_commands.describe(word="Word to ban")
    @app_commands.default_permissions(manage_messages=True)
    async def automod_add(self, interaction: discord.Interaction, word: str) -> None:
        if not interaction.guild_id:
            return
        
        await self.repo.add_banned_word(interaction.guild_id, word)
        await interaction.response.send_message(f"Added {word} to word filter.", ephemeral=True)

    @automod.command(name="remove", description="Remove a word from the automod filter.")
    @app_commands.describe(word="Word to unban")
    @app_commands.default_permissions(manage_messages=True)
    async def automod_remove(self, interaction: discord.Interaction, word: str) -> None:
        if not interation.guild_id:
            return
        
        await self.repo.remove_banned_word(interaction.guild_id, word)
        await interaction.response.send_message(f"Removed {word} from word filter.", ephemeral=True)
        