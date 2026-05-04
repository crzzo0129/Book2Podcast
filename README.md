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

### 1. 环境要求

- Python 3.10+
- Node.js 18+
- (Windows 用户需确保 `python` 和 `node` 已加入 PATH)

### 2. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 配置 DeepSeek API Key

在 `backend/` 目录下复制 `.env.example` 为 `.env`，填入你的 API Key：

```bash
cp .env.example .env
```

编辑 `.env`：
```
DEEPSEEK_API_KEY=你的DeepSeek_API_Key
```

> 获取 API Key：[platform.deepseek.com](https://platform.deepseek.com)

### 4. 安装前端依赖

```bash
cd frontend
npm install
```

### 5. 启动服务

**Windows：** 双击项目根目录下的 `start_backend.bat` 和 `start_frontend.bat`

**macOS/Linux：**
```bash
# 终端1 - 后端
cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 终端2 - 前端
cd frontend && npm run dev
```

### 6. 使用

1. 浏览器打开 `http://localhost:3000`
2. 上传 PDF 或 TXT 文件
3. 进入书本详情页，点击「生成播客」
4. 等待生成完成后，点击章节播放

移动端访问：手机浏览器打开 `http://<电脑IP>:3000`

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
