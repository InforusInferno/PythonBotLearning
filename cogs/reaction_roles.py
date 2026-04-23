import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import List, Dict, Any, Optional
from utils.repositories import ReactionRoleRepository

logger = logging.getLogger(__name__)

class RoleButton(discord.ui.Button):
    def __init__(self, role: discord.Role, emoji: Optional[str] = None):
        super().__init__(
            label=role.name,
            style=discord.ButtonStyle.primary,
            custom_id=f"rr:button:{role.id}",
            emoji=emoji
        )
        self.role_id = role.id

    async def callback(self, interaction:discord.Interaction):
        role = interaction.guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message("That role doesn't exist", ephemeral=True)
            return
        
        if role in interaction.user.roles:
            await interaction.user_remove_roles(role)
            await interaction.response.send_message(f"Removed {role.name}", ephemeral=True)
        else:
            try:
                await interaction.user.add_roles(role)
                await interaction.response.send_message(f"Added {role.name}", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message("No permission", ephemeral=True)

class RoleSelect(discord.ui.Select):
    def __init__(self, roles: List[discord.Role], panel_id: str):
        options = [
            discord.SelectOption(label=r.name, value=str(r.id), description=f"Toggle {r.name} role")
            for r in roles
        ]
        super().__init__(
            placeholder="Select your roles..",
            min_values=0,
            max_values=len[roles],
            options=options,
            custom_id=f"rr:select:{panel_id}"
        )

    async def callback(self, interaction:discord.Interaction):
        all_role_ids = [int(o.value) for o in self.options]
        selected_ids = [int(v) for v in self.values]
        guild_roles = {r_id: interaction.guild.get_role(r_id) for r_id in all_role_ids}

        to_add = [guild_roles[r_id] for r_id in selected_ids if guild_roles[r_id] and guild_roles[r_id] not in interaction.user.roles]
        to_remove = [guild_roles[r_id] for r_id in all_role_ids if guild_roles[r_id] and r_id not in selected_ids and guild_roles[r_id] in interaction.user.roles]

        try:
            if to_add: await interaction.user.add_roles(*to_add)
            if to_remove: await interaction.user.remove_roles(*to_remove)

            msg = "Roles updated."
            if to_add: msg += f"\nAdded: {', '.join([r.name for r in to_add])}"
            if to_remove: msg += f"\nRemoved: {', '.join([r.name for r in to_remove])}"

            await interaction.response.send_message(msg, ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("No permissions", ephemeral=True)

class RoleView(discord.ui.View):
    def __init__(self, roles: List[discord.Role], mode: str, panel_id: Optional[str] = None):
        super().__init__(timeout=None)

        if mode == "buttons":
            for role in roles:
                self.add_item(RoleButton(role))
        else:
            self.add_item(RoleSelect(roles, panel_id or "temp"))

class ReactionRoles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.repo = ReactionRoleRepository()

    async def cog_load(self):
        panels = await self.repo.get_all_panels()
        count = 0
        for msg_id, data in panels.items():
            guild = self.bot.get_guild(data.get("guild_id"))
            if not guild: continue

            roles = [guild.get_role(r_id) for r_id in data["role_ids"] if guild.get_role(r_id)]
            if not roles: continue

            view = RoleView(roles, data["mode"], msg_id)
            self.bot.add_view(view)
            count += 1
        logger.info(f"Re-registered {count} reaction role panels")
    
    @app_commands.command(name="roles_create", description="Create a roles panel")
    @app_commands.describe(
        title="Title for role panel",
        description="Description for role panel",
        mode="Buttons are more suitable for smaller amounts, dropdowns for bigger",
        role1="Role to include",
        role2="Role to include",
        role3="Role to include",
        role4="Role to include",
        role5="Role to include"
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def roles_create(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        mode: str,
        role1: discord.Role,
        role2: Optional[discord.Role] = None,
        role3: Optional[discord.Role] = None,
        role4: Optional[discord.Role] = None,
        role5: Optional[discord.Role] = None
    ):
        if mode not in ["buttons", "dropdown"]:
            await interaction.response.send_message("Mode must either be 'buttons' or 'dropdown'", ephemeral=True)
            return
        
        roles = [r for r in [role1, role2, role3, role4, role5] if r]

        embed = discord.Embed(title=title, description=description, color=discord.Color.green())
        embed.set_footer(text="Click a button or select option to get role")

        view = RoleView(roles, mode)

        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()

        panel_data = {
            "guild_id": interaction.guild.id,
            "mode": mode,
            "role_ids": [r.id for r in roles],
            "title": title,
            "description": description
        }
        await self.repo.save_panel(message.id, panel_data)

        final_view = RoleView(roles, mode, str(message.id))
        await interaction.edit_original_response(view=final_view)
        self.bot.add_view(final_view)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReactionRoles(bot))
    

