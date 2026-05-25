import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, avatarUrl, userInitials } from "../api";
import ReactionBar from "../components/ReactionBar";

export default function FollowingPage() {
  const [posts, setPosts] = useState([]);
  const [me, setMe] = useState(null);

  const load = async () => {
    try {
      const [p, m] = await Promise.all([api.followingPosts(), api.getMe()]);
      setPosts(p);
      setMe(m);
    } catch {}
  };

  useEffect(() => { load(); }, []);

  return (
    <div>
      <h1 className="page-title" style={{ marginBottom: 20 }}>Посты подписок</h1>
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
        <div className="empty-state"><p>Нет постов от подписок. Подпишитесь на пользователей!</p></div>
      )}
    </div>
  );
}
