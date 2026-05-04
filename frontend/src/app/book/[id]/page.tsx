"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useParams } from "next/navigation";
import {
  getBook,
  getChapters,
  generatePodcast,
  getChapterAudioUrl,
  getChapterScript,
  Book,
  Chapter,
} from "@/lib/api";

export default function BookDetail() {
  const params = useParams();
  const bookId = params.id as string;

  const [book, setBook] = useState<Book | null>(null);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  const [currentChapter, setCurrentChapter] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [script, setScript] = useState("");
  const [showScript, setShowScript] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  const fetchData = useCallback(async () => {
    try {
      const [b, c] = await Promise.all([getBook(bookId), getChapters(bookId)]);
      setBook(b);
      setChapters(c);
    } catch {
      setError("无法连接后端服务");
    }
  }, [bookId]);

  useEffect(() => {
    fetchData();
    const timer = setInterval(() => {
      getBook(bookId).then(setBook).catch(() => {});
      getChapters(bookId).then(setChapters).catch(() => {});
    }, 3000);
    return () => clearInterval(timer);
  }, [fetchData, bookId]);

  const handleGenerate = async () => {
    setGenerating(true);
    setError("");
    try {
      await generatePodcast(bookId);
    } catch (e: any) {
      setError(e.message || "生成失败");
    }
    setGenerating(false);
  };

  const handlePlay = async (chapter: Chapter) => {
    if (!chapter.has_audio) return;
    const audio = audioRef.current;
    if (!audio) return;

    if (currentChapter === chapter.id) {
      if (audio.paused) {
        audio.play();
        setIsPlaying(true);
      } else {
        audio.pause();
        setIsPlaying(false);
      }
      return;
    }

    setCurrentChapter(chapter.id);
    audio.src = getChapterAudioUrl(bookId, chapter.id);
    audio.load();
    audio.play();
    setIsPlaying(true);
  };

  const handleViewScript = async (chapter: Chapter) => {
    if (chapter.id === currentChapter && showScript) {
      setShowScript(false);
      return;
    }
    setCurrentChapter(chapter.id);
    setShowScript(true);
    try {
      const data = await getChapterScript(bookId, chapter.id);
      setScript(data.script || "暂无脚本");
    } catch {
      setScript("加载脚本失败");
    }
  };

  if (!book) {
    return (
      <div className="py-12 text-center text-zinc-400">
        <div className="w-8 h-8 border-2 border-zinc-400 border-t-transparent rounded-full animate-spin mx-auto" />
      </div>
    );
  }

  const isProcessing = book.status === "generating" || book.status === "parsing";
  const hasCompleted = chapters.some((c) => c.has_audio);

  return (
    <div className="py-6 space-y-6">
      <div>
        <a href="/" className="text-sm text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300">
          &larr; 返回书架
        </a>
        <h1 className="text-xl font-bold text-zinc-900 dark:text-zinc-100 mt-2">
          {book.title}
        </h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">
          {book.total_chapters} 个章节 · {book.filename}
        </p>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      {!hasCompleted && book.status !== "generating" && (
        <button
          onClick={handleGenerate}
          disabled={generating || isProcessing}
          className="w-full py-3 rounded-xl bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
        >
          {generating ? "启动中..." : "生成播客"}
        </button>
      )}

      {isProcessing && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm text-zinc-500">
            <span>正在生成播客...</span>
            <span>
              {book.completed_chapters} / {book.total_chapters}
            </span>
          </div>
          <div className="w-full bg-zinc-200 dark:bg-zinc-800 rounded-full h-2">
            <div
              className="bg-amber-500 h-2 rounded-full transition-all duration-500"
              style={{
                width: `${(book.completed_chapters / Math.max(book.total_chapters, 1)) * 100}%`,
              }}
            />
          </div>
        </div>
      )}

      <div>
        <h2 className="text-sm font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wide mb-2">
          章节列表
        </h2>
        <div className="space-y-1">
          {chapters.map((chapter) => (
            <div
              key={chapter.id}
              className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
                currentChapter === chapter.id
                  ? "bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800"
                  : "border border-transparent hover:bg-zinc-50 dark:hover:bg-zinc-900"
              }`}
            >
              <button
                onClick={() => handlePlay(chapter)}
                disabled={!chapter.has_audio}
                className={`shrink-0 w-9 h-9 rounded-full flex items-center justify-center transition-colors ${
                  chapter.has_audio
                    ? "bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 hover:opacity-80"
                    : "bg-zinc-200 dark:bg-zinc-800 text-zinc-400"
                }`}
              >
                {currentChapter === chapter.id && isPlaying ? (
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <rect x="6" y="4" width="4" height="16" rx="1" />
                    <rect x="14" y="4" width="4" height="16" rx="1" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                    <polygon points="5,3 19,12 5,21" />
                  </svg>
                )}
              </button>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100 truncate">
                  {chapter.title}
                </p>
                <p className="text-xs text-zinc-400">
                  {chapter.status === "completed" && chapter.duration_seconds
                    ? `${Math.floor(chapter.duration_seconds / 60)}:${String(Math.floor(chapter.duration_seconds % 60)).padStart(2, "0")}`
                    : chapter.status === "processing"
                    ? "生成中..."
                    : chapter.status === "failed"
                    ? "失败"
                    : chapter.has_audio
                    ? "就绪"
                    : "待生成"}
                </p>
              </div>
              <button
                onClick={() => handleViewScript(chapter)}
                className="text-xs text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 px-2 py-1 rounded"
              >
                文稿
              </button>
            </div>
          ))}
        </div>
      </div>

      {showScript && script && (
        <div className="p-4 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-zinc-500">播客文稿</h3>
            <button
              onClick={() => setShowScript(false)}
              className="text-zinc-400 hover:text-zinc-600"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <pre className="text-sm text-zinc-700 dark:text-zinc-300 whitespace-pre-wrap font-sans leading-relaxed">
            {script}
          </pre>
        </div>
      )}

      <audio
        ref={audioRef}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onEnded={() => {
          setIsPlaying(false);
          if (!currentChapter) return;
          const idx = chapters.findIndex((c) => c.id === currentChapter);
          if (idx < chapters.length - 1) {
            const next = chapters[idx + 1];
            if (next.has_audio) {
              handlePlay(next);
            }
          }
        }}
        className="hidden"
      />

      {currentChapter && (
        <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-zinc-900 border-t border-zinc-200 dark:border-zinc-800 p-4">
          <div className="max-w-2xl mx-auto flex items-center gap-3">
            <button
              onClick={() => {
                const idx = chapters.findIndex((c) => c.id === currentChapter);
                if (idx > 0) handlePlay(chapters[idx - 1]);
              }}
              className="text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z" />
              </svg>
            </button>
            <button
              onClick={() => {
                const audio = audioRef.current;
                if (!audio) return;
                if (audio.paused) {
                  audio.play();
                  setIsPlaying(true);
                } else {
                  audio.pause();
                  setIsPlaying(false);
                }
              }}
              className="w-10 h-10 rounded-full bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 flex items-center justify-center"
            >
              {!isPlaying ? (
                <svg className="w-5 h-5 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                  <polygon points="5,3 19,12 5,21" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <rect x="6" y="4" width="4" height="16" rx="1" />
                  <rect x="14" y="4" width="4" height="16" rx="1" />
                </svg>
              )}
            </button>
            <button
              onClick={() => {
                const idx = chapters.findIndex((c) => c.id === currentChapter);
                if (idx < chapters.length - 1) handlePlay(chapters[idx + 1]);
              }}
              className="text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6 18l8.5-6L6 6v12zm10-12v12h2V6h-2z" />
              </svg>
            </button>
            <div className="flex-1 text-sm text-zinc-600 dark:text-zinc-400 truncate">
              {chapters.find((c) => c.id === currentChapter)?.title}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
