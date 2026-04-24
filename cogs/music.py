import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import yt_dlp
import logging
from functools import partial

logger = logging.getLogger(__name__)


def silence_bug_reports(*args, **kwargs):
    return ''
yt_dlp.utils.bug_reports_message = silence_bug_reports

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'youtube_include_dash_manifest': False,
    'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')
        self.webpage_url = data.get('webpage_url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        
        def fetch_data():
            return ytdl.extract_info(url, download=not stream)

        data = await loop.run_in_executor(None, fetch_data)

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)




class MusicPlayer:
    def __init__(self, interaction, cog):
        self.bot = interaction.client
        self.guild = interaction.guild
        self._channel = interaction.channel
        self._cog = cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None
        self.volume = 0.5
        self.current = None

        self.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()
            try:
                async with asyncio.timeout(300):
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self.guild)

            if not isinstance(source, YTDLSource):
                try:
                    source = await YTDLSource.from_url(source, loop=self.bot.loop, stream=True)
                except Exception as e:
                    await self._channel.send(f'Error processing song: {e}')
                    continue
            
            source.volume = self.volume
            self.current = source

            if not self.guild.voice_client:
                await self._channel.send("I've been disconnected from voice!")
                return self.destroy(self.guild)

            def toggle_next(*args, **kwargs):
                self.bot.loop.call_soon_threadsafe(self.next.set)

            self.guild.voice_client.play(source, after=toggle_next)
            
            embed = discord.Embed(title="Now Playing 🎵", description=f"[{source.title}]({source.webpage_url})", color=discord.Color.green())
            embed.set_thumbnail(url=source.thumbnail)
            self.np = await self._channel.send(embed=embed)

            await self.next.wait()

            source.cleanup()
            self.current = None

    def destroy(self, guild):
        return self.bot.loop.create_task(self._cog.cleanup(guild))
            
    def destroy(self, guild):
        return self.bot.loop.create_task(self._cog.cleanup(guild))


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = {}
    
    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass
    
    def get_player(self, interaction):
        try: 
            player = self.players[interaction.guild_id]
        except KeyError:
            player = MusicPlayer(interaction, self)
            self.players[interaction.guild_id] = player

        return player

    @app_commands.command(name="mplay", description="Play music from URL or search term.")
    async def mplay(self, interaction: discord.Interaction, search: str):
        await interaction.response.defer()
        
        vc = interaction.guild.voice_client

        if not vc:
            if not interaction.user.voice:
                return await interaction.followup.send("You are not in a voice channel!", ephemeral=True)

            await interaction.user.voice.channel.connect()
            vc = interaction.guild.voice_client
        
        player = self.get_player(interaction)

        try:
            source = await YTDLSource.from_url(search, loop=self.bot.loop, stream=True)
        except Exception as e:
            return await interaction.followup.send(f"An error occurred: {e}")
        
        await player.queue.put(source)
        await interaction.followup.send(f"Queued: **{source.title}** ✅")
    
    @app_commands.command(name="mskip", description="Skip the current song.")
    async def mskip(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client

        if not vc or not vc.is_playing():
            return await interaction.response.send_message("Nothing is playing.", ephemeral=True)
        
        vc.stop()
        await interaction.response.send_message("Skipped! ⏭️")
    
    @app_commands.command(name="mstop", description="Stop the music and disconnect.")
    async def mstop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client

        if not vc:
            return await interaction.response.send_message("Not connected to a voice channel.", ephemeral=True)
        
        await self.cleanup(interaction.guild)
        await interaction.response.send_message("Stopped and disconnected. 👋")
    
    @app_commands.command(name="mqueue", description="Show the current music queue.")
    async def mqueue(self, interaction: discord.Interaction):
        player = self.get_player(interaction)
        if player.queue.empty():
            return await interaction.response.send_message("The queue is currently empty.")
        
        upcoming = list(player.queue._queue)[:10]
        
        fmt = '\n'.join(f"**{i+1}.** {song.title}" for i, song in enumerate(upcoming))
        embed = discord.Embed(title=f'Queue - Next {len(upcoming)} Songs', description=fmt, color=discord.Color.blue())

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="mnow_playing", description="Show details of the current song.")
    async def mnow_playing(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client

        if not vc or not vc.is_connected():
            return await interaction.response.send_message("Not connected to a voice channel.", ephemeral=True)
        
        player = self.get_player(interaction)
        if not player.current:
            return await interaction.response.send_message("Nothing is currently playing.")

        embed = discord.Embed(title="Now Playing 🎵", description=f"[{player.current.title}]({player.current.webpage_url})", color=discord.Color.green())
        embed.set_thumbnail(url=player.current.thumbnail)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Music(bot))
