const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Book {
  id: string;
  title: string;
  filename: string;
  file_type: string;
  status: string;
  total_chapters: number;
  completed_chapters: number;
  chapter_list: { index: number; title: string }[];
  error_message?: string;
  created_at: string;
}

export interface Chapter {
  id: string;
  index: number;
  title: string;
  status: string;
  duration_seconds: number | null;
  has_audio: boolean;
  audio_url: string | null;
}

export async function uploadBook(file: File): Promise<Book> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/api/books/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "上传失败");
  }
  return res.json();
}

export async function listBooks(): Promise<Book[]> {
  const res = await fetch(`${API_BASE}/api/books`);
  if (!res.ok) throw new Error("获取书本列表失败");
  return res.json();
}

export async function getBook(bookId: string): Promise<Book> {
  const res = await fetch(`${API_BASE}/api/books/${bookId}`);
  if (!res.ok) throw new Error("获取书本信息失败");
  return res.json();
}

export async function getChapters(bookId: string): Promise<Chapter[]> {
  const res = await fetch(`${API_BASE}/api/books/${bookId}/chapters`);
  if (!res.ok) throw new Error("获取章节列表失败");
  return res.json();
}

export async function generatePodcast(bookId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/books/${bookId}/generate`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "生成失败");
  }
}

export async function deleteBook(bookId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/books/${bookId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("删除失败");
}

export async function getChapterScript(
  bookId: string,
  chapterId: string
): Promise<{ id: string; script: string }> {
  const res = await fetch(
    `${API_BASE}/api/books/${bookId}/chapters/${chapterId}/script`
  );
  if (!res.ok) throw new Error("获取脚本失败");
  return res.json();
}

export function getChapterAudioUrl(bookId: string, chapterId: string): string {
  return `${API_BASE}/api/books/${bookId}/chapters/${chapterId}/audio`;
}

export function getFullAudioUrl(bookId: string): string {
  return `${API_BASE}/static/audio/${bookId}_full.mp3`;
}
