import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
from flask import Flask
from threading import Thread

# --- ระบบ Keep Alive (ทำให้บอทออนไลน์ 24 ชม.) ---
app = Flask('')
@app.route('/')
def home(): return "SunSy Music is Online 24/7!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- เริ่มระบบบอท ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
queues = {}

class MusicView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="ADD", style=discord.ButtonStyle.primary, emoji="➕")
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SongModal())

    @discord.ui.button(label="PAUSE", style=discord.ButtonStyle.secondary, emoji="⏸️")
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.pause()
            await interaction.response.send_message("หยุดชั่วคราว!", ephemeral=True)

    @discord.ui.button(label="RESUME", style=discord.ButtonStyle.secondary, emoji="▶️")
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_paused():
            interaction.guild.voice_client.resume()
            await interaction.response.send_message("เล่นต่อแล้ว!", ephemeral=True)

    @discord.ui.button(label="SKIP", style=discord.ButtonStyle.secondary, emoji="⏭️")
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.voice_client:
            interaction.guild.voice_client.stop()
            await interaction.response.send_message("ข้ามเพลงแล้ว!", ephemeral=True)

    @discord.ui.button(label="STOP", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            queues[interaction.guild.id] = []
            await interaction.response.send_message("หยุดและออกจากห้องแล้วครับ!", ephemeral=True)

class SongModal(discord.ui.Modal, title='เพิ่มเพลง'):
    song = discord.ui.TextInput(label='พิมพ์ชื่อเพลงหรือลิงก์ YouTube')
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"จัดคิว: {self.song.value}")
        if interaction.guild.id not in queues: queues[interaction.guild.id] = []
        queues[interaction.guild.id].append(self.song.value)
        if not interaction.guild.voice_client or not interaction.guild.voice_client.is_playing():
            await play_next(interaction)

async def play_next(interaction):
    if not queues.get(interaction.guild.id): return
    song_query = queues[interaction.guild.id].pop(0)
    channel = interaction.user.voice.channel
    if not interaction.guild.voice_client: await channel.connect()
    with yt_dlp.YoutubeDL({'format': 'bestaudio', 'noplaylist': True}) as ydl:
        info = ydl.extract_info(f"ytsearch:{song_query}", download=False)['entries'][0]
    
    # --- แก้ไขจุดนี้: เปลี่ยนจาก ffmpeg.exe เป็น ffmpeg เฉยๆ ---
    player = discord.FFmpegPCMAudio(info['url'], executable="ffmpeg", 
                                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", 
                                    options="-vn")
    
    interaction.guild.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(interaction), bot.loop))
    await interaction.followup.send(f"กำลังเล่น: {info['title']}")

@bot.event
async def on_ready():
    bot.add_view(MusicView())
    print(f'บอท {bot.user} พร้อมลุย 24 ชม. แล้วครับพี่!')

@bot.command()
async def setup(ctx):
    embed = discord.Embed(title="🎵 SunSy MUSIC", description="บอทพร้อมทำงาน 24 ชม.", color=discord.Color.red())
    await ctx.send(embed=embed, view=MusicView())

# --- เปิดระบบ 24/7 ---
keep_alive()
# --- แก้ไขจุดนี้: ดึง Token จาก Environment ---
bot.run(os.environ['DISCORD_TOKEN'])
