"""Turn a chat message into text worth reading aloud.

Pure functions only, so every rule is covered by tests/test_normalize.py.
Input is discord's `message.clean_content`, where mentions are already
resolved to "@name", "#channel" and "@role".
"""

import re

MAX_LEN = 200
SKIP_PREFIX = "//"

_URL = re.compile(r"https?://\S+")
_CUSTOM_EMOJI = re.compile(r"<a?:\w+:\d+>")
_EMOJI = re.compile(
    "["
    "\U0001f000-\U0001faff"  # pictographs, emoticons, flags, skin tones
    "☀-➿"  # misc symbols, dingbats
    "⬀-⯿"  # arrows, stars
    "️‍⃣"  # variation selector, zero-width joiner, keycap
    "]+"
)
_MENTION_SIGIL = re.compile(r"(?<!\S)[@#](?=\S)")
_LAUGH = re.compile(r"(?<!\d)5{3,}(?!\d)")
_STRETCH = re.compile(r"([^\d\s])\1{2,}")
_SPACES = re.compile(r"\s+")


def clean(text: str) -> str:
    """Apply the text rules. Returns "" when nothing speakable is left."""
    text = _URL.sub(" ลิงก์ ", text)
    text = _CUSTOM_EMOJI.sub(" ", text)
    text = _EMOJI.sub(" ", text)
    text = _MENTION_SIGIL.sub("", text)
    text = _LAUGH.sub(" ฮ่า ๆ ", text)
    text = _STRETCH.sub(r"\1\1", text)
    text = _SPACES.sub(" ", text).strip()
    return text[:MAX_LEN].rstrip()


def normalize(text: str, *, speaker: str | None, has_attachments: bool) -> str | None:
    """Build the line to speak, or None to stay quiet.

    speaker: the author's display name when they differ from the previous
    message's author, None when the same person keeps talking.
    """
    if text.lstrip().startswith(SKIP_PREFIX):
        return None

    body = clean(text)
    if not body:
        if not has_attachments:
            return None
        body = "ส่งไฟล์"

    return f"{speaker} บอกว่า {body}" if speaker else body
