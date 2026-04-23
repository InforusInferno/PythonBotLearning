import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
import random
import time
import datetime
from typing import Optional, List, Dict
from utils.repositories import EconomyRepository, BoostRepository

logger = logging.getLogger(__name__)

MESSAGE_COOLDOWN = 60
MESSAGE_MIN_CREDITS = 5
MESSAGE_MAX_CREDITS = 15
DAILY_MIN_CREDITS = 100
DAILY_MAX_CREDITS = 200
DAILY_COOLDOWN = 86400
WORK_MIN_CREDITS = 50
WORK_MAX_CREDITS = 150
WORK_COOLDOWN = 3600
STEAL_COOLDOWN = 7200
STEAL_SUCCESS_CHANCE = 0.4
STEAL_MIN_PERCENT = 0.1
STEAL_MAX_PERCENT = 0.3
STEAL_FINE_MIN = 100
STEAL_FINE_MAX = 200

class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.repo = EconomyRepository()
        self.boost_repo = BoostRepository()
        self.passive_income_task.start()

    def cog_unload(self):
        self.passive_income_task.cancel()

    SHOP_ITEMS = {
         "red_role": {"name": "Red Role Color", "price": 500, "type": "role", "role_name": "Red Specialist"},
        "blue_role": {"name": "Blue Role Color", "price": 500, "type": "role", "role_name": "Blue Veteran"},
        "gold_role": {"name": "Gold Role Color", "price": 1000, "type": "role", "role_name": "Gold Elite"},
        "investor": {"name": "Investor Role (Passive Income)", "price": 5000, "type": "role", "role_name": "Server Investor"},
        "xp_boost": {"name": "XP Booster (2x for 1h)", "price": 1500, "type": "boost", "boost_type": "xp_multiplier"}
    }

    @tasks.loop(hours=1.0)
    async def passive_income_task(self):
        logger.info("Running passive inc task")
        for guild in self.bot.guilds:
            investor_role = discord.utils.get(guild.roles, name="Server Investor")
            if not investor_role:
                continue

            for member in investor_role.members:
                if member.bot:
                    continue
                await self.repo.add_balance(guild.id, member.id, 100)
                logger.info(f"Gave 100 p credits to {member} in {guild.name}")
    @passive_income_task.before_loop
    async def before_passive_income_task(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        
        guild_id = message.guild.id
        user_id = message.author.id
        current_time = time.time()

        last_msg = await self.repo.get_cooldown(guild_id, user_id, "message")
        if current_time - last_msg < MESSAGE_COOLDOWN:
            return
        
        await self.repo.set_cooldown(guild_id, user_id, "message", current_time)

        multiplier = await self.boost_repo.get_active_multiplier(guild_id, user_id, "economy")
        credits_gain = int(random.randint(MESSAGE_MIN_CREDITS, MESSAGE_MAX_CREDITS) * multiplier)

        await self.repo.add_balance(guild_id, user_id, credits_gain)

    @app_commands.command(name="balance", description="Check your balance")
    async def balance(self, interaction: discord.Interaction, member: Optional[discord.Member] = None) -> None:
        target = member or interaction.user
        if not interaction.guild_id:
            return
        
        balance = await self.repo.get_balance(interaction.guild_id, target.id)

        embed = discord.Embed(
            title="Economy Balance",
            description=f"{target.mention} has {balance} credits.",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=target.display_avatar.url if target.display_avatar else None)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="Get daily bonus")
    async def daily(self, interaction: discord.Interaction) -> None:
        if not interaction.guild_id:
            return
        
        guild_id = interaction.guild_id
        user_id = interaction.user.id
        current_time = time.time()

        last_daily = await self.repo.get_cooldown(guild_id, user_id, "daily")
        if current_time - last_daily < DAILY_COOLDOWN:
            remaining = int(DAILY_COOLDOWN - (current_time - last_daily))
            hours, remainder = divmod(remaining, 3600)
            minutes, seconds = divmod(remaining, 60)
            await interaction.response.send_message(f"You already claimed your daily. Check back in {hours}h, {minutes}m, and {seconds}s.", ephemeral=True)
            return
        
        reward = random.randint(DAILY_MIN_CREDITS, DAILY_MAX_CREDITS)
        await self.repo.add_balance(guild_id, user_id, reward)
        await self.repo.set_cooldown(guild_id, user_id, "daily", current_time)

        await interaction.response.send_message(f"Daily claimed. Received {credits} credits.")

    @app_commands.command(name="work", description="be empl*yed and get a j*b (and  money)")
    async def work(self, interaction: discord.Interaction) -> None:
        if not interaction.guild_id:
            return

        guild_id = interaction.guild_id
        user_id = interaction.user.id
        current_time = time.time()

        last_work = await self.repo.get_cooldown(guild_id, user_id, "work")
        if current_time - last_work < WORK_COOLDOWN:
            remaining = int(WORK_COOLDOWN - (current_time - last_work))
            await interaction.response.send_message(f"You're exhausted. Wait {remaining // 60}m", ephemeral=True)
            return
        
        jobs = ["You worked as a librarian", "You sold a bunch of newspapers", "You won the local chess championship", "You won a giveaway", "You met verity", "You arrested a bunch of guys for fraud"]
        job = random.choice(jobs)
        reward = random.randint(WORK_MIN_CREDITS, WORK_MAX_CREDITS)

        await self.repo.add_balance(guild_id, user_id, reward)
        await self.repo.set_cooldown(guild_id, user_id, "work", current_time)

        await interaction.response.send_message(f"{job} and got {reward} credits.")

    @app_commands.command(name="steal", description="robin dabank")
    async def steal(self, interaction: discord.Interaction, member: discord.Member) -> None:
        if not interaction.guild_id:
            return
        
        if member.id == interaction.user.id:
            await interaction.response.send_message("bro you cannot rob yourself 😭", ephemeral=True)
            return
        
        if member.bot:
            await interaction.response.send_message("Leave the clanker alone", ephemeral=True)
            return
        
        guild_id = interaction.guild_id
        user_id = interaction.user.id
        current_time = time.time()

        last_steal = await self.repo.get_cooldown(guild_id, user_id, "steal")
        if current_time - last_steal < STEAL_COOLDOWN:
            remaining = int(STEAL_COOLDOWN - (current_time - last_steal))
            await interaction.response.send_message(f"Cops are investigating, wait {remaining // 60} mins", ephemeral=True)
            return
        
        target_balance = await self.repo.get_balance(guild_id, member.id)
        if target_balance < 50:
            await interaction.response.send_message("dis bro broke as hell give him a break", ephemeral=True)
            return
        
        await self.repo.set_cooldown(guild_id, user_id, "steal", current_time)

        if random.number() < STEAL_SUCCESS_CHANCE:
            percent = random.uniform(STEAL_MIN_PERCENT, STEAL_MAX_PERCENT)
            stolen = int(target_balance * percent)
            await self.repo.add_balance(guild_id, member.id, -stolen)
            await self.repo.add_balance(guild_id, user_id, stolen)
            await interaction.response.send_message(f"You stole {credits} from {member.mention}")
        else:
            fine = random.randint(STEAL_FINE_MIN, STEAL_FINE_MAX)
            await self.repo.add_balance(guild_id, user_id, -fine)
            await interaction.response.send_message(f"Cops caught bro, bail was {credits}")

    @app_commands.command(name="pay", description="give money to a brokie")
    async def pay(self, interaction: discord.Interaction, member: discord.Member, amount: int) -> None:
        if not interaction.guild_id:
            return
        
        if amount <= 0:
            await interaction.response.send_message("u not slick buddy 😭", ephemeral=True)
            return
        
        if member.id == interaction.user.id:
            await interaction.response.send_message("bro. 😭🤞 no.", ephemeral=True)
            return
        
        guild_id = interaction.guild_id
        user_id = interaction.user.id
        
        balance = await self.repo.get_balance(guild_id, user_id)
        if balance < amount:
            await interaction.response.send_message("how u tryna do that u cant js print money", ephemeral=True)
            return
        
        await self.repo.add_balance(guild_id, user_id, -amount)
        await self.repo.add_balance(guild_id, member.id, amount)

        await interaction.response.send_message(f"You sent {credits} to {member.mention}")

    @app_commands.command(name="shop", description="check HOW to spend fake money on faker stuff")
    async def shop(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="Server Shop",
            description="Buy pixels",
            color=discord.Color.blue()
        )

        for item_id, details in self.SHOP_ITEMS.items():
            embed.add_field(
                name=f"{details['name']} - {details['price']} creds",
                value=f"Type: {details['type'].capitalize()}\nID: `{item_id}`",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="buy stuff")
    async def buy(self, interaction: discord.Interaction, item_id : str) -> None:
        if not interaction.guild_id:
            return
        
        if item_id not in self.SHOP_ITEMS:
            await interaction.response.send_message("invalid item id. use /shop to check", ephemeral=True)
            return
        
        item = self.SHOP_ITEMS[item_id]
        guild_id = interaction.guild_id
        user_id = interaction.user.id

        balance = await self.repo.get_balance(guild_id, user_id)
        if balance < item["price"]:
            await interaction.response.send_message("you too broke for this twin", ephemeral=True)
            return
        
        if item["type"] == "role":
            role_name = item["role_name"]
            role = discord.utils.get(interaction.guild.roles, name=role_name)

            if not role:
                try:
                    role = await interaction.guild.create_role(name=role_name, reason="Shop purchase")
                except discord.Forbidden:
                    await interaction.response.send_message("i dont have perms to create a role", ephemeral=True)
                    return
                
            if role in interaction.user.roles:
                await interaction.response.send_message("you already have this", ephemeral=True)
                return
            
            try:
                await interaction.user.add_roles(role)
            except discord.Forbidden:
                await interaction.response.send_message("I dont have perms to add roles to a user", ephemeral=True)
                return
        
        elif item["type"] == "boost":
            boost_type = "xp" if "xp" in item["boost_type"] else "economy"
            end_time = time.time() + 3600
            await self.boost_repo.add_boost(guild_id, user_id, boost_type, 2.0, end_time)

        await self.repo.add_balance(guild_id, user_id, -item["price"])
        await interaction.response.send_message(f"Successfully bought {item['name']} for {item['price']}")

    @app_commands.command(name="credits_leaderboard", description="check who is the richest")
    async def credits_leaderboard(self, interaction: discord.Interaction) -> None:
        if not interaction.guild_id:
            await interaction.response.send_message("leaderboards are only in serversss", ephemeral=True)
            return
        
        data = await self.repo.read()
        str_guild = str(interaction.guild_id)
        guild_data = data.get(str_guild, {})

        if not guild_data:
            await interaction.response.send_message("No one has money in here")
            return
        
        sorted_users = sorted(
            [(user_id, info["balance"]) for user_id, info in guild_data.items()],
            key= lambda x:x[1],
            reverse=True
        )[:10]

        embed = discord.Embed(
            title=f"Credit Leaderboard - {interaction.guild.name}",
            color=discord.Color.gold()
        )

        desc = " "
        for i, (user_id_str, balance) in enumerate(sorted_users, 1):
            desc += f"**{i}.** <@{user_id_str}> - {balance} Credits\n"

        embed.description = desc
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Economy(bot))