import aiohttp
import html
import logging
import random
from typing import Dict, Optional
import discord
from discord import app_commands
from discord.ext import commands
from utils.repositories import TriviaRepository, CustomTriviaRepository

logger = logging.getLogger(__name__)

MAX_LABEL_LENGTH = 80
TRIVIA_TIMEOUT = 60.0

