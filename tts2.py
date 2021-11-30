import discord
import os
import json
from json import JSONEncoder
from discord import FFmpegPCMAudio
from discord.utils import get
from gtts import gTTS
from discord.ext import commands
from discord_slash import SlashCommand
from discord_components import Button, Select, SelectOption, ComponentsBot

bot = commands.Bot(command_prefix='t.',help_command=None)
slash = SlashCommand(bot, sync_commands=True)

Token = input("Insert token here : ")

guild_id = {698129392257466380, 668845200973496360}
chat_id = []
chat_name = []
tts_author = []
author_name = []
setup_stat = 0
keep_text_stat = 0

'''
with open('settings.json') as f:
    data = json.load(f)

if f["token"] == "":
    Token = input("INSERT ME A TOKEN: ")
    if Token == "":
        print("WTF Token!?")
        exit(1)
    print("Next time, please set your token in settings.json")
else:
    Token = f["token"]
'''

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
    name = "How",
    description = "ดูวิธีการใช้งาน",
    guild_ids = guild_id 
)
async def how(ctx):
    em = discord.Embed(
        title="How To การใช้เทียนไข?", 
        description="สำหรับวิธีการตั้งค่าก่อนใช้งานมีอยู่สามขั้นตอนเท่านั้นนะคะ"
    )
    em.add_field(name="-", value="---")
    em.add_field(name="-", value="---")
    em.add_field(name="-", value="---")
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
        source = discord.FFmpegOpusAudio('startup.wav')
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
'''
@slash.slash(
    name='KeepText',
    description='Set channel to speech',
    guild_ids = guild_id
)
async def keeptext(ctx):
    
    global keep_text_stat
    
    if keep_text_stat == 0 and ctx.author.id == 479646298933297153:
        keep_text_stat = 1
        await ctx.reply("✅ : Keep Text was Enable")
        f = open("text.txt", "a", encoding="utf8")
        f.write("[✔ Start Keep]\n")
        f.close()

    elif keep_text_stat == 1 and ctx.author.id == 479646298933297153:
        keep_text_stat = 0
        await ctx.reply("🚫 : Keep Text was Disable")
        f = open("text.txt", "a", encoding="utf8")
        f.write("[❌ Ended Keep]\n \n")
        f.close()

    elif ctx.author.id != 479646298933297153:
        await ctx.reply("You don't have permission to use this commands.")
'''
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

@slash.slash(
    name = "Reply",
    description = "Speech Reply message", 
    guild_ids = guild_id
)
async def r(ctx):
    voice_client = get(bot.voice_clients, guild=ctx.guild)
    source = discord.FFmpegOpusAudio('speech.mp3')
    await ctx.reply("Message reply complete")
    voice_client.play(source)

@bot.event
async def on_message(message):

    global chat_id, setup_stat, keep_text_stat

    if message.author.id == 904757918455459860:
        print("\nBot had talking in : " + message.content)

    elif setup_stat == 1:
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
                print('Play... : ' + message.content)

        else :
            print('\nMessage in other chat : ' + message.channel.name + "\nIn content : " + message.content)
    
    elif setup_stat == 0:
        print("\nAuthor did not setup TTS Channel for use TTS feture")

    await bot.process_commands(message)
'''
@bot.event
async def on_message(text):

    global keep_text_stat

    if keep_text_stat == 1 and text.author.id != 904757918455459860:
        txt = "[ " + str(text.guild) + " : " + str(text.channel.name) + " ] " + str(text.author.name) + " : " + str(text.content) + "\n"
        f = open("text.txt", "a", encoding="utf8")
        f.write(txt)
        f.close()
    
    elif keep_text_stat == 0:
        print("KT == 0")
    else:
        print("")
'''
bot.run(Token)