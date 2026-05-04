import asyncio
import os
import re
import uuid
import edge_tts
from config import settings


def _build_ssml(text: str, voice: str, style: str, rate: float) -> str:
    """Wrap plain text in SSML with expressive style and natural pacing."""
    text = text.strip()
    rate_str = f"{rate:.2f}"
    return (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"'
        f' xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="zh-CN">'
        f'<voice name="{voice}">'
        f'<mstts:express-as style="{style}" styledegree="1.5">'
        f'<prosody rate="{rate_str}" pitch="+0%">'
        f'{text}'
        f'</prosody>'
        f'</mstts:express-as>'
        f'</voice>'
        f'</speak>'
    )


def _add_sentence_breaks(text: str) -> str:
    """Insert short breaks between sentences for natural pacing."""
    text = re.sub(r"([。！？；?!;])\s*", r"\1<break time='300ms'/>", text)
    text = re.sub(r"([，,、])\s*", r"\1<break time='150ms'/>", text)
    text = re.sub(r"(……|\.\.\.)\s*", r"\1<break time='500ms'/>", text)
    return text


def _clean_role_prefix(text: str) -> str:
    """Strip any residual role markers from text before TTS."""
    text = re.sub(r"\*\*(甲|乙)\*\*[：:]", "", text)
    text = re.sub(r"^(甲|乙)[：:]\s*", "", text)
    text = re.sub(r"(?<=.)(甲|乙)[：:]", "", text)
    return text.strip()


async def _tts_ssml(ssml: str, output_path: str):
    communicate = edge_tts.Communicate(ssml)
    await communicate.save(output_path)


def _concat_mp3_files(input_paths: list[str], output_path: str) -> int:
    total_size = 0
    with open(output_path, "wb") as out:
        for path in input_paths:
            if os.path.exists(path):
                with open(path, "rb") as f:
                    data = f.read()
                    out.write(data)
                    total_size += len(data)
    return total_size


async def generate_audio_for_script(script: str, chapter_id: str) -> str:
    lines = script.strip().split("\n")
    tmp_paths = []

    os.makedirs(settings.AUDIO_DIR, exist_ok=True)

    sem = asyncio.Semaphore(3)

    async def process_line(i: int, line: str):
        line = line.strip()
        if not line:
            return

        if line.startswith("甲："):
            text = _clean_role_prefix(line[2:].strip())
            voice = settings.TTS_MALE_VOICE
            style = settings.TTS_MALE_STYLE
            rate = settings.TTS_MALE_RATE
        elif line.startswith("乙："):
            text = _clean_role_prefix(line[2:].strip())
            voice = settings.TTS_FEMALE_VOICE
            style = settings.TTS_FEMALE_STYLE
            rate = settings.TTS_FEMALE_RATE
        else:
            text = _clean_role_prefix(line)
            if not text:
                return
            voice = settings.TTS_MALE_VOICE
            style = settings.TTS_MALE_STYLE
            rate = settings.TTS_MALE_RATE

        if not text:
            return

        text = _add_sentence_breaks(text)
        ssml = _build_ssml(text, voice, style, rate)

        tmp_path = os.path.join(settings.AUDIO_DIR, f"{chapter_id}_{i}.mp3")
        async with sem:
            await _tts_ssml(ssml, tmp_path)
        tmp_paths.append(tmp_path)

    valid_lines = [(i, line) for i, line in enumerate(lines) if line.strip()]

    tasks = [process_line(i, line) for i, line in valid_lines]

    if not tasks:
        output_path = os.path.join(settings.AUDIO_DIR, f"{chapter_id}.mp3")
        with open(output_path, "wb") as f:
            f.write(b"")
        return output_path, 0.0

    await asyncio.gather(*tasks)

    output_path = os.path.join(settings.AUDIO_DIR, f"{chapter_id}.mp3")
    total_size = _concat_mp3_files(tmp_paths, output_path)

    duration_estimate = total_size / 8000.0
    if duration_estimate < 0.1:
        duration_estimate = 5.0

    for p in tmp_paths:
        if os.path.exists(p):
            os.remove(p)

    return output_path, duration_estimate


def merge_chapters(chapter_paths: list[str], book_id: str) -> str:
    os.makedirs(settings.AUDIO_DIR, exist_ok=True)
    output_path = os.path.join(settings.AUDIO_DIR, f"{book_id}_full.mp3")
    valid_paths = [p for p in chapter_paths if os.path.exists(p)]
    _concat_mp3_files(valid_paths, output_path)
    return output_path
