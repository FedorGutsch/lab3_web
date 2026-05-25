import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, avatarUrl, userInitials } from "../api";
import ReactionBar from "../components/ReactionBar";

export default function UserPage() {
  const { id } = useParams();
  const [user, setUser] = useState(null);
  const [posts, setPosts] = useState([]);
  const [me, setMe] = useState(null);
  const [isFollowing, setIsFollowing] = useState(false);

  const load = async () => {
    try {
      const [u, p, f, m] = await Promise.all([
        api.getUser(id),
        api.userPosts(id),
        api.isFollowing(id),
        api.getMe(),
      ]);
      setUser(u);
      setPosts(p);
      setIsFollowing(f.is_following);
      setMe(m);
    } catch {}
  };

  useEffect(() => { load(); }, [id]);

  const toggleSub = async () => {
    try {
      if (isFollowing) await api.unsubscribe(id);
      else await api.subscribe(id);
      setIsFollowing(!isFollowing);
    } catch {}
  };

  if (!user) return <div className="empty-state"><p>Загрузка...</p></div>;

  return (
    <div>
      <div className="card">
        <div className="profile-header">
          <div className="avatar avatar-lg">
            {avatarUrl(user) ? <img src={avatarUrl(user)} alt="" /> : userInitials(user)}
          </div>
          <div className="profile-info">
            <h3>{user.username}</h3>
            <p>{user.bio || "Нет описания"}</p>
          </div>
        </div>
        <button
          onClick={toggleSub}
          className={`sub-btn ${isFollowing ? "unfollow" : "follow"}`}
        >
          {isFollowing ? "Отписаться" : "Подписаться"}
        </button>
      </div>

      <h2 style={{ fontSize: 18, fontWeight: 600, margin: "24px 0 12px" }}>Посты</h2>
      {posts.map((p) => (
        <div key={p.id} className="card">
          <div className="post-title">{p.title}</div>
          <div className="post-content">{p.content}</div>
          <ReactionBar postId={p.id} reactions={p.reactions || []} me={me} onReload={load} />
          <div className="post-date" style={{ marginTop: 8 }}>{new Date(p.created_at).toLocaleString("ru")}</div>
        </div>
      ))}
      {posts.length === 0 && (
        <div className="empty-state"><p>Нет постов</p></div>
      )}
    </div>
  );
}
