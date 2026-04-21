import logging
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class UtilityBot(commands.Bot):
    # The main bot class

    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        super().__init__(
            command_prefix=commands.when_mentioned_or('!'),
            intents=intents,
            help_command=None
        )

    async def setup_hook(self) -> None:
        # Before startup, for extensions
        initial_extensions = [
            "cogs.sanity",
            "cogs.study_timer",
            "cogs.trivia",
            "cogs.moderation",
            "cogs.leveling",
            "cogs.tasks",
            "cogs.events"
        ]   

        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
                logger.info(f"Loaded extension: {extension}")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")

        # Sync app commands to Discord
        await self.tree.sync()
        logger.info("Sync complete")

    async def on_ready(self) -> None:
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info("Setup complete.")

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # env vars from .env file
    load_dotenv()
    token = os.getenv("DISCORD_BOT_TOKEN")

    if not token or token == "your_bot_token_here":
        logger.error("Can't find bot token.")
        return

    bot = UtilityBot()
    bot.run(token, log_handler=None)

if __name__ == "__main__":
    main()                    

# js pushing a redeploy