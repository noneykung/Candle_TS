import discord
from discord import FFmpegPCMAudio
from discord.utils import get
from gtts import gTTS
from discord.ext import commands
from discord_slash import SlashCommand

bot = commands.Bot(command_prefix='t.',help_command=None)
slash = SlashCommand(bot, sync_commands=True)

Token = ('OTA0NzU3OTE4NDU1NDU5ODYw.YYALeQ.p8Y0vQSCtj0cfN_JuUWb-ILONJU')

guild_id = {698129392257466380, 668845200973496360}
chat_id = []
chat_name = []
tts_author = []
author_name = []
setup_stat = 0

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
    em = discord.Embed(title="เทียนไขมาแย้ววว", description="น้องเป็นบอทที่จะแปลงข้อความเป็นเสียงให้กับพี่ ๆ ในดิสนะคะ")
    em.add_field(name="/join", value="พาน้องเข้าห้องนะคะ")
    em.add_field(name="/disconnect", value="นำน้องออกจากห้องค่ะ")
    em.add_field(name="/setup", value="ตั้งค่าห้องสำหรับการใช้ฟีเจอร์ Text to speech ค่ะ")
    await ctx.send(content=None, embed=em)

@slash.slash(
    name = 'join',
    description = 'Let me in your voice channel',
    guild_ids = guild_id
)
async def join(ctx):
    channel = ctx.author.voice.channel
    voice_client = get(bot.voice_clients, guild=ctx.guild)

    if voice_client == None:
        channel = ctx.author.voice.channel
        voice = await channel.connect()
        source = discord.FFmpegOpusAudio('startup.mp3')
        await ctx.reply('Joined!')
        print('\nJoined!')
        voice.play(source)

    else :
        await ctx.reply('Check you are in the voice channel')
        print('No member in the voice channel')

@slash.slash(
    name = 'Disconnect',
    description = "Let me out from voice channel",
    guild_ids = guild_id
)
async def disconnect(ctx):

    voice_client = get(bot.voice_clients, guild=ctx.guild)

    if (ctx.voice_client):
        source = discord.FFmpegOpusAudio('shutdown.mp3')
        await ctx.reply('Bye and See ya!')
        print('\nLeave!')
        voice_client.play(source)
        await ctx.guild.voice_client.disconnect()

    else:
        await ctx.send('I did not in the voice channel!')
        print('I an not in the voice channel')

@slash.slash(
    name='Setup',
    description='Set channel to speech',
    guild_ids = guild_id
)
async def setup(ctx):
    global chat_id, chat_name, setup_stat
    chat_id = str(ctx.channel.id)
    chat_name = str(ctx.channel.name)
    setup_stat = 1
    await ctx.reply("TTS Has setup in chat : " + chat_name + " (" + chat_id + ")")
    print("\nTTS Has setup in chat : " + chat_name + " (" + chat_id + ")")

@slash.slash(
    name = "Check",
    description = "Check TTS Channel Id", 
    guild_ids = guild_id
)
async def check(ctx):
    global chat_id, chat_name, tts_author, author_name, setup_stat

    if setup_stat == 0:
        await ctx.reply("TTS did not setup already")
        print("\nTTS did not setup already")

    elif setup_stat == 1:
        await ctx.reply("TTS already setup in : " + chat_name + " (" + chat_id + ")")
        await ctx.reply("TTS already setup in : " + author_name + " (" + tts_author + ")")
        print("\nCommand Check TTS setup in chat : " + chat_name + " (" + chat_id + ")\n" + "Setup by : " + author_name)

@bot.event
async def on_message(message):

    global chat_id, setup_stat

    if setup_stat == 1:
        if message.channel.id == int(chat_id) and message.author.id != 904757918455459860:
            tts = gTTS(str(message.content) ,lang='th')
            tts.save('speech.mp3')
            print('\n' + 'User Name >> ' + str(message.author.name) + '\nSpeech Has Update in content : ' + str(message.content))
            voice_client = get(bot.voice_clients, guild=message.guild)

            if voice_client == None:
                print('Bot dose not join voice channel')

            elif voice_client != None : 
                source = discord.FFmpegOpusAudio('speech.mp3')
                voice_client.play(source)
                print('Play... ' + message.content)

        elif message.author.id == 904757918455459860:
            print("\nBot had talking in : " + message.content)

        else :
            print('\nMessage in other chat : ' + message.channel.name + "\nIn content : " + message.content)
    
    elif setup_stat == 0:
        print("\nAuthor did not setup TTS Channel for use TTS feture")

    await bot.process_commands(message)

bot.run(Token)