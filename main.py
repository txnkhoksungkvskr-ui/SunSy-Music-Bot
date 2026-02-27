import discord, yt_dlp, asyncio, os
from discord.ext import commands
from flask import Flask
from threading import Thread

# 1. ระบบ Keep Alive กัน Render เตะ (ทำงานได้ดีจาก Log ล่าสุด)
app = Flask('')
@app.route('/')
def home(): return "SunSy Music is Online!"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
queues = {}

# ลิงก์รูปภาพที่เสถียรที่สุด (จาก Discord โดยตรง)
IMAGE_URL = "https://cdn.discordapp.com/attachments/1463546041197658266/1476726406120472668/ChatGPT_Image_27_.._2569_06_14_35.png"

class MusicView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="➕ ADD", style=discord.ButtonStyle.primary, custom_id="add")
    async def add(self, i: discord.Interaction, b: discord.ui.Button): await i.response.send_modal(SongModal())
    @discord.ui.button(label="⏸️ PAUSE", style=discord.ButtonStyle.secondary, custom_id="pause")
    async def pause(self, i: discord.Interaction, b: discord.ui.Button):
        if i.guild.voice_client: i.guild.voice_client.pause()
        await i.response.send_message("หยุดชั่วคราว", ephemeral=True)
    @discord.ui.button(label="▶️ RESUME", style=discord.ButtonStyle.secondary, custom_id="resume")
    async def resume(self, i: discord.Interaction, b: discord.ui.Button):
        if i.guild.voice_client: i.guild.voice_client.resume()
        await i.response.send_message("เล่นต่อ", ephemeral=True)
    @discord.ui.button(label="⏭️ SKIP", style=discord.ButtonStyle.secondary, custom_id="skip")
    async def skip(self, i: discord.Interaction, b: discord.ui.Button):
        if i.guild.voice_client: i.guild.voice_client.stop()
        await i.response.send_message("ข้ามเพลง", ephemeral=True)
    @discord.ui.button(label="⏹️ STOP", style=discord.ButtonStyle.danger, custom_id="stop")
    async def stop(self, i: discord.Interaction, b: discord.ui.Button):
        if i.guild.voice_client: await i.guild.voice_client.disconnect()
        queues[i.guild.id] = []
        await i.response.send_message("ออกจากห้อง", ephemeral=True)

class SongModal(discord.ui.Modal, title='เพิ่มเพลง'):
    song = discord.ui.TextInput(label='พิมพ์ชื่อเพลงหรือลิงก์ YouTube')
    async def on_submit(self, i: discord.Interaction):
        await i.response.defer()
        if i.guild.id not in queues: queues[i.guild.id] = []
        queues[i.guild.id].append(self.song.value)
        
        # เชื่อมต่อเสียงแบบ Forced (แก้ปัญหาเสียงไม่ออก)
        if not i.guild.voice_client:
            if i.user.voice:
                await i.user.voice.channel.connect(reconnect=True, timeout=20)
            else:
                return await i.followup.send("พี่เข้าห้องเสียงก่อนครับ!", ephemeral=True)
        
        if not i.guild.voice_client.is_playing():
            await play_next(i)
        await i.followup.send(f"✅ คิว: {self.song.value}", ephemeral=True)

async def play_next(i):
    if not queues.get(i.guild.id) or not i.guild.voice_client: return
    song_query = queues[i.guild.id].pop(0)
    
    ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'no_warnings': True, 'source_address': '0.0.0.0'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{song_query}", download=False)['entries'][0]
    
    # ปรับแต่ง FFmpeg ให้เหมาะกับ Server Render (Linux)
    ffmpeg_opts = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn -filter:a "volume=1.0"'
    }
    
    source = discord.FFmpegPCMAudio(info['url'], executable="ffmpeg", **ffmpeg_opts)
    i.guild.voice_client.play(source, after=lambda e: bot.loop.create_task(play_next(i)))
    await i.channel.send(f"🎵 กำลังเล่น: **{info['title']}**")

@bot.command()
async def setup(ctx):
    embed = discord.Embed(title="🎵 SunSy MUSIC", description="กดปุ่มเพื่อสั่งการบอท", color=0xffa500)
    embed.set_image(url=IMAGE_URL)
    await ctx.send(embed=embed, view=MusicView())

@bot.event
async def on_ready():
    bot.add_view(MusicView())
    print(f'SunSy Music พร้อม! (Port 8080 Open)')

bot.run(os.environ['DISCORD_TOKEN'])
