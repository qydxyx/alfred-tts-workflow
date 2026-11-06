from alfred_tts.query import has_cjk, parse_query, slug


def test_parse_plain_text() -> None:
    parsed = parse_query("你好，今天天气真好")
    assert parsed.provider is None
    assert parsed.text == "你好，今天天气真好"
    assert parsed.is_stop is False


def test_parse_at_provider() -> None:
    parsed = parse_query("@kokoro 测试离线语音")
    assert parsed.provider == "kokoro"
    assert parsed.text == "测试离线语音"


def test_parse_voice_id_after_provider() -> None:
    parsed = parse_query("@elevenlabs voice:JBFqnCBsd6RMkjVDRZzb 你好")
    assert parsed.provider == "elevenlabs"
    assert parsed.voice == "JBFqnCBsd6RMkjVDRZzb"
    assert parsed.text == "你好"


def test_parse_hash_voice_id() -> None:
    parsed = parse_query("#pNInz6obpgDQGcFmaJgB hello")
    assert parsed.provider is None
    assert parsed.voice == "pNInz6obpgDQGcFmaJgB"
    assert parsed.text == "hello"


def test_parse_stop() -> None:
    assert parse_query("stop").is_stop is True
    assert parse_query("STOP").is_stop is True


def test_parse_empty() -> None:
    parsed = parse_query("   ")
    assert parsed.text == ""
    assert parsed.provider is None


def test_has_cjk_and_slug() -> None:
    assert has_cjk("hello 世界")
    assert not has_cjk("hello world")
    assert slug("你好 world?") == "你好_world"
