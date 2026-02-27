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

# ลิงก์รูปภาพที่พี่ให้มา
IMAGE_URL = "https://cdn.discordapp.com/attachments/1463546041197658266/1476749635145039912/ChatGPT_Image_27_.._2569_06_14_35.png?ex=69a241c5&is=69a0f045&hm=b3414f35599ca69856ab2facb71158b6cc10c8a2f2ac5d5e7118a10a7ab827e4&"

class MusicView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # ตั้งค่าให้ปุ่มทำงานตลอดไป

    @discord.ui.button(label="ADD", style=discord.ButtonStyle.primary, emoji="➕", custom_id="btn_add")
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SongModal())

    @discord.ui.button(label="PAUSE", style=discord.ButtonStyle.secondary, emoji="⏸️", custom_id="btn_pause")
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.pause()
            await interaction.response.send_message("หยุดชั่วคราว!", ephemeral=True)

    @discord.ui.button(label="RESUME", style=discord.ButtonStyle.secondary, emoji="▶️", custom_id="btn_resume")
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_paused():
            interaction.guild.voice_client.resume()
            await interaction.response.send_message("เล่นต่อแล้ว!", ephemeral=True)

    @discord.ui.button(label="SKIP", style=discord.ButtonStyle.secondary, emoji="⏭️", custom_id="btn_skip")
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.voice_client:
            interaction.guild.voice_client.stop()
            await interaction.response.send_message("ข้ามเพลงแล้ว!", ephemeral=True)

    @discord.ui.button(label="STOP", style=discord.ButtonStyle.danger, emoji="⏹️", custom_id="btn_stop")
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            queues[interaction.guild.id] = []
            await interaction.response.send_message("หยุดและออกจากห้องแล้วครับ!", ephemeral=True)

class SongModal(discord.ui.Modal, title='เพิ่มเพลง'):
    song = discord.ui.TextInput(label='พิมพ์ชื่อเพลงหรือลิงก์ YouTube')
    async def on_submit(self, interaction: discord.Interaction):
        # ป้องกัน Error ถ้าหาเพลงไม่เจอ
        await interaction.response.defer() # บอก Discord ว่ากำลังประมวลผล
        if interaction.guild.id not in queues: queues[interaction.guild.id] = []
        queues[interaction.guild.id].append(self.song.value)
        
        if not interaction.guild.voice_client or not interaction.guild.voice_client.is_playing():
            # ตรวจสอบว่าผู้ใช้อยู่ในห้องเสียงไหม
            if interaction.user.voice:
                await play_next(interaction)
            else:
                await interaction.followup.send("พี่ต้องเข้าห้องเสียงก่อนสั่งเล่นเพลงนะ!", ephemeral=True)

async def play_next(interaction):
    if not queues.get(interaction.guild.id) or len(queues[interaction.guild.id]) == 0:
        return
    
    song_query = queues[interaction.guild.id].pop(0)
    channel = interaction.user.voice.channel
    
    # เชื่อมต่อห้องเสียงถ้ายังไม่ได้เชื่อมต่อ
    if not interaction.guild.voice_client:
        try:
            await channel.connect()
        except Exception as e:
            await interaction.followup.send(f"เชื่อมต่อห้องเสียงไม่ได้: {e}", ephemeral=True)
            return
        
    # ปรับปรุงระบบค้นหาเพลง ป้องกัน IndexOutofRange
    with yt_dlp.YoutubeDL({'format': 'bestaudio', 'noplaylist': True, 'quiet': True}) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{song_query}", download=False)
            if 'entries' in info and len(info['entries']) > 0:
                video_info = info['entries'][0]
            else:
                await interaction.followup.send("หาเพลงไม่เจอครับพี่ ลองชื่ออื่นดูนะ!", ephemeral=True)
                return
        except Exception as e:
            await interaction.followup.send(f"เกิดข้อผิดพลาดในการดึงข้อมูลเพลง: {e}", ephemeral=True)
            return
    
    # ใช้ executable="ffmpeg" (ต้องมั่นใจว่าติดตั้งใน Aptfile แล้ว)
    player = discord.FFmpegPCMAudio(video_info['url'], executable="ffmpeg", 
                                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", 
                                    options="-vn")
    
    # เล่นเพลงและตั้งค่าให้เล่นเพลงถัดไปอัตโนมัติ
    interaction.guild.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(interaction), bot.loop))
    await interaction.followup.send(f"กำลังเล่น: {video_info['title']}")

@bot.event
async def on_ready():
    bot.add_view(MusicView()) # โหลดปุ่มแบบถาวร
    print(f'บอท {bot.user} พร้อมลุย 24 ชม. แล้วครับพี่!')

@bot.command()
async def setup(ctx):
    # สร้าง Embed และใส่รูปภาพที่พี่ให้มา
    embed = discord.Embed(title="🎵 SunSy MUSIC", description="กดปุ่มสั่งการบอทได้เลย", color=discord.Color.red())
    embed.set_image(url=IMAGE_URL) # ใส่รูปภาพลงใน Embed
    await ctx.send(embed=embed, view=MusicView())

# --- เปิดระบบ 24/7 ---
keep_alive()
# --- ดึง Token จาก Environment ---
bot.run(os.environ['DISCORD_TOKEN'])
