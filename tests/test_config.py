from pathlib import Path

import pytest

from candle.config import ConfigError, load_settings


def test_defaults_with_only_token():
    s = load_settings({"DISCORD_TOKEN": "abc"})
    assert s.discord_token == "abc"
    assert s.azure_speech_key is None
    assert s.azure_region == "southeastasia"
    assert s.dev_guild_id is None
    assert s.db_path == Path("data/candle.db")
    assert s.default_voice == "th-TH-PremwadeeNeural"


def test_blank_values_count_as_unset():
    s = load_settings({"DISCORD_TOKEN": "abc", "AZURE_SPEECH_KEY": "  ", "DEV_GUILD_ID": ""})
    assert s.azure_speech_key is None
    assert s.dev_guild_id is None


def test_missing_token_raises():
    with pytest.raises(ConfigError, match="DISCORD_TOKEN"):
        load_settings({})


def test_dev_guild_id_parsed():
    assert load_settings({"DISCORD_TOKEN": "x", "DEV_GUILD_ID": "123"}).dev_guild_id == 123


def test_bad_dev_guild_id_raises():
    with pytest.raises(ConfigError, match="DEV_GUILD_ID"):
        load_settings({"DISCORD_TOKEN": "x", "DEV_GUILD_ID": "abc"})
