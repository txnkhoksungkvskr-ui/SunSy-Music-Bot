import discord, yt_dlp, asyncio, os
from discord.ext import commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
queues = {}

# ลิงก์รูปภาพที่ผมดึงมาให้ใหม่ (เป็น CDN ของ Discord โดยตรง จะไม่พังเหมือน Imgur)
IMAGE_URL = "https://cdn.discordapp.com/attachments/1463546041197658266/1476726406120472668/ChatGPT_Image_27_.._2569_06_14_35.png"

class MusicView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="➕ ADD", style=discord.ButtonStyle.primary, custom_id="add")
    async def add(self, i: discord.Interaction, b: discord.ui.Button):
        await i.response.send_modal(SongModal())

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
        await i.response.send_message("บอทออกจากห้อง", ephemeral=True)

class SongModal(discord.ui.Modal, title='เพิ่มเพลง'):
    song = discord.ui.TextInput(label='ชื่อเพลงหรือลิงก์ YouTube')
    async def on_submit(self, i: discord.Interaction):
        await i.response.defer()
        if i.guild.id not in queues: queues[i.guild.id] = []
        queues[i.guild.id].append(self.song.value)
        if not i.guild.voice_client:
            if i.user.voice: await i.user.voice.channel.connect()
            else: return await i.followup.send("พี่ต้องเข้าห้องเสียงก่อน!")
        if not i.guild.voice_client.is_playing(): await play_next(i)
        await i.followup.send(f"✅ เพิ่มคิว: {self.song.value}", ephemeral=True)

async def play_next(i):
    if not queues.get(i.guild.id) or not i.guild.voice_client: return
    song = queues[i.guild.id].pop(0)
    
    # แก้ปัญหา YouTube บล็อกบอท (IMG_0486.jpg)
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{song}", download=False)['entries'][0]
        
        # ใช้พาธ ffmpeg มาตรฐานของเซิร์ฟเวอร์
        source = discord.FFmpegPCMAudio(info['url'], executable="ffmpeg", 
                                        before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", 
                                        options="-vn")
        i.guild.voice_client.play(source, after=lambda e: bot.loop.create_task(play_next(i)))
        await i.channel.send(f"🎵 กำลังเล่น: **{info['title']}**")
    except Exception as e:
        await i.channel.send(f"❌ เกิดข้อผิดพลาด: {str(e)[:50]}")

@bot.command()
async def setup(ctx):
    embed = discord.Embed(title="🎵 SunSy MUSIC", description="กดปุ่มเพื่อสั่งการบอทได้เลยครับ", color=0xffa500)
    embed.set_image(url=IMAGE_URL)
    await ctx.send(embed=embed, view=MusicView())

@bot.event
async def on_ready():
    bot.add_view(MusicView())
    print('บอท SunSy พร้อมรันฟังก์ชันครบ!')

bot.run(os.environ['DISCORD_TOKEN'])
