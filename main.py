import discord, yt_dlp, asyncio, os
from discord.ext import commands
from flask import Flask
from threading import Thread

# --- ระบบ Keep Alive แก้ปัญหา "No open ports detected" ---
app = Flask('')
@app.route('/')
def home(): return "SunSy Music is Online!"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
queues = {}

# ลิงก์รูปภาพล่าสุดของพี่ครับ
IMAGE_URL = "https://cdn.discordapp.com/attachments/1475182590557163550/1476900589056299182/ChatGPT_Image_27_.._2569_06_14_35.png?ex=69a2ce5b&is=69a17cdb&hm=31b8b15b3f09c28573943f36c43d82f86a96b39b0a01811a54df5775e9b4ce88&"

class MusicView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="ADD", style=discord.ButtonStyle.primary, emoji="➕", custom_id="add_btn")
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button): await interaction.response.send_modal(SongModal())
    @discord.ui.button(label="STOP", style=discord.ButtonStyle.danger, emoji="⏹️", custom_id="stop_btn")
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.voice_client: await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("หยุดและออกจากห้องแล้วครับ!", ephemeral=True)

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
    song_query = queues[interaction.guild.id].pop(0)
    with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'quiet': True, 'no_warnings': True}) as ydl:
        info = ydl.extract_info(f"ytsearch:{song_query}", download=False)['entries'][0]
    
    # แก้ปัญหาเสียงไม่ออก: ใช้ executable="ffmpeg"
    player = discord.FFmpegPCMAudio(info['url'], executable="ffmpeg", 
                                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", 
                                    options="-vn")
    interaction.guild.voice_client.play(player, after=lambda e: bot.loop.create_task(play_next(interaction)))
    await interaction.channel.send(f"🎵 กำลังเล่น: **{info['title']}**")

@bot.command()
async def setup(ctx):
    embed = discord.Embed(title="🎵 SunSy MUSIC", description="กดปุ่มเพื่อสั่งการบอทได้เลยครับ", color=0xffa500)
    embed.set_image(url=IMAGE_URL)
    await ctx.send(embed=embed, view=MusicView())

@bot.event
async def on_ready():
    bot.add_view(MusicView())
    print(f'บอท {bot.user} พร้อมสวยแล้วครับพี่!')

bot.run(os.environ['DISCORD_TOKEN'])
