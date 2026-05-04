import os
import uuid
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from config import settings
from database import init_db, get_db
from models import Book, Chapter, Task, BookStatus, ChapterStatus
from parser import parse_file
from script_generator import generate_script, validate_script
from tts_generator import generate_audio_for_script, merge_chapters


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.AUDIO_DIR, exist_ok=True)
    await init_db()
    yield


app = FastAPI(title="Book2Podcast", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static/audio", StaticFiles(directory=settings.AUDIO_DIR), name="audio")


@app.get("/api/health")
async def health_check():
    api_key = settings.DEEPSEEK_API_KEY
    return {
        "status": "ok",
        "deepseek_configured": bool(api_key and len(api_key) > 10),
    }


@app.post("/api/books/upload")
async def upload_book(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("pdf", "txt"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 和 TXT 格式")

    book_id = str(uuid.uuid4())
    save_name = f"{book_id}.{ext}"
    save_path = os.path.join(settings.UPLOAD_DIR, save_name)

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="文件为空")

    with open(save_path, "wb") as f:
        f.write(content)

    try:
        _, chapters = parse_file(save_path, ext)
        title = os.path.splitext(file.filename)[0]
    except Exception as e:
        os.remove(save_path)
        import traceback
        detail = f"文件解析失败: {str(e)}"
        print(f"[ERROR] Upload failed: {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=detail)

    book = Book(
        id=book_id,
        title=title,
        filename=file.filename,
        file_type=ext,
        file_path=save_path,
        status=BookStatus.PARSED.value,
        total_chapters=len(chapters),
        chapter_list=[{"index": c["index"], "title": c["title"]} for c in chapters],
    )
    db.add(book)

    for ch in chapters:
        chapter = Chapter(
            id=str(uuid.uuid4()),
            book_id=book_id,
            index=ch["index"],
            title=ch["title"],
            content_text=ch["content"],
            status=ChapterStatus.PENDING.value,
        )
        db.add(chapter)

    await db.commit()

    return {
        "id": book_id,
        "title": title,
        "total_chapters": len(chapters),
        "chapters": [{"index": c["index"], "title": c["title"]} for c in chapters],
    }


@app.get("/api/books")
async def list_books(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Book).order_by(Book.created_at.desc())
    )
    books = result.scalars().all()
    return [
        {
            "id": b.id,
            "title": b.title,
            "filename": b.filename,
            "file_type": b.file_type,
            "status": b.status,
            "total_chapters": b.total_chapters,
            "completed_chapters": b.completed_chapters,
            "chapter_list": b.chapter_list,
            "created_at": b.created_at.isoformat(),
        }
        for b in books
    ]


@app.get("/api/books/{book_id}")
async def get_book(book_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="书本不存在")

    return {
        "id": book.id,
        "title": book.title,
        "filename": book.filename,
        "file_type": book.file_type,
        "status": book.status,
        "total_chapters": book.total_chapters,
        "completed_chapters": book.completed_chapters,
        "chapter_list": book.chapter_list,
        "error_message": book.error_message,
        "created_at": book.created_at.isoformat(),
    }


@app.get("/api/books/{book_id}/chapters")
async def list_chapters(book_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Chapter)
        .where(Chapter.book_id == book_id)
        .order_by(Chapter.index)
    )
    chapters = result.scalars().all()
    return [
        {
            "id": c.id,
            "index": c.index,
            "title": c.title,
            "status": c.status,
            "duration_seconds": c.duration_seconds,
            "has_audio": c.audio_path is not None,
            "audio_url": f"/api/books/{book_id}/chapters/{c.id}/audio" if c.audio_path else None,
            "error_message": c.error_message,
        }
        for c in chapters
    ]


@app.post("/api/books/{book_id}/generate")
async def generate_podcast(
    book_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="书本不存在")

    if book.status in (BookStatus.GENERATING.value, BookStatus.PARSING.value):
        raise HTTPException(status_code=400, detail="正在处理中，请稍候")

    book.status = BookStatus.GENERATING.value
    book.completed_chapters = 0
    await db.commit()

    background_tasks.add_task(_process_book, book_id)

    return {"status": "started", "book_id": book_id}


async def _process_book(book_id: str):
    from database import async_session

    async with async_session() as db:
        try:
            result = await db.execute(select(Book).where(Book.id == book_id))
            book = result.scalar_one_or_none()
            if not book:
                return

            result = await db.execute(
                select(Chapter)
                .where(Chapter.book_id == book_id)
                .order_by(Chapter.index)
            )
            chapters = result.scalars().all()

            for ch in chapters:
                ch.status = ChapterStatus.PROCESSING.value
            await db.commit()

            audio_paths = []

            for ch in chapters:
                content = ch.content_text or ""
                if not content.strip():
                    ch.status = ChapterStatus.COMPLETED.value
                    ch.script = ""
                    book.completed_chapters += 1
                    await db.commit()
                    continue

                try:
                    script = await generate_script(ch.title, content)
                    if not validate_script(script):
                        script = f"甲：今天我们来聊聊《{ch.title}》。\n乙：好的，请开始吧。\n{script}"

                    ch.script = script
                    ch.status = ChapterStatus.PROCESSING.value
                    await db.commit()

                    audio_path, duration = await generate_audio_for_script(script, ch.id)
                    ch.audio_path = audio_path
                    ch.duration_seconds = duration
                    ch.status = ChapterStatus.COMPLETED.value
                    book.completed_chapters += 1
                    audio_paths.append(audio_path)

                except Exception as e:
                    ch.status = ChapterStatus.FAILED.value
                    ch.error_message = str(e)
                    book.completed_chapters += 1

                await db.commit()

            if audio_paths:
                try:
                    merge_chapters(audio_paths, book_id)
                except Exception:
                    pass

            book.status = BookStatus.COMPLETED.value
            await db.commit()

        except Exception as e:
            book = (await db.execute(select(Book).where(Book.id == book_id))).scalar_one_or_none()
            if book:
                book.status = BookStatus.FAILED.value
                book.error_message = str(e)
                await db.commit()


@app.get("/api/books/{book_id}/chapters/{chapter_id}/audio")
async def get_chapter_audio(book_id: str, chapter_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id, Chapter.book_id == book_id)
    )
    chapter = result.scalar_one_or_none()
    if not chapter or not chapter.audio_path:
        raise HTTPException(status_code=404, detail="音频不存在")

    if not os.path.exists(chapter.audio_path):
        raise HTTPException(status_code=404, detail="音频文件丢失")

    return FileResponse(
        chapter.audio_path,
        media_type="audio/mpeg",
        filename=f"chapter_{chapter.index}.mp3",
    )


@app.get("/api/books/{book_id}/chapters/{chapter_id}/script")
async def get_chapter_script(book_id: str, chapter_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id, Chapter.book_id == book_id)
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")

    return {"id": chapter.id, "script": chapter.script or ""}


@app.delete("/api/books/{book_id}")
async def delete_book(book_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="书本不存在")

    if os.path.exists(book.file_path):
        os.remove(book.file_path)

    chapter_result = await db.execute(select(Chapter).where(Chapter.book_id == book_id))
    for ch in chapter_result.scalars().all():
        if ch.audio_path and os.path.exists(ch.audio_path):
            os.remove(ch.audio_path)

    full_audio = os.path.join(settings.AUDIO_DIR, f"{book_id}_full.mp3")
    if os.path.exists(full_audio):
        os.remove(full_audio)

    await db.execute(delete(Chapter).where(Chapter.book_id == book_id))
    await db.execute(delete(Book).where(Book.id == book_id))
    await db.commit()

    return {"status": "deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
