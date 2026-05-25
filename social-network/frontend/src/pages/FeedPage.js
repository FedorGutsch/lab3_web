import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, avatarUrl, userInitials } from "../api";
import ReactionBar from "../components/ReactionBar";

export default function FeedPage() {
  const [posts, setPosts] = useState([]);
  const [me, setMe] = useState(null);
  const nav = useNavigate();

  const load = async () => {
    try {
      const [p, u] = await Promise.all([api.globalFeed(), api.getMe()]);
      setPosts(p);
      setMe(u);
    } catch {}
  };

  useEffect(() => { load(); }, []);

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Лента</h1>
        <button onClick={() => nav("/create-post")} className="btn btn-primary btn-sm">+ Новый пост</button>
      </div>

      {posts.map((p) => (
        <div key={p.id} className="card">
          <div className="post-header">
            <Link to={`/user/${p.author_id}`}>
              <div className="avatar">
                {avatarUrl({ avatar_url: p.author_avatar })
                  ? <img src={avatarUrl({ avatar_url: p.author_avatar })} alt="" />
                  : userInitials({ username: p.author_username })
                }
              </div>
            </Link>
            <div>
              <Link to={`/user/${p.author_id}`} className="post-author">{p.author_username}</Link>
              <div className="post-date">{new Date(p.created_at).toLocaleString("ru")}</div>
            </div>
          </div>
          <div className="post-title">{p.title}</div>
          <div className="post-content">{p.content}</div>
          <ReactionBar postId={p.id} reactions={p.reactions || []} me={me} onReload={load} />
        </div>
      ))}

      {posts.length === 0 && (
        <div className="empty-state"><p>Пока нет постов. Создайте первый!</p></div>
      )}
    </div>
  );
}
