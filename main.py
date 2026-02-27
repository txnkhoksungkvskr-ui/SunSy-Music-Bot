import discord, yt_dlp, asyncio, os
from discord.ext import commands
from flask import Flask
from threading import Thread

# --- ระบบ Keep Alive ---
app = Flask('')
@app.route('/')
def home(): return "SunSy Music is Online!"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
queues = {}

# ลิงก์รูปภาพแบบถาวร (ไม่มีวันหมดอายุ)
IMAGE_URL = "https://i.imgur.com/k6uO5iW.jpeg" 

class MusicView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="➕ ADD", style=discord.ButtonStyle.primary, custom_id="add")
    async def add(self, i: discord.Interaction, b: discord.ui.Button): await i.response.send_modal(SongModal())
    @discord.ui.button(label="⏸️ PAUSE", style=discord.ButtonStyle.secondary, custom_id="pause")
    async def pause(self, i: discord.Interaction, b: discord.ui.Button):
        if i.guild.voice_client and i.guild.voice_client.is_playing(): i.guild.voice_client.pause()
        await i.response.send_message("หยุดชั่วคราว", ephemeral=True)
    @discord.ui.button(label="▶️ RESUME", style=discord.ButtonStyle.secondary, custom_id="resume")
    async def resume(self, i: discord.Interaction, b: discord.ui.Button):
        if i.guild.voice_client and i.guild.voice_client.is_paused(): i.guild.voice_client.resume()
        await i.response.send_message("เล่นต่อแล้ว", ephemeral=True)
    @discord.ui.button(label="⏭️ SKIP", style=discord.ButtonStyle.secondary, custom_id="skip")
    async def skip(self, i: discord.Interaction, b: discord.ui.Button):
        if i.guild.voice_client: i.guild.voice_client.stop()
        await i.response.send_message("ข้ามเพลงแล้ว", ephemeral=True)
    @discord.ui.button(label="⏹️ STOP", style=discord.ButtonStyle.danger, custom_id="stop")
    async def stop(self, i: discord.Interaction, b: discord.ui.Button):
        if i.guild.voice_client: await i.guild.voice_client.disconnect()
        await i.response.send_message("หยุดบอท", ephemeral=True)

class SongModal(discord.ui.Modal, title='เพิ่มเพลง'):
    song = discord.ui.TextInput(label='ชื่อเพลงหรือลิงก์ YouTube')
    async def on_submit(self, i: discord.Interaction):
        await i.response.defer()
        if i.guild.id not in queues: queues[i.guild.id] = []
        queues[i.guild.id].append(self.song.value)
        if not i.guild.voice_client or not i.guild.voice_client.is_playing():
            if i.user.voice: await i.user.voice.channel.connect()
            await play_next(i)
        await i.followup.send(f"✅ เพิ่ม: {self.song.value}", ephemeral=True)

async def play_next(i):
    if not queues.get(i.guild.id) or not i.guild.voice_client: return
    song = queues[i.guild.id].pop(0)
    with yt_dlp.YoutubeDL({'format': 'bestaudio', 'quiet': True}) as ydl:
        info = ydl.extract_info(f"ytsearch:{song}", download=False)['entries'][0]
    player = discord.FFmpegPCMAudio(info['url'], executable="ffmpeg", before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn")
    i.guild.voice_client.play(player, after=lambda e: bot.loop.create_task(play_next(i)))
    try: await i.channel.send(f"🎵 กำลังเล่น: {info['title']}")
    except: pass

@bot.command()
async def setup(ctx):
    embed = discord.Embed(title="🎵 SunSy MUSIC", description="กดปุ่มสั่งการบอทเลย", color=0xffa500)
    embed.set_image(url=IMAGE_URL)
    await ctx.send(embed=embed, view=MusicView())

@bot.event
async def on_ready():
    bot.add_view(MusicView())
    print('บอทพร้อม! ปุ่มโหลดครบ!')

bot.run(os.environ['DISCORD_TOKEN'])
