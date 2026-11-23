import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from candle.normalize import normalize
from candle.tts.azure import THAI_VOICES
from candle.voice import VoiceSession

if TYPE_CHECKING:
    from candle.__main__ import Candle

log = logging.getLogger(__name__)

STARTUP_SOUND = Path(__file__).resolve().parent.parent / "assets" / "startup.wav"
EMPTY_TIMEOUT = 60  # seconds alone in a voice channel before leaving
VERSION = "0.2.0"
CANDLE_COLOUR = discord.Colour.from_rgb(255, 230, 189)


class TTSCommands(commands.Cog):
    def __init__(self, bot: "Candle") -> None:
        self.bot = bot
        self.sessions: dict[int, VoiceSession] = {}

    async def cog_unload(self) -> None:
        for session in self.sessions.values():
            await session.close()
        self.sessions.clear()

    # --- voice ---------------------------------------------------------

    @app_commands.command(name="join", description="พาเทียนไขเข้าห้องเสียงที่คุณอยู่")
    @app_commands.guild_only()
    async def join(self, itx: discord.Interaction) -> None:
        assert isinstance(itx.user, discord.Member) and itx.guild is not None
        if itx.user.voice is None or itx.user.voice.channel is None:
            await itx.response.send_message("เข้าห้องเสียงก่อนนะคะ แล้วค่อยเรียกเทียนไข", ephemeral=True)
            return
        channel = itx.user.voice.channel

        session = self.sessions.get(itx.guild.id)
        if session is not None and session.vc.is_connected():
            if session.vc.channel == channel:
                await itx.response.send_message("เทียนไขอยู่ในห้องนี้แล้วค่ะ", ephemeral=True)
            else:
                await session.vc.move_to(channel)
                await itx.response.send_message(f"ย้ายมาห้อง {channel.mention} แล้วค่ะ")
            return
        if session is not None:  # stale: connection dropped without an event
            await self._end(itx.guild.id)
        if itx.guild.voice_client is not None:  # connected but untracked
            await itx.guild.voice_client.disconnect(force=True)

        await itx.response.defer()
        try:
            vc = await channel.connect(self_deaf=True)
        except discord.ClientException:
            await itx.followup.send("เทียนไขกำลังเข้าห้องอยู่ค่ะ รอแป๊บนึงนะคะ", ephemeral=True)
            return
        except (TimeoutError, discord.Forbidden) as e:
            log.warning("guild=%s voice connect failed: %r", itx.guild.id, e)
            await itx.followup.send(
                "เข้าห้องไม่ได้ค่ะ ลองเช็กว่าเทียนไขมีสิทธิ์ Connect กับ Speak ในห้องนี้นะคะ", ephemeral=True
            )
            return
        session = VoiceSession(vc, self.bot.router)
        self.sessions[itx.guild.id] = session
        session.sound(STARTUP_SOUND)

        tts_channel = self.bot.store.get(itx.guild.id).tts_channel_id
        if tts_channel:
            note = f"จะอ่านข้อความในห้อง <#{tts_channel}> ให้ฟังนะคะ"
        else:
            note = "ยังไม่ได้ตั้งห้องแชทให้อ่านเลย ให้แอดมินใช้ `/setup` ก่อนนะคะ"
        await itx.followup.send(f"มาแล้วค่ะ~ อยู่ห้อง {channel.mention}\n{note}")

    @app_commands.command(name="leave", description="ให้เทียนไขออกจากห้องเสียง")
    @app_commands.guild_only()
    async def leave(self, itx: discord.Interaction) -> None:
        assert itx.guild is not None
        if not await self._end(itx.guild.id):
            await itx.response.send_message("เทียนไขไม่ได้อยู่ในห้องเสียงค่ะ", ephemeral=True)
            return
        await itx.response.send_message("บ๊ายบายค่ะ แล้วเจอกันใหม่น้า")

    @app_commands.command(name="skip", description="ข้ามข้อความที่กำลังอ่านอยู่")
    @app_commands.guild_only()
    async def skip(self, itx: discord.Interaction) -> None:
        assert itx.guild is not None
        session = self.sessions.get(itx.guild.id)
        if session is not None and session.skip():
            await itx.response.send_message("ข้ามแล้วค่ะ", ephemeral=True)
        else:
            await itx.response.send_message("ตอนนี้ไม่ได้อ่านอะไรอยู่ค่ะ", ephemeral=True)

    # --- settings ------------------------------------------------------

    @app_commands.command(name="setup", description="เลือกห้องแชทที่ให้เทียนไขอ่าน (ไม่ใส่ห้อง = ดูค่าที่ตั้งไว้)")
    @app_commands.describe(channel="ห้องแชทที่จะให้อ่านออกเสียง")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    async def setup(self, itx: discord.Interaction, channel: discord.TextChannel | None = None) -> None:
        assert itx.guild is not None
        store = self.bot.store
        if channel is None:
            s = store.get(itx.guild.id)
            where = f"<#{s.tts_channel_id}>" if s.tts_channel_id else "ยังไม่ได้ตั้ง"
            voice = THAI_VOICES.get(s.voice or self.bot.settings.default_voice, s.voice)
            await itx.response.send_message(f"ห้องที่อ่าน: {where}\nเสียง: {voice}", ephemeral=True)
            return
        await store.set_channel(itx.guild.id, channel.id)
        await itx.response.send_message(f"ตั้งค่าแล้วค่ะ เทียนไขจะอ่านข้อความในห้อง {channel.mention}")

    @app_commands.command(name="voice", description="เลือกเสียงของเทียนไขในเซิร์ฟเวอร์นี้")
    @app_commands.describe(voice="เสียงที่ต้องการ")
    @app_commands.choices(voice=[app_commands.Choice(name=label, value=vid) for vid, label in THAI_VOICES.items()])
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    async def voice(self, itx: discord.Interaction, voice: app_commands.Choice[str]) -> None:
        assert itx.guild is not None
        await self.bot.store.set_voice(itx.guild.id, voice.value)
        note = "" if self.bot.settings.azure_speech_key else "\n(ตอนนี้ยังไม่ได้ตั้ง Azure เลยใช้เสียง gTTS ไปก่อนนะคะ)"
        await itx.response.send_message(f"เปลี่ยนเป็นเสียง {voice.name} แล้วค่ะ{note}")

    @app_commands.command(name="help", description="สิ่งที่เทียนไขทำได้ค่ะ")
    async def help(self, itx: discord.Interaction) -> None:
        em = discord.Embed(
            title="เทียนไขมาแย้ววว 🕯️",
            description="น้องเป็นบอทที่อ่านข้อความในแชทเป็นเสียงให้พี่ ๆ ในห้องพูดคุยฟังค่ะ",
            colour=CANDLE_COLOUR,
        )
        em.add_field(
            name="เริ่มใช้งาน",
            value=(
                "1. แอดมินใช้ `/setup` เลือกห้องแชทที่จะให้อ่าน\n"
                "2. เข้าห้องเสียงแล้วพิมพ์ `/join`\n"
                "3. พิมพ์ในห้องแชทนั้น เทียนไขจะอ่านให้ฟังค่ะ"
            ),
            inline=False,
        )
        em.add_field(
            name="คำสั่ง",
            value=(
                "`/join` เข้าห้องเสียง · `/leave` ออกจากห้อง · `/skip` ข้ามข้อความ\n"
                "`/setup` ตั้งห้องแชท · `/voice` เลือกเสียง (สำหรับแอดมิน)"
            ),
            inline=False,
        )
        em.add_field(name="เคล็ดลับ", value="พิมพ์ `//` นำหน้าข้อความ ถ้าไม่อยากให้เทียนไขอ่าน", inline=False)
        em.set_footer(text=f"{VERSION} | Text to speech Bot for everyone!")
        await itx.response.send_message(embed=em)

    # --- events --------------------------------------------------------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.guild is None:
            return
        session = self.sessions.get(message.guild.id)
        if session is None or not session.vc.is_connected():
            return
        settings = self.bot.store.get(message.guild.id)
        if message.channel.id != settings.tts_channel_id:
            return

        same_speaker = session.last_author_id == message.author.id
        text = normalize(
            message.clean_content,
            speaker=None if same_speaker else message.author.display_name,
            has_attachments=bool(message.attachments),
        )
        if text is None:
            return
        session.last_author_id = message.author.id
        session.say(text, settings.voice or self.bot.settings.default_voice)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ) -> None:
        session = self.sessions.get(member.guild.id)
        if session is None:
            return
        if self.bot.user is not None and member.id == self.bot.user.id and after.channel is None:
            await self._end(member.guild.id)  # kicked or disconnected
            return
        self._watch_empty(member.guild.id, session)

    def _watch_empty(self, guild_id: int, session: VoiceSession) -> None:
        channel = session.vc.channel
        alone = channel is not None and not any(not m.bot for m in channel.members)
        if alone and session.leave_task is None:
            session.leave_task = asyncio.create_task(self._leave_when_empty(guild_id))
        elif not alone and session.leave_task is not None:
            session.leave_task.cancel()
            session.leave_task = None

    async def _leave_when_empty(self, guild_id: int) -> None:
        await asyncio.sleep(EMPTY_TIMEOUT)
        session = self.sessions.get(guild_id)
        if session is not None:
            session.leave_task = None  # don't let close() cancel this task
            log.info("guild=%s left empty voice channel", guild_id)
            await self._end(guild_id)

    async def _end(self, guild_id: int) -> bool:
        session = self.sessions.pop(guild_id, None)
        if session is None:
            return False
        await session.close()
        return True


async def setup(bot: "Candle") -> None:
    await bot.add_cog(TTSCommands(bot))
