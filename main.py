import discord, yt_dlp, os
from discord.ext import commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
queues = {}

IMAGE_URL = "https://cdn.discordapp.com/attachments/1463546041197658266/1476726406120472668/ChatGPT_Image_27_.._2569_06_14_35.png"

class MusicView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="➕ ADD", style=discord.ButtonStyle.primary)
    async def add(self, i: discord.Interaction, b: discord.ui.Button):
        await i.response.send_modal(SongModal())

    @discord.ui.button(label="⏸️ PAUSE", style=discord.ButtonStyle.secondary)
    async def pause(self, i: discord.Interaction, b: discord.ui.Button):
        if i.guild.voice_client:
            i.guild.voice_client.pause()
        await i.response.send_message("⏸️ พักเพลงแล้ว", ephemeral=True)

    @discord.ui.button(label="▶️ RESUME", style=discord.ButtonStyle.secondary)
    async def resume(self, i: discord.Interaction, b: discord.ui.Button):
        if i.guild.voice_client:
            i.guild.voice_client.resume()
        await i.response.send_message("▶️ เล่นต่อแล้ว", ephemeral=True)

    @discord.ui.button(label="⏭️ SKIP", style=discord.ButtonStyle.secondary)
    async def skip(self, i: discord.Interaction, b: discord.ui.Button):
        if i.guild.voice_client:
            i.guild.voice_client.stop()
        await i.response.send_message("⏭️ ข้ามเพลง", ephemeral=True)

    @discord.ui.button(label="⏹️ STOP", style=discord.ButtonStyle.danger)
    async def stop(self, i: discord.Interaction, b: discord.ui.Button):
        if i.guild.voice_client:
            await i.guild.voice_client.disconnect()
        await i.response.send_message("⏹️ บอทออกแล้ว", ephemeral=True)


class SongModal(discord.ui.Modal, title="เพิ่มเพลง"):
    song = discord.ui.TextInput(label="ชื่อเพลง / ลิงก์ YouTube")

    async def on_submit(self, i: discord.Interaction):
        await i.response.defer(ephemeral=True)

        queues.setdefault(i.guild.id, []).append(self.song.value)

        if not i.guild.voice_client:
            if not i.user.voice:
                return await i.followup.send("❌ เข้าห้องเสียงก่อน")
            await i.user.voice.channel.connect()

        if not i.guild.voice_client.is_playing():
            await play_next(i)

        await i.followup.send(f"✅ เพิ่มคิว: {self.song.value}")


async def play_next(i):
    vc = i.guild.voice_client
    if not vc or not queues.get(i.guild.id):
        return

    song = queues[i.guild.id].pop(0)

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "user_agent": "Mozilla/5.0"
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{song}", download=False)["entries"][0]

        print("Playing:", info["title"])

        source = await discord.FFmpegOpusAudio.from_probe(
            info["url"],
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
        )

        vc.play(source, after=lambda e: bot.loop.create_task(play_next(i)))
        await i.channel.send(f"🎵 กำลังเล่น: **{info['title']}**")

    except Exception as e:
        print("ERROR:", e)
        await i.channel.send("❌ เล่นเพลงไม่ได้")


@bot.command()
async def setup(ctx):
    embed = discord.Embed(
        title="🎵 SunSy MUSIC",
        description="บอทเพลง Render (เสียงออกแน่นอน)",
        color=0xffa500
    )
    embed.set_image(url=IMAGE_URL)
    await ctx.send(embed=embed, view=MusicView())


@bot.event
async def on_ready():
    bot.add_view(MusicView())
    print("✅ Bot Ready")


bot.run(os.environ["DISCORD_TOKEN"])
