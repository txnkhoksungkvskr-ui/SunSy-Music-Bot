import discord, yt_dlp, asyncio, os
from discord.ext import commands
from flask import Flask
from threading import Thread

# --- ระบบ Keep Alive (ต้องมีเพื่อให้ Render มองเห็น Port) ---
app = Flask('')
@app.route('/')
def home(): return "SunSy Music is Online 24/7!"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
queues = {}

# ตั้งค่าให้หลบการตรวจจับของ YouTube
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

class MusicView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="ADD", style=discord.ButtonStyle.primary, emoji="➕")
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SongModal())
    @discord.ui.button(label="STOP", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("หยุดแล้วครับ!", ephemeral=True)

class SongModal(discord.ui.Modal, title='เพิ่มเพลง'):
    song = discord.ui.TextInput(label='พิมพ์ชื่อเพลงหรือลิงก์ YouTube')
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer() # ใช้ defer แทน send_message เพื่อกัน Error
        if interaction.guild.id not in queues: queues[interaction.guild.id] = []
        queues[interaction.guild.id].append(self.song.value)
        if not interaction.guild.voice_client or not interaction.guild.voice_client.is_playing():
            if interaction.user.voice:
                await interaction.user.voice.channel.connect()
                await play_next(interaction)
        await interaction.followup.send(f"จัดคิว: {self.song.value}")

async def play_next(interaction):
    if not queues.get(interaction.guild.id): return
    song_query = queues[interaction.guild.id].pop(0)
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(f"ytsearch:{song_query}", download=False)['entries'][0]
    
    player = discord.FFmpegPCMAudio(info['url'], executable="ffmpeg", 
                                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", 
                                    options="-vn")
    
    interaction.guild.voice_client.play(player, after=lambda e: bot.loop.create_task(play_next(interaction)))
    try: await interaction.followup.send(f"กำลังเล่น: {info['title']}")
    except: pass

@bot.command()
async def setup(ctx):
    embed = discord.Embed(title="🎵 SunSy MUSIC", description="กดปุ่มสั่งการบอทได้เลย", color=discord.Color.red())
    embed.set_image(url="https://cdn.discordapp.com/attachments/1463546041197658266/1476726406120472668/ChatGPT_Image_27_.._2569_06_14_35.png")
    await ctx.send(embed=embed, view=MusicView())

bot.run(os.environ['DISCORD_TOKEN'])
