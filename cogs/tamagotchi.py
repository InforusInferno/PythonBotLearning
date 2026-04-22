import discord
from discord import app_commands
from discord.ext import commands
import logging
import time
import math
import random
from typing import Optional
from utils.repositories import TamagotchiRepository

logger = logging.getLogger(__name__)

async def setup(bot):
    """Entry point for the extension."""
    await bot.add_cog(TamagotchiCog(bot))

class TamagotchiCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.repo = TamagotchiRepository()
        self.decay_rate = 2.0

    def _apply_decay(self, pet: dict) -> dict:
        current_time = time.time()
        time_diff = current_time - pet["last_update"]
        hours_passed = time_diff / 3600.0

        decay_amount = hours_passed * self.decay_rate

        # Fixed spelling: hygiene
        for stat in ["satiety", "energy", "happiness", "hygiene"]:
            pet[stat] = max(0.0, pet[stat] - decay_amount)
        
        pet["last_update"] = current_time

        # Fixed math syntax
        avg_health = (pet["satiety"] + pet["energy"] + pet["happiness"] + pet["hygiene"]) / 4
        if avg_health <= 0:
            pet["died_at"] = current_time
            pet["leave_reason"] = "deceased"
        elif pet["happiness"] <= 0 and pet["discipline"] < 15:
            pet["died_at"] = current_time
            pet["leave_reason"] = "ran_away"

        return pet
    
    def _get_mood_emoji(self, pet: dict) -> str:
        avg_health = (pet["satiety"] + pet["energy"] + pet["happiness"] + pet["hygiene"]) / 4
        if avg_health > 80:
            status = "😛 Very Happy"
        elif avg_health > 50:
            status = "😐 Meh"
        elif avg_health > 20:
            status = "😔 Struggling"
        elif avg_health > 0:
            status = "🤒 Critical"
        else:
            status = "⚰️ Dead"

        if pet["discipline"] < 30:
            status += " | 😈 Naughty"
        elif pet["discipline"] > 80:
            status += " | 😇 Well Behaved"

        return status

    async def _get_or_create_pet(self, interaction: discord.Interaction) -> Optional[dict]:
        pet = await self.repo.get_pet(interaction.user.id)
        if not pet:
            await interaction.response.send_message("You don't have a pet! Use `/pet_create` to adopt one.")        
            return None
        
        pet = self._apply_decay(pet)

        if pet.get("leave_reason"):
            reason = pet["leave_reason"]
            await self.repo.add_to_history(interaction.user.id, pet)
            await self.repo.save_pet(interaction.user.id, None)
            
            # Fixed f-string quotes
            if reason == "deceased":
                msg = f"Your pet {pet['name']} has died due to neglect."
            else:
                msg = f"Your pet {pet['name']} ran away."
            await interaction.response.send_message(f"{msg}\nUse `/pet_history` to visit the graveyard or `/pet_create` to adopt a new one.")
            return None
        return pet
    
    @app_commands.command(name="pet_create", description="Adopt a pet")
    async def pet_create(self, interaction: discord.Interaction, name: str):
        existing = await self.repo.get_pet(interaction.user.id) # Fixed .user.id
        if existing:
            await interaction.response.send_message(f"You already have a pet named {existing['name']}!", ephemeral=True)
            return
        
        await self.repo.create_pet(interaction.user.id, name)
        await interaction.response.send_message(f"Congrats! You adopted {name}! Use `/pet_status` to check")

    @app_commands.command(name="pet_status", description="Check on your pet")
    async def pet_status(self, interaction: discord.Interaction):
        pet = await self._get_or_create_pet(interaction)
        if not pet: return

        await self.repo.save_pet(interaction.user.id, pet)
        embed = discord.Embed(
            title=f"{pet['name']}'s Status",
            description=f"Managed by {interaction.user.mention}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Condition", value=self._get_mood_emoji(pet), inline=False)
        embed.add_field(name="Satiety (Hunger)", value=f"{math.floor(pet['satiety'])}/100", inline=True)
        embed.add_field(name="Energy (Sleep)", value=f"{math.floor(pet['energy'])}/100", inline=True)
        embed.add_field(name="Happiness", value=f"{math.floor(pet['happiness'])}/100", inline=True)
        embed.add_field(name="Hygiene (Clean)", value=f"{math.floor(pet['hygiene'])}/100", inline=True)
        embed.add_field(name="Discipline", value=f"{math.floor(pet['discipline'])}/100", inline=True)
        
        embed.set_footer(text=f"Pet born on {time.strftime('%Y-%m-%d', time.localtime(pet['born_at']))}")
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="pet_history", description="View previous pets")
    async def pet_history(self, interaction: discord.Interaction):
        history = await self.repo.get_history(interaction.user.id)
        if not history:
            await interaction.response.send_message("Nothing here. Either no deaths or no pets", ephemeral=True)
            return
        
        embed = discord.Embed(title=f"{interaction.user.display_name}'s Graveyard", color=discord.Color.dark_grey())

        desc = ""
        for i, pet in enumerate(reversed(history), 1):
            lifespan = pet["died_at"] - pet["born_at"]
            days = int(lifespan // 86400)
            hours = int((lifespan % 86400) // 3600)

            reason = pet.get("leave_reason", "deceased")
            status = "Passed Away" if reason == "deceased" else "Ran Away"
            
            desc += f"**{i}. {pet['name']}** ({status})\nLived: {days}d {hours}h | Date: <t:{int(pet['died_at'])}:d>\n\n"
            if i >= 10: break

        embed.description = desc
        await interaction.response.send_message(embed=embed)

    async def _interact(self, interaction: discord.Interaction, satiety=0, energy=0, happiness=0, hygiene=0, discipline=0, msg="Done!", can_refuse=True):
        pet = await self._get_or_create_pet(interaction)
        if not pet: return

        if can_refuse and pet["discipline"] < 30:
            refusal_chance = min(0.4, (35 - pet["discipline"]) / 100)
            if random.random() < refusal_chance:
                await self.repo.save_pet(interaction.user.id, pet)
                responses = [
                    f"**{pet['name']}** turned their back on you and ignored the command.",
                    f"**{pet['name']}** is being stubborn and won't listen.",
                    f"**{pet['name']}** just stared at you blankly.",
                    f"**{pet['name']}** ran away and hid!"
                ]
                await interaction.response.send_message(random.choice(responses))
                return
        
        pet["satiety"] = min(100.0, max(0.0, pet["satiety"] + satiety))
        pet["energy"] = min(100.0, max(0.0, pet["energy"] + energy))
        pet["happiness"] = min(100.0, max(0.0, pet["happiness"] + happiness))
        pet["hygiene"] = min(100.0, max(0.0, pet["hygiene"] + hygiene))
        pet["discipline"] = min(100.0, max(0.0, pet["discipline"] + discipline))

        await self.repo.save_pet(interaction.user.id, pet)
        await interaction.response.send_message(f"{pet['name']}: {msg}")
    
    @app_commands.command(name="feed", description="Feed your pet")
    async def feed(self, interaction: discord.Interaction):
        await self._interact(interaction, satiety=20, hygiene=-5, msg="yum yum")

    @app_commands.command(name="sleep", description="Snooze")
    async def sleep(self, interaction: discord.Interaction):
        await self._interact(interaction, energy=40, msg="ZzZzZzZzZz")
    
    @app_commands.command(name="pet", description="pet your pet")
    async def pet_cmd(self, interaction: discord.Interaction): # Fixed function name
        await self._interact(interaction, happiness=15, msg="pat pat pat")
    
    @app_commands.command(name="play", description="games :D")
    async def play_cmd(self, interaction: discord.Interaction): # Fixed function name
        await self._interact(interaction, happiness=25, energy=-15, hygiene=-10, msg="your pet has unlocked the zoomies")

    @app_commands.command(name="hit", description="Punish >:(")
    async def hit_cmd(self, interaction: discord.Interaction): # Fixed function name
        await self._interact(interaction, happiness=-30, discipline=10, msg="OWWW", can_refuse=False)
    
    @app_commands.command(name="poke", description="Poke your pet")
    async def poke(self, interaction: discord.Interaction):
        await self._interact(interaction, happiness=-5, energy=5, msg="Boop! Woke em up")

    @app_commands.command(name="clean", description="take a shower")
    async def clean(self, interaction: discord.Interaction):
        await self._interact(interaction, hygiene=40, msg="squeaky clean!")

    @app_commands.command(name="hug", description="give a hug :D")
    async def hug(self, interaction: discord.Interaction):
        await self._interact(interaction, happiness=30, msg="awwwww")

    @app_commands.command(name="nudge", description="give a nudge")
    async def nudge(self, interaction: discord.Interaction):
        await self._interact(interaction, discipline=5, happiness=-2, msg="pet straightened up now", can_refuse=False)

    @app_commands.command(name="praise", description="praise pet")
    async def praise(self, interaction: discord.Interaction):
        await self._interact(interaction, discipline=10, happiness=10, msg="YAYYYY", can_refuse=False)

    @app_commands.command(name="time_out", description="time out")
    async def time_out(self, interaction: discord.Interaction):
        await self._interact(interaction, discipline=20, happiness=-20, msg=":(", can_refuse=False)
