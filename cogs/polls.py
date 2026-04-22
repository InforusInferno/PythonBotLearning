import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import List, Optional
from utils.repositories import PollRepository

logger = logging.getLogger(__name__)

class PollVoteButton(discord.ui.Button):
    def __init__(self, label: str, index: int, custom_id: str):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.secondary,
            custom_id=custom_id
        )
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        view: PollView = self.view
        user_id = str(interaction.user.id)

        poll_data = await view.repo.get_poll(interaction.message.id)
        if not poll_data:
            await interaction.response.send_message("This poll is no longer active", ephemeral=True)
            return
        
        if poll_data["votes"].get(user_id) == self.index:
            await interaction.response.send_message("You have already voted for this option", ephemeral=True)
            return

        poll_data["votes"][user_id] = self.index
        await view.repo.save_poll(interaction.message.id, poll_data)

        embed = view.create_poll_embed(poll_data)
        await interaction.response.edit_message(embed=embed)

class PollView(discord.ui.View):
    def __init__(self, repo: PollRepository, question: str, options: List[str], message_id: Optional[int] = None):
        super().__init__(timeout=None)
        self.repo = repo
        self.question = question
        self.options = options

        for i, option in enumerate(options):
            cid = f"poll:vote:{message_id}:{i}" if message_id else f"poll:temp:{i}"
            self.add_item(PollVoteButton(label=option[:80], index=i, custom_id=cid))

    def create_poll_embed(self, poll_data: dict) -> discord.Embed:
        total_votes = len(poll_data["votes"])
        embed = discord.Embed(
            title=f"{poll_data['question']}",
            color=discord.Color.blue()
        )

        option_counts = [0] * len(poll_data["options"])
        for user_vote in poll_data["votes"].values():
            option_counts[user_vote] += 1

        for i, option in enumerate(poll_data["options"]):
            count = option_counts[i]
            percentage = (count / total_votes * 100) if total_votes >0 else 0

            bar_length = 10
            filled = int(percentage / 10)
            bar = "█" * filled + "░" * (bar_length - filled)

            embed.add_field(
                name=option,
                value=f"{bar} {count} votes ({percentage:.1f}%)",
                inline=False
            )

        embed.set_footer(text=f"Total Votes: {total_votes} | Persistence Active")
        return embed

class Polls(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.repo = PollRepository()
    
    async def cog_load(self):
        all_polls = await self.repo.get_all_polls()
        count = 0
        for msg_id, data in all_polls.items():
            view = PollView(self.repo, data["question"], data["options"], int(msg_id))
            self.bot.add_view(view)
            count += 1
        logger.info(f"Re-registered {count} persistent poll views")
    
    @app_commands.command(name="poll", description="Create a poll with up to 10 options")
    @app_commands.describe(
        question="The question to ask",
        option1="First option",
        option2="Second option",
        option3="Third option (optional)",
        option4="Fourth option (optional)",
        option5="Fifth option (optional)",
    )

    async def poll(
        self, 
        interaction: discord.Interaction, 
        question: str, 
        option1: str, 
        option2: str,
        option3: Optional[str] = None,
        option4: Optional[str] = None,
        option5: Optional[str] = None,
        option6: Optional[str] = None,
        option7: Optional[str] = None,
        option8: Optional[str] = None,
        option9: Optional[str] = None,
        option10: Optional[str] = None
    ):
        options = [o for o in [option1, option2, option3, option4, option5, option6, option7, option8, option9, option10] if o]

        view = PollView(self.repo, question, options)

        embed = view.create_poll_embed({"question": question, "options": options, "votes":{}})
        await interaction.response.send_message(embed=embed, view=view)

        message = await interaction.original_response()

        poll_data = {
            "question": question,
            "options": options,
            "votes": {},
            "author_id": interaction.user.id
        }

        await self.repo.save_poll(message.id, poll_data)

        persistent_view = PollView(self.repo, question, options, message.id)
        await interaction.edit_original_response(view=persistent_view)
        self.bot.add_view(persistent_view)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Polls(bot))