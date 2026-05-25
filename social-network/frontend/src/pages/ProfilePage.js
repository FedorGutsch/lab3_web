import React, { useEffect, useState, useRef } from "react";
import { api, avatarUrl, userInitials } from "../api";

export default function ProfilePage() {
  const [user, setUser] = useState(null);
  const [edit, setEdit] = useState(false);
  const [form, setForm] = useState({ email: "", bio: "" });
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const fileRef = useRef(null);

  const load = async () => {
    try {
      const u = await api.getMe();
      setUser(u);
      setForm({ email: u.email, bio: u.bio });
    } catch {}
  };

  useEffect(() => { load(); }, []);

  const save = async (e) => {
    e.preventDefault();
    try {
      await api.updateMe(form);
      setEdit(false);
      setMsg("Сохранено");
      load();
      setTimeout(() => setMsg(""), 2000);
    } catch {
      setErr("Ошибка сохранения");
    }
  };

  const handleAvatar = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      await api.uploadAvatar(file);
      load();
      setMsg("Аватар обновлён");
      setTimeout(() => setMsg(""), 2000);
    } catch (ex) {
      setErr(ex.message);
    }
  };

  if (!user) return <div className="empty-state"><p>Загрузка...</p></div>;

  return (
    <div>
      <h1 className="page-title" style={{ marginBottom: 20 }}>Мой профиль</h1>

      <div className="card">
        <div className="profile-header">
          <div className="avatar-upload" onClick={() => fileRef.current?.click()}>
            <div className="avatar avatar-lg">
              {avatarUrl(user) ? <img src={avatarUrl(user)} alt="" /> : userInitials(user)}
            </div>
            <div className="avatar-upload-overlay">Сменить</div>
            </div>
          <input ref={fileRef} type="file" accept="image/*" onChange={handleAvatar} style={{ display: "none" }} />
          <div className="profile-info">
            <h3>{user.username}</h3>
            <p>На платформе с {new Date(user.created_at).toLocaleDateString("ru")}</p>
          </div>
        </div>

        {msg && <div className="msg-success">{msg}</div>}
        {err && <div className="msg-error">{err}</div>}

        {edit ? (
          <form onSubmit={save}>
            <div className="form-group">
              <label className="form-label">Email</label>
              <input className="form-input" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </div>
            <div className="form-group">
              <label className="form-label">О себе</label>
              <textarea className="form-input" value={form.bio} onChange={(e) => setForm({ ...form, bio: e.target.value })} />
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button type="submit" className="btn btn-primary">Сохранить</button>
              <button type="button" onClick={() => setEdit(false)} className="btn btn-ghost">Отмена</button>
            </div>
          </form>
        ) : (
          <>
            <div className="profile-field">
              <div className="profile-field-label">Email</div>
              <div className="profile-field-value">{user.email}</div>
            </div>
            <div className="profile-field">
              <div className="profile-field-label">О себе</div>
              <div className="profile-field-value">{user.bio || "—"}</div>
            </div>
            <button onClick={() => setEdit(true)} className="btn btn-primary" style={{ marginTop: 12 }}>Редактировать</button>
          </>
        )}
      </div>
    </div>
  );
}
