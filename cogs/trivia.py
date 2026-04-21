import aiohttp
import html
import logging
import random
from typing import Dict, Optional
import discord
from discord import app_commands
from discord.ext import commands
from utils.repositories import TriviaRepository, CustomTriviaRepository, EconomyRepository

logger = logging.getLogger(__name__)

MAX_LABEL_LENGTH = 80
TRIVIA_TIMEOUT = 60.0

TRIVIA_CATEGORIES = [
    app_commands.Choice(name="Any", value=0),
    app_commands.Choice(name="Server Custom", value=-1),
    app_commands.Choice(name="General Knowledge", value=9),
    app_commands.Choice(name="Books", value=10),
    app_commands.Choice(name="Film", value=11),
    app_commands.Choice(name="Music", value=12),
    app_commands.Choice(name="Video Games", value=15),
    app_commands.Choice(name="Computers", value=18)
]

class TriviaView(discord.ui.View):
    def __init__(self, cog: "TriviaGame", user_id: int, guild_id: Optional[int], correct_answer : str, answers: list[str], is_party_mode: bool = False):
        super().__init__(timeout=TRIVIA_TIMEOUT)
        self.cog = cog
        self.user_id = user_id
        self.guild_id = guild_id
        self.correct_answer = correct_answer
        self.is_party_mode = is_party_mode

        for ans in answers:
            btn = discord.ui.Button(label=ans[:MAX_LABEL_LENGTH], style=discord.ButtonStyle.primary)
            btn.callback = self.make_callback(btn, ans)
            self.add_item(btn)

    def make_callback(self, button: discord.ui.Button, answer_text: str):
        async def callback(interaction: discord.Interaction):
            if not self.is_party_mode and interaction.user.id != self.user_id:
                await interaction.response.send_message("This isn't your question, use /trivia to play your own", ephemeral=True)
                return
            
            is_correct = (answer_text == self.correct_answer)

            for child in self.children:
                child.disabled = True
                if isinstance(child, discord.ui.Button):
                    if child.label == self.correct_answer[:MAX_LABEL_LENGTH]:
                        child.style = discord.ButtonStyle.success
                    elif child.label == button.label and not is_correct:
                        child.style = discord.ButtonStyle.danger
            
            if is_correct:
                credits_reward = 25 if self.is_party_mode else 10
                if self.guild_id:
                    self.cog.bot.loop.create_task(self.cog.repo.add_score(self.guild_id, interaction.user.id, 1))
                    self.cog.bot.loop.create_task(self.cog.economy_repo.add_balance(self.guild_id, interaction.user.id, credits_reward))
                
                if self.is_party_mode:
                    result_msg = f"Correct answer. {interaction.user.mention} got it first. +1 point and {credits_reward} credits"
                else:
                    result_msg = f"Correct. You got 1 point and {credits_reward} credits"

            else:
                if self.is_party_mode:
                    result_msg = f"Wrong! {interaction.user.mention} guessed wrong. Right answer: {self.correct_answer}"
                else:
                    result_msg = f"Wrong! The right answer was {self.correct_answer}"

            content = interaction.message.content.split("\n\nResult:")[0] if interaction.message.content else "Trivia Question"
            await interaction.response.edit_message(content=f"{content}\n\nResult: {result_msg}", view=self)
            self.stop()
        return callback
    
class TriviaGame(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.repo = TriviaRepository()
        self.custom_repo = CustomTriviaRepository()
        self.economy_repo = EconomyRepository()
        self.session: Optional[aiohttp.ClientSession] = None

    async def cog_load(self) -> None:
        self.session(aiohttp.ClientSession)

    async def cog_unload(self) -> None:
        if self.session:
            await self.session.close()
    
    async def _fetch_questions(self, category_id: int = 0) -> Optional[dict]:
        url = "https://opentdb.com/api.php?amount=1&type=multiple"
        if category_id > 0:
            url += f"&category={category_id}"

        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("results") and len(data["results"]) > 0:
                        return data["results"][0]
        except Exception as e:
            logger.error(f"Error fetching trivia: {e}")
        return None
    
    trivia = app_commands.Group(name="trivia", description="Play a trivia game")

    async def _send_trivia(self, interaction: discord.Interaction, category: int, is_party_mode: bool):
        await interaction.response.defer()

        if category == -1:
            if not interaction.guild_id:
                await interaction.followup.send("Custom trivia is only available in servers")
                return
            custom_questions = await self.custom_repo.get_questions(interaction.guild_id)
            if not custom_questions:
                await interaction.followup.send("This server doesn't have custom questions yet. Use /trivia add_custom to add one")
                return
            
            question_data = random.choice(custom_questions)
            question_text = question_data["question"]
            correct_answer = question_data["correct_answer"]
            incorrect_answers = question_data["incorrect_answers"]
            category_name = "Server Custom"
            difficulty = "Custom"
        
        else:
            question_data = await self._fetch_question(category)
            if not question_data:
                await interaction.followup.send("Failed to fetch a trivia question from OpenTDB. Try again later")
                return
            
            question_text = html.unescape(question_data["question"])
            correct_answer = html.unescape(question_data["correct_answer"])
            incorrect_answers = [html.unescape(ans) for ans in question_data["incorrect_answers"]]
            category_name = html.unescape(question_data["category"])
            difficulty = question_data["difficulty"].capitalize()
        
        all_answers = incorrect_answers + [correct_answer]
        random.shuffle(all_answers)

        mode_str = "PARTY TRIVIA. First answer wins\n\n" if is_party_mode else " "
        content = f"{mode_str}Category: {category_name} | Difficulty: {difficulty}\n\nQuestion: {question_text}"

        view = TriviaView(
            cog=self,
            user_id=interaction.user.id,
            guild_id=interaction.guild_id,
            correct_answer=correct_answer,
            answers=all_answers,
            is_party_mode=is_party_mode
        )

        await interaction.followup.send(content=content, view=view)
    
    @trivia.command(name="play", description="get a solo trivia question")
    @app_commands.describe(category="Optional category to pick")
    @app_commands.choices(category=TRIVIA_CATEGORIES)
    async def trivia_play(self, interaction: discord.Interaction, category: int = 0) -> None:
        await self._send_trivia(interaction, category, is_party_mode=False)
    
    @trivia.command(name="party", description="Multiplayer trivia question")
    @app_commands.describe(category="Optional category to pick")
    @app_commands.choices(category=TRIVIA_CATEGORIES)
    async def trivia_party(self, interaction: discord.Interaction, category: int = 0) -> None:
        await self._send_trivia(interaction, category, is_party_mode=True)
    
    @trivia.command(name="leaderboard", description="Trivia GOATs")
    async def trivia_leaderboard(self, interaction: discord.Interaction) -> None:
        if not interaction.guild_id:
            await interaction.response.send_message("Leaderboards are only available in servers", ephemeral=True)
            return
        
        guild_scores = await self.repo.get_guild_scores(interaction.guild_id)

        if not guild_scores:
            await interaction.response.send_message("No one has any trivia score")
            return
        
        sorted_scores = sorted(guild_scores.items(), key=lambda item: item[1], reverse=True)
        top_5 = sorted_scores[:5]
        
        embed = discord.Embed(title=f"Trivia Leaderboard - {interaction.guild.name}", color=discord.Color.gold())

        description = " "
        for idx, (user_id_str, score) in enumerate(top_5, 1):
            description += f"{idx}. <@{user_id_str}> - {score} pts\n"
        
        embed.description = description
        await interaction.response.send_message(embed=embed)

    @trivia.command(name="add_custom", description="Add a custom question")
    @app_commands.describe(
        question="The trivia question",
        correct = "The correct answer",
        wrong1 = "first wrong answer",
        wrong2 = "Second wrong answer",
        wrong3 = "Third wrong answer"
    )
    async def trivia_add_custom(self, interaction: discord.Interaction, question: str, correct: str, wrong1 : str, wrong2: str, wrong3: str) -> None:
        if not interaction.guild_id:
            await interaction.response.send_message("You can only do this in servers", ephemeral=True)
            return
        
        incorrect_answers = [wrong1, wrong2, wrong3]
        await self.custom_repo.add_question(
            interaction.guild_id,
            question,
            correct,
            incorrect_answers,
            interaction.user.id
        )

        await interaction.response.send_message(f"Added custom question: {question}", ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TriviaGame(bot))
    



