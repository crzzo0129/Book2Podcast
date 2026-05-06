# Book2Podcast - 书本变播客

将 PDF/TXT 书本转化为双人对谈播客，随时随地收听学习。

## 功能

- 上传 PDF 或 TXT 书本，自动识别章节
- AI 生成双人对话播客稿（讲解者+学习者）
- 语音合成播客音频，支持章节切换
- 移动端友好的 Web 界面，支持 PWA

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Next.js 16 + Tailwind CSS |
| 后端 | Python FastAPI |
| LLM | DeepSeek API |
| TTS | Microsoft Edge TTS (免费) |

## 快速开始

### 方式一：一键启动（推荐 Windows 用户）

1. 安装 [Python 3.10+](https://python.org) 和 [Node.js 18+](https://nodejs.org)
2. 双击项目根目录 `start.bat`
3. 首次运行会自动安装依赖、提示配置 API Key、启动服务并打开浏览器

### 方式二：Docker Compose（最简）

```bash
# 设置 API Key 环境变量
set DEEPSEEK_API_KEY=你的Key   # Windows
export DEEPSEEK_API_KEY=你的Key  # macOS/Linux

docker-compose up
```

浏览器打开 `http://localhost:3000`

### 方式三：手动启动

```bash
# 终端1 - 后端
cd backend
pip install -r requirements.txt
cp .env.example .env  # 编辑填入 DeepSeek API Key
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 终端2 - 前端
cd frontend
npm install
npm run dev
```

## 语音优化

- 男声(讲解者)：云扬(Yunyang) - 专业新闻播报风格
- 女声(学习者)：晓晓(Xiaoxiao) - 自然对话风格
- 使用 SSML 注入说话风格和句间停顿

## 项目结构

```
podcast/
├── backend/              # Python FastAPI 后端
│   ├── main.py           # API 入口
│   ├── parser.py         # PDF/TXT 解析 & 章节切分
│   ├── script_generator.py  # DeepSeek 对话脚本生成
│   ├── tts_generator.py  # Edge TTS 语音合成
│   ├── config.py         # 配置管理
│   ├── models.py         # 数据模型
│   ├── database.py       # 数据库连接
│   └── requirements.txt
├── frontend/             # Next.js 前端
│   └── src/
│       ├── app/
│       │   ├── page.tsx          # 首页 - 上传 & 书架
│       │   └── book/[id]/page.tsx # 书本详情 - 播放器
│       └── lib/
│           └── api.ts            # API 客户端
├── start_backend.bat     # Windows 后端启动脚本
└── start_frontend.bat    # Windows 前端启动脚本
```

## 自定义语音

编辑 `backend/config.py` 可更换 TTS 音色和说话风格：

```python
TTS_MALE_VOICE: str = "zh-CN-YunyangNeural"
TTS_MALE_STYLE: str = "newscast"
TTS_FEMALE_VOICE: str = "zh-CN-XiaoxiaoNeural"
TTS_FEMALE_STYLE: str = "chat"
```

可用风格：`chat`, `newscast`, `cheerful`, `sad`, `angry`, `excited` 等（取决于所选语音支持）。
