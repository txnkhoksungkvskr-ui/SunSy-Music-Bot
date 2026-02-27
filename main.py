import discord, yt_dlp, asyncio, os
from discord.ext import commands
from flask import Flask
from threading import Thread

# --- ระบบ Keep Alive ---
app = Flask('')
@app.route('/')
def home(): return "SunSy Music is Online 24/7!"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
queues = {}
IMAGE_URL = "https://cdn.discordapp.com/attachments/1463546041197658266/1476749635145039912/ChatGPT_Image_27_.._2569_06_14_35.png?ex=69a241c5&is=69a0f045&hm=b3414f35599ca69856ab2facb71158b6cc10c8a2f2ac5d5e7118a10a7ab827e4&"

# สูตรลับ: ปรับ User-Agent ให้เหมือน Browser เพื่อหลบการบล็อก
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

class MusicView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

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

    @discord.ui.button(label="STOP", style=discord.ButtonStyle.danger, emoji="⏹️", custom_id="btn_stop")
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("หยุดและออกจากห้องแล้วครับ!", ephemeral=True)

class SongModal(discord.ui.Modal, title='เพิ่มเพลง'):
    song = discord.ui.TextInput(label='พิมพ์ชื่อเพลงหรือลิงก์ YouTube')
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.guild.id not in queues: queues[interaction.guild.id] = []
        queues[interaction.guild.id].append(self.song.value)
        if not interaction.guild.voice_client or not interaction.guild.voice_client.is_playing():
            await play_next(interaction)

async def play_next(interaction):
    if not queues.get(interaction.guild.id): return
    song = queues[interaction.guild.id].pop(0)
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{song}", download=False)
            video = info['entries'][0]
        except Exception as e:
            return await interaction.followup.send(f"หาเพลงไม่เจอครับ: {e}")
    
    player = discord.FFmpegPCMAudio(video['url'], executable="ffmpeg", 
                                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", 
                                    options="-vn")
    
    interaction.guild.voice_client.play(player, after=lambda e: bot.loop.create_task(play_next(interaction)))
    await interaction.followup.send(f"กำลังเล่น: {video['title']}")

@bot.event
async def on_ready():
    bot.add_view(MusicView())
    print(f'บอท {bot.user} พร้อมสวยและเสถียรแล้วครับพี่!')

@bot.command()
async def setup(ctx):
    embed = discord.Embed(title="🎵 SunSy MUSIC", description="กดปุ่มสั่งการบอท หรือพิมพ์ !play ได้เลยครับ", color=discord.Color.red())
    embed.set_image(url=IMAGE_URL) # รูปภาพสุดสวยของพี่
    await ctx.send(embed=embed, view=MusicView())

@bot.command()
async def play(ctx, *, search):
    if not ctx.author.voice: return await ctx.send("เข้าห้องเสียงก่อนครับพี่!")
    if not ctx.voice_client: await ctx.author.voice.channel.connect()
    if ctx.guild.id not in queues: queues[ctx.guild.id] = []
    queues[ctx.guild.id].append(search)
    if not ctx.voice_client.is_playing(): await play_next(ctx)
    else: await ctx.send("เพิ่มลงคิวแล้วครับ!")

bot.run(os.environ['DISCORD_TOKEN'])
