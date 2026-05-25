import React, { useState } from "react";
import { api } from "../api";

const EMOJIS = ["👍", "❤️", "😂", "😮", "😢"];

export default function ReactionBar({ postId, reactions, me, onReload }) {
  const [loading, setLoading] = useState(false);

  const toggle = async (emoji) => {
    setLoading(true);
    try {
      await api.toggleReaction(postId, emoji);
      onReload();
    } catch {}
    setLoading(false);
  };

  const myReaction = me ? reactions.find((r) => r.user_id === me.id) : null;

  return (
    <div className="reaction-bar">
      {EMOJIS.map((e) => {
        const count = reactions.filter((r) => r.emoji === e).length;
        const isActive = myReaction && myReaction.emoji === e;
        return (
          <button
            key={e}
            onClick={() => toggle(e)}
            disabled={loading}
            className={`reaction-btn${isActive ? " active" : ""}`}
          >
            {e} {count > 0 && <span className="count">{count}</span>}
          </button>
        );
      })}
    </div>
  );
}
