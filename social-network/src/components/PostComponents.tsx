"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { api, PostOut } from "@/lib/api";

const REACTION_EMOJI: Record<string, string> = {
  like: "👍",
  love: "❤️",
  wow: "😮",
  sad: "😢",
  angry: "😠",
};

export function CreatePost({ onCreated }: { onCreated: (post: PostOut) => void }) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleCreate = async () => {
    if (!title.trim()) return;
    setLoading(true);
    setError("");
    try {
      const post = await api.createPost({ title: title.trim(), content: content.trim() });
      setTitle("");
      setContent("");
      setOpen(false);
      onCreated(post);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="bg-emerald-600 hover:bg-emerald-700 text-white gap-2">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          Новый пост
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Создать пост</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <Input
            placeholder="Заголовок"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <Textarea
            placeholder="Содержание..."
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={5}
          />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Button
            onClick={handleCreate}
            disabled={loading || !title.trim()}
            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
          >
            {loading ? "Создание..." : "Опубликовать"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function PostCard({
  post,
  currentUserId,
  onDeleted,
  onReactionToggled,
}: {
  post: PostOut;
  currentUserId: number;
  onDeleted?: () => void;
  onReactionToggled?: () => void;
}) {
  const [reactions, setReactions] = useState<Record<string, number>>(
    Object.fromEntries(
      Object.entries(
        post.reactions.reduce<Record<string, number>>((acc, r) => {
          acc[r.type] = (acc[r.type] || 0) + 1;
          return acc;
        }, {})
      )
    )
  );
  const [myReactions, setMyReactions] = useState<Set<string>>(
    new Set(post.reactions.filter((r) => r.user_id === currentUserId).map((r) => r.type))
  );
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(post.title);
  const [editContent, setEditContent] = useState(post.content);

  const toggleReaction = async (type: string) => {
    try {
      if (myReactions.has(type)) {
        await api.removeReaction(post.id, type);
        setMyReactions((prev) => { const n = new Set(prev); n.delete(type); return n; });
        setReactions((prev) => ({ ...prev, [type]: Math.max(0, (prev[type] || 1) - 1) }));
      } else {
        await api.addReaction({ post_id: post.id, type });
        setMyReactions((prev) => new Set(prev).add(type));
        setReactions((prev) => ({ ...prev, [type]: (prev[type] || 0) + 1 }));
      }
      onReactionToggled?.();
    } catch {
      // ignore
    }
  };

  const handleSaveEdit = async () => {
    try {
      await api.updatePost(post.id, { title: editTitle, content: editContent });
      setEditing(false);
      onReactionToggled?.();
    } catch {
      // ignore
    }
  };

  const handleDelete = async () => {
    try {
      await api.deletePost(post.id);
      onDeleted?.();
    } catch {
      // ignore
    }
  };

  const date = new Date(post.created_at).toLocaleDateString("ru-RU", {
    day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
  });

  return (
    <Card className="shadow-sm hover:shadow-md transition-shadow border-0 bg-white dark:bg-gray-900">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {post.title}
            </CardTitle>
            <p className="text-xs text-muted-foreground mt-1">
              <span className="font-medium text-emerald-600">@{post.author_username}</span> · {date}
            </p>
          </div>
          {post.author_id === currentUserId && (
            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => { setEditTitle(post.title); setEditContent(post.content); setEditing(true); }}
                className="text-gray-400 hover:text-emerald-600 h-8 w-8 p-0"
              >
                ✏️
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleDelete}
                className="text-gray-400 hover:text-red-600 h-8 w-8 p-0"
              >
                🗑️
              </Button>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {editing ? (
          <div className="space-y-3">
            <Input value={editTitle} onChange={(e) => setEditTitle(e.target.value)} />
            <Textarea value={editContent} onChange={(e) => setEditContent(e.target.value)} rows={3} />
            <div className="flex gap-2">
              <Button size="sm" onClick={handleSaveEdit} className="bg-emerald-600 hover:bg-emerald-700 text-white">
                Сохранить
              </Button>
              <Button size="sm" variant="outline" onClick={() => setEditing(false)}>
                Отмена
              </Button>
            </div>
          </div>
        ) : (
          <>
            {post.content && (
              <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap mb-3">
                {post.content}
              </p>
            )}
            <div className="flex flex-wrap gap-1.5 pt-2 border-t dark:border-gray-800">
              {Object.entries(REACTION_EMOJI).map(([type, emoji]) => (
                <button
                  key={type}
                  onClick={() => toggleReaction(type)}
                  className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-sm transition-all ${
                    myReactions.has(type)
                      ? "bg-emerald-100 dark:bg-emerald-900 ring-1 ring-emerald-400"
                      : "bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700"
                  }`}
                >
                  <span>{emoji}</span>
                  {(reactions[type] || 0) > 0 && (
                    <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                      {reactions[type]}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
