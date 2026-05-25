import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { api } from "../api";

export default function CreatePostPage() {
  const nav = useNavigate();
  const location = useLocation();
  const existing = location.state?.post;

  const [form, setForm] = useState({
    title: existing?.title || "",
    content: existing?.content || "",
  });
  const [err, setErr] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    try {
      if (existing) {
        await api.updatePost(existing.id, form);
      } else {
        await api.createPost(form);
      }
      nav("/my-posts");
    } catch (e) {
      setErr(e.message);
    }
  };

  return (
    <div style={{ maxWidth: 500, margin: "0 auto" }}>
      <h1 className="page-title" style={{ marginBottom: 20 }}>
        {existing ? "Редактировать пост" : "Новый пост"}
      </h1>
      {err && <div className="msg-error">{err}</div>}
      <div className="card">
        <form onSubmit={submit}>
          <div className="form-group">
            <label className="form-label">Заголовок</label>
            <input
              className="form-input"
              placeholder="О чём ваш пост?"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Содержание</label>
            <textarea
              className="form-input"
              placeholder="Расскажите подробнее..."
              value={form.content}
              onChange={(e) => setForm({ ...form, content: e.target.value })}
            />
          </div>
          <button type="submit" className="btn btn-primary btn-block">
            {existing ? "Сохранить изменения" : "Опубликовать"}
          </button>
        </form>
      </div>
    </div>
  );
}
