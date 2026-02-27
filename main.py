import discord, yt_dlp, asyncio, os
from discord.ext import commands
from flask import Flask
from threading import Thread

# Web server for Render
app = Flask('')
@app.route('/')
def home(): return "SunSy Music is Online!"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
queues = {}

# ใช้ลิงก์ภาพที่ผมดึงมาให้ใหม่ (เป็น CDN ของ Discord โดยตรง)
IMAGE_URL = "https://cdn.discordapp.com/attachments/1463546041197658266/1476726406120472668/ChatGPT_Image_27_.._2569_06_14_35.png"

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
        await i.response.send_message("ข้ามแล้ว", ephemeral=True)
    @discord.ui.button(label="⏹️ STOP", style=discord.ButtonStyle.danger, custom_id="stop")
    async def stop(self, i: discord.Interaction, b: discord.ui.Button):
        if i.guild.voice_client: await i.guild.voice_client.disconnect()
        await i.response.send_message("บอทออกแล้ว", ephemeral=True)

class SongModal(discord.ui.Modal, title='เพิ่มเพลง'):
    song = discord.ui.TextInput(label='พิมพ์ชื่อเพลงหรือลิงก์ YouTube')
    async def on_submit(self, i: discord.Interaction):
        await i.response.defer()
        if i.guild.id not in queues: queues[i.guild.id] = []
        queues[i.guild.id].append(self.song.value)
        if not i.guild.voice_client:
            if i.user.voice: await i.user.voice.channel.connect()
            else: return await i.followup.send("พี่ต้องอยู่ในห้องเสียงก่อนครับ!")
        if not i.guild.voice_client.is_playing(): await play_next(i)
        else: await i.followup.send(f"✅ เพิ่มคิว: {self.song.value}")

async def play_next(i):
    if not queues.get(i.guild.id) or not i.guild.voice_client: return
    song = queues[i.guild.id].pop(0)
    with yt_dlp.YoutubeDL({'format': 'bestaudio', 'quiet': True}) as ydl:
        info = ydl.extract_info(f"ytsearch:{song}", download=False)['entries'][0]
    
    # เพิ่ม options=-vn เพื่อตัดภาพออกและเน้นเสียง
    player = discord.FFmpegPCMAudio(info['url'], executable="ffmpeg", 
                                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", 
                                    options="-vn -b:a 128k")
    i.guild.voice_client.play(player, after=lambda e: bot.loop.create_task(play_next(i)))
    try: await i.channel.send(f"🎵 กำลังเล่น: {info['title']}")
    except: pass

@bot.command()
async def setup(ctx):
    embed = discord.Embed(title="🎵 SunSy MUSIC", description="กดปุ่มเพื่อสั่งงาน", color=0xffa500)
    embed.set_image(url=IMAGE_URL)
    await ctx.send(embed=embed, view=MusicView())

@bot.event
async def on_ready():
    bot.add_view(MusicView())
    print('บอทพร้อมทำงาน!')

bot.run(os.environ['DISCORD_TOKEN'])
