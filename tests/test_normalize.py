import pytest

from candle.normalize import MAX_LEN, clean, normalize


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("ดูนี่ https://youtu.be/abc?t=1 สิ", "ดูนี่ ลิงก์ สิ"),
        ("สวัสดี <:candle:123456789>", "สวัสดี"),
        ("ไปกัน <a:dance:987654321> เลย", "ไปกัน เลย"),
        ("น่ารัก 😍👍🏻", "น่ารัก"),
        ("ธงไทย 🇹🇭 ❤️", "ธงไทย"),
        ("ครอบครัว 👨‍👩‍👧 จ้า", "ครอบครัว จ้า"),
        ("@นนท์ มาห้อง #general หน่อย", "นนท์ มาห้อง general หน่อย"),
        ("ส่งเมลไปที่ a@b.com", "ส่งเมลไปที่ a@b.com"),
        ("55555", "ฮ่า ๆ"),
        ("ตลกมาก 555+", "ตลกมาก ฮ่า ๆ +"),
        ("โทร 0815553333", "โทร 0815553333"),
        ("ราคา 1000 บาท", "ราคา 1000 บาท"),
        ("ค่าาาาาา", "ค่าา"),
        ("งงงงงง", "งง"),
        ("โอเคค", "โอเคค"),
        ("  เว้น    วรรค  ", "เว้น วรรค"),
        ("😂😂😂", ""),
    ],
)
def test_clean(raw, expected):
    assert clean(raw) == expected


def test_clean_truncates():
    assert len(clean("ก" * 50 + "ข" * 500)) <= MAX_LEN


def test_skip_prefix():
    assert normalize("// ไม่ต้องอ่าน", speaker="นนท์", has_attachments=False) is None
    assert normalize("  //เงียบ", speaker=None, has_attachments=False) is None


def test_new_speaker_gets_prefix():
    assert normalize("หวัดดี", speaker="นนท์", has_attachments=False) == "นนท์ บอกว่า หวัดดี"


def test_same_speaker_no_prefix():
    assert normalize("หวัดดี", speaker=None, has_attachments=False) == "หวัดดี"


def test_attachment_only():
    assert normalize("", speaker="นนท์", has_attachments=True) == "นนท์ บอกว่า ส่งไฟล์"


def test_attachment_with_text_reads_text():
    assert normalize("ดูรูปนี้", speaker=None, has_attachments=True) == "ดูรูปนี้"


def test_nothing_left_is_silent():
    assert normalize("😂😂", speaker="นนท์", has_attachments=False) is None
    assert normalize("", speaker=None, has_attachments=False) is None
