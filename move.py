import discord
from discord_slash import SlashCommand
from discord.ext import commands

bot = commands.Bot(command_prefix='t.',help_command=None)
slash = SlashCommand(bot, sync_commands=True)
guild_id = {698129392257466380, 668845200973496360}

Token = "OTA0NzU3OTE4NDU1NDU5ODYw.YYALeQ.ca60uQkJzJ6bpC0cIyosX5G_X80"

@bot.event
async def on_ready():
    print('\nLogged in as ' + bot.user.name +" (" + str(bot.user.id) + ")\n------")
    #await setBotName(bot,'Candle_TS')
    await bot.change_presence(activity=discord.Game(name='อยู่ห่างไกลมันเหงาใจ อยากชื่นใจต้องอยู่ใกล้กัน~'))

@slash.slash(
    name = "Help",
    description = "สิ่งที่เทียนไขทำได้ค่ะ",
    guild_ids = guild_id 
)
async def help(ctx):
    em = discord.Embed(
        title = "เทียนไขมาแย้ววว", 
        description = "น้องเป็นบอทที่จะแปลงข้อความเป็นเสียงให้กับพี่ ๆ ในดิสนะคะ",
        colour = discord.Colour.from_rgb(255,230,189)
    )
    em.set_author(name = "เทียนไขเจ้าค่ะ" , icon_url = "https://media.discordapp.net/attachments/902103837651906593/914784729981677598/Candle_TS_Logo.png?")
    em.add_field(name="/join", value="พาน้องเข้าห้องนะคะ")
    em.add_field(name="/disconnect", value="นำน้องออกจากห้องค่ะ")
    em.add_field(name="/setup", value="ตั้งค่าห้องสำหรับการใช้ฟีเจอร์ Text to speech ค่ะ")
    em.set_image(url="https://media.discordapp.net/attachments/902103837651906593/914784730182991872/Candle_TS_Banner.png")

    await ctx.send(
        embed = em
    )

@slash.slash(
    name='Move Member',
    description='move member to another voice channel',
    guild_ids = guild_id
)
async def move(
    ctx,
    channel: discord.VoiceChannel
):
    print('Test command move')
    await ctx.send('Test command move')

bot.run(Token)