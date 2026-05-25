import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, avatarUrl, userInitials } from "../api";
import ReactionBar from "../components/ReactionBar";

export default function MyPostsPage() {
  const [posts, setPosts] = useState([]);
  const [me, setMe] = useState(null);
  const nav = useNavigate();

  const load = async () => {
    try {
      const [p, u] = await Promise.all([api.myPosts(), api.getMe()]);
      setPosts(p);
      setMe(u);
    } catch {}
  };

  useEffect(() => { load(); }, []);

  const del = async (id) => {
    if (!window.confirm("Удалить пост?")) return;
    await api.deletePost(id);
    load();
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Мои посты</h1>
        <button onClick={() => nav("/create-post")} className="btn btn-primary btn-sm">+ Новый пост</button>
      </div>

      {posts.map((p) => (
        <div key={p.id} className="card">
          <div className="post-header">
            <div className="avatar">
              {me && avatarUrl(me) ? <img src={avatarUrl(me)} alt="" /> : userInitials(me || {})}
            </div>
            <div>
              <b>{p.author_username}</b>
              <div className="post-date">{new Date(p.created_at).toLocaleString("ru")}</div>
            </div>
          </div>
          <div className="post-title">{p.title}</div>
          <div className="post-content">{p.content}</div>
          <ReactionBar postId={p.id} reactions={p.reactions || []} me={me} onReload={load} />
          <div className="post-actions">
            <button onClick={() => nav(`/edit-post/${p.id}`, { state: { post: p } })} className="btn btn-ghost btn-sm">Редактировать</button>
            <button onClick={() => del(p.id)} className="btn btn-danger btn-sm">Удалить</button>
          </div>
        </div>
      ))}

      {posts.length === 0 && (
        <div className="empty-state"><p>У вас пока нет постов</p></div>
      )}
    </div>
  );
}
