import discord, yt_dlp, asyncio, os
from discord.ext import commands
from flask import Flask
from threading import Thread

# 1. ระบบ Keep Alive (กัน Render เตะบอท)
app = Flask('')
@app.route('/')
def home(): return "SunSy Music is Online!"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
queues = {}

# 2. ตั้งค่าการเล่นเพลง (ใช้ FFmpeg ตรงๆ)
YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': True}
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

class MusicView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # ห้ามตั้ง timeout เพื่อให้ปุ่มค้างตลอด

    @discord.ui.button(label="ADD", style=discord.ButtonStyle.primary, emoji="➕", custom_id="add")
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SongModal())

    @discord.ui.button(label="STOP", style=discord.ButtonStyle.danger, emoji="⏹️", custom_id="stop")
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("หยุดและออกจากห้องแล้ว!", ephemeral=True)

class SongModal(discord.ui.Modal, title='เพิ่มเพลง'):
    song = discord.ui.TextInput(label='พิมพ์ชื่อเพลงหรือลิงก์ YouTube')
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.guild.id not in queues: queues[interaction.guild.id] = []
        queues[interaction.guild.id].append(self.song.value)
        if not interaction.guild.voice_client or not interaction.guild.voice_client.is_playing():
            if interaction.user.voice:
                await interaction.user.voice.channel.connect()
                await play_next(interaction)
        await interaction.followup.send(f"✅ เพิ่มลงคิว: {self.song.value}", ephemeral=True)

async def play_next(interaction):
    if not queues.get(interaction.guild.id): return
    song = queues[interaction.guild.id].pop(0)
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(f"ytsearch:{song}", download=False)['entries'][0]
    
    # ใช้ executable="ffmpeg" (ต้องมีใน Aptfile แล้ว)
    player = discord.FFmpegPCMAudio(info['url'], executable="ffmpeg", **FFMPEG_OPTIONS)
    interaction.guild.voice_client.play(player, after=lambda e: bot.loop.create_task(play_next(interaction)))
    await interaction.channel.send(f"🎵 กำลังเล่น: **{info['title']}**")

@bot.command()
async def setup(ctx):
    embed = discord.Embed(title="🎵 SunSy MUSIC", description="กดปุ่มเพื่อสั่งการบอทครับ", color=0xffa500)
    await ctx.send(embed=embed, view=MusicView())

@bot.event
async def on_ready():
    bot.add_view(MusicView()) # คำสั่งนี้สำคัญมาก: โหลดปุ่มให้กลับมาทำงาน
    print('บอทตื่นแล้ว!')

bot.run(os.environ['DISCORD_TOKEN'])
