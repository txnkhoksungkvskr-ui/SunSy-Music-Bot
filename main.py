import discord, yt_dlp, asyncio, os
from discord.ext import commands

# 1. ตั้งค่าพื้นฐาน
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
queues = {}

# ลิงก์รูปภาพแบนเนอร์ที่เสถียร (ใช้ CDN ตรงของ Discord กันรูปหาย)
IMAGE_URL = "https://cdn.discordapp.com/attachments/1463546041197658266/1476726406120472668/ChatGPT_Image_27_.._2569_06_14_35.png"

# 2. ระบบปุ่มกด (ครบทุกฟังก์ชันตามที่พี่ต้องการ)
class MusicView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="➕ ADD", style=discord.ButtonStyle.primary, custom_id="add")
    async def add(self, i: discord.Interaction, b: discord.ui.Button):
        await i.response.send_modal(SongModal())

    @discord.ui.button(label="⏸️ PAUSE", style=discord.ButtonStyle.secondary, custom_id="pause")
    async def pause(self, i: discord.Interaction, b: discord.ui.Button):
        if i.guild.voice_client: i.guild.voice_client.pause()
        await i.response.send_message("⏸️ พักเพลงแป๊บนะครับ", ephemeral=True)

    @discord.ui.button(label="▶️ RESUME", style=discord.ButtonStyle.secondary, custom_id="resume")
    async def resume(self, i: discord.Interaction, b: discord.ui.Button):
        if i.guild.voice_client: i.guild.voice_client.resume()
        await i.response.send_message("▶️ เล่นเพลงต่อแล้วครับ", ephemeral=True)

    @discord.ui.button(label="⏭️ SKIP", style=discord.ButtonStyle.secondary, custom_id="skip")
    async def skip(self, i: discord.Interaction, b: discord.ui.Button):
        if i.guild.voice_client: i.guild.voice_client.stop()
        await i.response.send_message("⏭️ ข้ามเพลงให้แล้วครับ", ephemeral=True)

    @discord.ui.button(label="⏹️ STOP", style=discord.ButtonStyle.danger, custom_id="stop")
    async def stop(self, i: discord.Interaction, b: discord.ui.Button):
        if i.guild.voice_client: await i.guild.voice_client.disconnect()
        queues[i.guild.id] = []
        await i.response.send_message("⏹️ บอทออกจากห้องแล้วครับ", ephemeral=True)

# 3. หน้าต่างกรอกชื่อเพลง
class SongModal(discord.ui.Modal, title='เพิ่มเพลงลงคิว'):
    song = discord.ui.TextInput(label='พิมพ์ชื่อเพลง หรือ ลิงก์ YouTube')
    async def on_submit(self, i: discord.Interaction):
        await i.response.defer()
        if i.guild.id not in queues: queues[i.guild.id] = []
        queues[i.guild.id].append(self.song.value)
        
        if not i.guild.voice_client:
            if i.user.voice:
                await i.user.voice.channel.connect()
            else:
                return await i.followup.send("❌ พี่ต้องเข้าห้องเสียงก่อนนะครับ!", ephemeral=True)
        
        if not i.guild.voice_client.is_playing():
            await play_next(i)
        await i.followup.send(f"✅ เพิ่มเข้าคิว: {self.song.value}", ephemeral=True)

# 4. ระบบดึงเพลงและเล่นเพลง (แก้ปัญหา YouTube บล็อกบอท)
async def play_next(i):
    if not queues.get(i.guild.id) or not i.guild.voice_client: return
    song_query = queues[i.guild.id].pop(0)
    
    # ตั้งค่าหัวใจหลักเพื่อให้ YouTube ไม่บล็อก (User-Agent คือสิ่งสำคัญ)
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{song_query}", download=False)['entries'][0]
        
        # ตั้งค่า FFmpeg ให้ทนทานต่อ Server ต่างประเทศ
        ffmpeg_opts = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        
        source = discord.FFmpegPCMAudio(info['url'], **ffmpeg_opts)
        i.guild.voice_client.play(source, after=lambda e: bot.loop.create_task(play_next(i)))
        await i.channel.send(f"🎵 กำลังเล่น: **{info['title']}**")
    except Exception as e:
        await i.channel.send(f"⚠️ เกิดปัญหาในการดึงเพลง: {str(e)[:100]}")

# 5. คำสั่ง Setup หน้าตาบอท (จุดรวมความสวยงาม)
@bot.command()
async def setup(ctx):
    embed = discord.Embed(
        title="🎵 SunSy MUSIC", 
        description="กดปุ่มด้านล่างเพื่อสั่งการบอทได้เลยครับพี่!", 
        color=0xffa500
    )
    embed.set_image(url=IMAGE_URL)
    await ctx.send(embed=embed, view=MusicView())

@bot.event
async def on_ready():
    bot.add_view(MusicView()) # ทำให้ปุ่มทำงานได้ตลอดเวลาแม้บอทรีสตาร์ท
    print(f'Logged in as {bot.user} - ฟังก์ชันครบ รูปสวย พร้อมรัน!')

bot.run(os.environ['DISCORD_TOKEN'])
