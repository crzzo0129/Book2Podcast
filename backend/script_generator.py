import re
from openai import AsyncOpenAI
from config import settings

client = AsyncOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
)

EXTRACT_PROMPT = """你是一位专业的读书笔记提取专家。请从以下书本章节内容中提取核心知识点，用于后续生成播客对谈稿。

## 提取要求
1. 找出 3-5 个核心概念或观点
2. 每个概念附带一个简短的解释（1-2句话）
3. 标注其中最有意思、最反常识的点
4. 如果有具体案例或数据，一并提取
5. 用简洁的列表形式输出，不要展开论述

## 输出格式
直接输出要点列表，每行一条：
- 概念1：简要解释
- 概念2：简要解释
...

不要输出任何标题、说明或额外文字。"""

SYSTEM_PROMPT = """你是一位专业的播客脚本作家。你的任务是将书本内容转化为一场有趣、引人入胜的双人对谈播客。

# ⚠️ 最重要的规则：输出格式（违反此规则将被拒绝）

你必须逐行输出，每行一条对话。每行必须以 "甲：" 或 "乙：" 开头。

正确示例：
甲：今天我们来聊聊习惯的力量这个话题。
乙：习惯这个话题太有意思了，每个人都有自己的一套习惯啊。
甲：没错，研究发现习惯的形成需要三个关键要素。
乙：哪三个？快给我讲讲。

错误示例（禁止）：
甲：今天我们来聊聊习惯的力量这个话题。乙：习惯这个话题太有意思了。甲：没错，研究发现习惯的形成需要三个关键要素。

## 角色设定
- 甲（讲解者）：知识渊博、表达清晰，负责解读书中的核心概念和观点。语气温和而专业。
- 乙（学习者）：好奇心强、善于提问，代表听众视角，不断追问、要求举例、总结要点。语气自然活泼。

## 写作要求
1. 请围绕提供的【内容要点】展开对话，不要复述或朗读原文
2. 用生活中的例子、比喻来解释抽象概念
3. 乙要适时打断、提问、共鸣，让对话有互动感
4. 可以加入适度的感叹和口语化表达（"原来如此！""这个有意思""等等，让我想想..."）
5. 对话长度控制在 800-1800 字之间，适合 5-10 分钟音频
6. 语言风格参考播客《纵横四海》《文化有限》

## 输出规则
1. 每行一条对话，以"甲："或"乙："开头
2. 甲和乙的对话交替进行
3. 每行之间用换行分隔
4. 不要添加任何其他文字、标题、markdown标记
5. 不要输出连续段落，必须是逐行对话"""


async def extract_key_points(chapter_title: str, chapter_content: str) -> str:
    prompt = f"""请从以下章节内容中提取核心要点。

章节标题：{chapter_title}

章节内容：
{chapter_content[:6000]}
"""

    response = await client.chat.completions.create(
        model=settings.DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": EXTRACT_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=1024,
    )

    points = response.choices[0].message.content.strip()
    return points


async def generate_script(chapter_title: str, chapter_content: str) -> str:
    if len(chapter_content.strip()) > 200:
        key_points = await extract_key_points(chapter_title, chapter_content)
    else:
        key_points = chapter_content

    user_prompt = f"""请根据以下内容要点，生成一段双人对谈播客稿。

⚠️ 注意：每行必须以"甲："或"乙："开头，每行一条对话，用换行分隔。

章节标题：{chapter_title}

内容要点：
{key_points[:4000]}
"""

    response = await client.chat.completions.create(
        model=settings.DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.8,
        max_tokens=4096,
    )

    raw = response.choices[0].message.content.strip()
    script = normalize_script(raw, chapter_title)
    return script
