import discord, yt_dlp, asyncio, os
from discord.ext import commands
from flask import Flask
from threading import Thread

# --- ระบบ Keep Alive ---
app = Flask('')
@app.route('/')
def home(): return "SunSy Music is Online 24/7!"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
queues = {}
IMAGE_URL = "https://cdn.discordapp.com/attachments/1463546041197658266/1476749635145039912/ChatGPT_Image_27_.._2569_06_14_35.png?ex=69a241c5&is=69a0f045&hm=b3414f35599ca69856ab2facb71158b6cc10c8a2f2ac5d5e7118a10a7ab827e4&"

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

class MusicView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="ADD", style=discord.ButtonStyle.primary, emoji="➕", custom_id="btn_add")
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button): await interaction.response.send_modal(SongModal())
    @discord.ui.button(label="PAUSE", style=discord.ButtonStyle.secondary, emoji="⏸️", custom_id="btn_pause")
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing(): interaction.guild.voice_client.pause()
    @discord.ui.button(label="RESUME", style=discord.ButtonStyle.secondary, emoji="▶️", custom_id="btn_resume")
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_paused(): interaction.guild.voice_client.resume()
    @discord.ui.button(label="STOP", style=discord.ButtonStyle.danger, emoji="⏹️", custom_id="btn_stop")
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.voice_client: await interaction.guild.voice_client.disconnect()

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

async def play_next(interaction):
    guild_id = interaction.guild.id
    if not queues.get(guild_id): return
    song = queues[guild_id].pop(0)
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(f"ytsearch:{song}", download=False)
        video = info['entries'][0]
    player = discord.FFmpegPCMAudio(video['url'], executable="/usr/bin/ffmpeg", 
                                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", 
                                    options="-vn -b:a 128k")
    interaction.guild.voice_client.play(player, after=lambda e: bot.loop.create_task(play_next(interaction)))
    await interaction.followup.send(f"🎵 กำลังเล่น: {video['title']}")

@bot.event
async def on_ready():
    bot.add_view(MusicView())
    print('บอทพร้อมทำงานแล้วครับ!')

@bot.command()
async def setup(ctx):
    embed = discord.Embed(title="🎵 SunSy MUSIC", description="กดปุ่มสั่งการบอทได้เลย", color=discord.Color.red())
    embed.set_image(url=IMAGE_URL) # นำรูปสวยๆ กลับมาแล้วครับ!
    await ctx.send(embed=embed, view=MusicView())

bot.run(os.environ['DISCORD_TOKEN'])
