import discord, yt_dlp, asyncio, os
from discord.ext import commands

# --- ลบ Flask และ Thread ออกเพราะพี่ไม่ได้ใส่มาในโค้ดล่าสุดครับ ---
# (ถ้าพี่อยากให้บอทออน 24 ชม. จริงๆ ต้องใส่ระบบ Keep Alive กลับมานะครับ)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
queues = {}

# --- แก้จุดตาย: ใส่ User-Agent หลบการบล็อกของ YouTube ---
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
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
            await interaction.response.send_message("หยุดเพลงชั่วคราวครับ!", ephemeral=True)

    @discord.ui.button(label="RESUME", style=discord.ButtonStyle.secondary, emoji="▶️", custom_id="btn_resume")
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_paused():
            interaction.guild.voice_client.resume()
            await interaction.response.send_message("เล่นต่อแล้วครับ!", ephemeral=True)

    @discord.ui.button(label="SKIP", style=discord.ButtonStyle.secondary, emoji="⏭️", custom_id="btn_skip")
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.voice_client:
            interaction.guild.voice_client.stop()
            await interaction.response.send_message("ข้ามเพลงแล้วครับ!", ephemeral=True)

    @discord.ui.button(label="STOP", style=discord.ButtonStyle.danger, emoji="⏹️", custom_id="btn_stop")
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            queues[interaction.guild.id] = []
            await interaction.response.send_message("หยุดและออกจากห้องแล้วครับ!", ephemeral=True)

class SongModal(discord.ui.Modal, title='เพิ่มเพลง'):
    song = discord.ui.TextInput(label='พิมพ์ชื่อเพลงหรือลิงก์ YouTube')
    async def on_submit(self, interaction: discord.Interaction):
        # --- ใช้ followup เพื่อให้ส่งข้อความทีหลังได้ ---
        await interaction.response.defer(ephemeral=True)
        if interaction.guild.id not in queues: queues[interaction.guild.id] = []
        queues[interaction.guild.id].append(self.song.value)
        if not interaction.guild.voice_client or not interaction.guild.voice_client.is_playing():
            if interaction.user.voice:
                await interaction.user.voice.channel.connect()
                await play_next(interaction)

async def play_next(interaction):
    if not queues.get(interaction.guild.id): return
    song_query = queues[interaction.guild.id].pop(0)
    
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{song_query}", download=False)['entries'][0]
        except Exception as e:
            return await interaction.followup.send(f"หาเพลงไม่เจอครับ: {e}")

    # --- แก้จุดตาย: ใช้ ffmpeg เฉยๆ (ไม่มี .exe) ---
    player = discord.FFmpegPCMAudio(info['url'], executable="ffmpeg", 
                                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", 
                                    options="-vn")
    
    # --- แก้การวนลูป: ใช้ bot.loop เพื่อให้ทำงานเสถียรบน Render ---
    interaction.guild.voice_client.play(player, after=lambda e: bot.loop.create_task(play_next(interaction)))
    
    # --- ใช้ followup.send เพื่อส่งข้อความหลังจาก defer ---
    await interaction.followup.send(f"กำลังเล่น: {info['title']}")

@bot.command()
async def setup(ctx):
    embed = discord.Embed(title="🎵 SunSy MUSIC", description="กดปุ่มสั่งการบอทได้เลย", color=discord.Color.red())
    # --- นี่คือรูปภาพ Embed ที่สวยที่สุดของพี่ครับ ---
    embed.set_image(url="https://cdn.discordapp.com/attachments/1463546041197658266/1476726406120472668/ChatGPT_Image_27_.._2569_06_14_35.png")
    await ctx.send(embed=embed, view=MusicView())

@bot.event
async def on_ready():
    # --- บังคับโหลด View เพื่อให้ปุ่มกดติดตลอดเวลา ---
    bot.add_view(MusicView())
    print('บอทพร้อมทำงานแล้วครับ!')

bot.run(os.environ['DISCORD_TOKEN']) # ใช้ Environment Variable เพื่อความปลอดภัย
