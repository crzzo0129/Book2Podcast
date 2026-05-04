"use client";

import { useState, useEffect, useCallback } from "react";
import { listBooks, uploadBook, deleteBook, Book } from "@/lib/api";

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { text: string; color: string }> = {
    uploaded: { text: "已上传", color: "bg-zinc-200 text-zinc-700" },
    parsing: { text: "解析中", color: "bg-blue-100 text-blue-700" },
    parsed: { text: "已解析", color: "bg-emerald-100 text-emerald-700" },
    generating: { text: "生成中", color: "bg-amber-100 text-amber-700" },
    completed: { text: "已完成", color: "bg-emerald-100 text-emerald-700" },
    failed: { text: "失败", color: "bg-red-100 text-red-700" },
  };
  const info = map[status] || { text: status, color: "bg-zinc-100 text-zinc-600" };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${info.color}`}>
      {info.text}
    </span>
  );
}

export default function Home() {
  const [books, setBooks] = useState<Book[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(false);

  const fetchBooks = useCallback(async () => {
    try {
      const data = await listBooks();
      setBooks(data);
    } catch {
      setError("无法连接后端服务，请确认服务已启动");
    }
  }, []);

  useEffect(() => {
    fetchBooks();
    const timer = setInterval(fetchBooks, 5000);
    return () => clearInterval(timer);
  }, [fetchBooks]);

  const handleFile = async (file: File) => {
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (ext !== "pdf" && ext !== "txt") {
      setError("仅支持 PDF 和 TXT 文件");
      return;
    }
    setError("");
    setUploading(true);
    try {
      await uploadBook(file);
      await fetchBooks();
    } catch (e: any) {
      setError(e.message || "上传失败");
    }
    setUploading(false);
  };

  const handleDelete = async (bookId: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm("确定要删除这本书吗？")) return;
    try {
      await deleteBook(bookId);
      await fetchBooks();
    } catch (e: any) {
      setError(e.message || "删除失败");
    }
  };

  return (
    <div className="py-6 space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
          书本变播客
        </h1>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          上传 PDF 或 TXT，生成双人对谈播客，随时随地收听
        </p>
      </div>

      <div
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer
          ${dragOver ? "border-zinc-900 bg-zinc-100 dark:border-zinc-100 dark:bg-zinc-800" : "border-zinc-300 dark:border-zinc-700 hover:border-zinc-500"}
        `}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setDragOver(false); const f = e.dataTransfer.files[0]; if (f) handleFile(f); }}
        onClick={() => document.getElementById("file-input")?.click()}
      >
        <input
          id="file-input"
          type="file"
          accept=".pdf,.txt"
          className="hidden"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
        />
        {uploading ? (
          <div className="space-y-2">
            <div className="w-8 h-8 border-2 border-zinc-900 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-sm text-zinc-500">正在上传和解析...</p>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="text-3xl">+</div>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              点击或拖拽上传 PDF / TXT 文件
            </p>
          </div>
        )}
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      <div className="space-y-2">
        <h2 className="text-sm font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wide">
          我的书架
        </h2>
        {books.length === 0 ? (
          <p className="text-sm text-zinc-400 dark:text-zinc-500 py-8 text-center">
            还没有书本，上传一本试试吧
          </p>
        ) : (
          <div className="space-y-3">
            {books.map((book) => (
              <a
                key={book.id}
                href={`/book/${book.id}`}
                className="block p-4 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 hover:border-zinc-400 dark:hover:border-zinc-700 transition-colors"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-zinc-900 dark:text-zinc-100 truncate">
                      {book.title}
                    </h3>
                    <p className="text-xs text-zinc-400 dark:text-zinc-500 mt-1">
                      {book.total_chapters} 个章节
                      {book.completed_chapters > 0 && ` · 已完成 ${book.completed_chapters}`}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <StatusBadge status={book.status} />
                    <button
                      onClick={(e) => handleDelete(book.id, e)}
                      className="text-zinc-400 hover:text-red-500 dark:hover:text-red-400 p-1"
                      title="删除"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
                {book.status === "generating" && (
                  <div className="mt-2 w-full bg-zinc-200 dark:bg-zinc-800 rounded-full h-1.5">
                    <div
                      className="bg-amber-500 h-1.5 rounded-full transition-all duration-500"
                      style={{
                        width: `${(book.completed_chapters / Math.max(book.total_chapters, 1)) * 100}%`,
                      }}
                    />
                  </div>
                )}
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
