const API = process.env.REACT_APP_API_URL || "http://localhost:8000/api";

// Время бездействия до автоматического выхода (1 минута — как lifetime access-токена)
const INACTIVITY_TIMEOUT_MS = 1 * 60 * 1000;

// ─── Хранилище токенов ───
function getAccessToken() {
  return localStorage.getItem("access_token");
}
function getRefreshToken() {
  return localStorage.getItem("refresh_token");
}
function setTokens(access, refresh) {
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
  resetActivityTimer();
}
function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

// ─── Проверка истечения JWT ───
function isTokenExpired(token) {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.exp * 1000 < Date.now();
  } catch {
    return true;
  }
}

// ─── HTTP-запрос с авто-обновлением токена ───
let refreshingPromise = null;

async function request(url, options = {}) {
  const headers = {};
  const token = getAccessToken();

  // Если body — FormData, не ставим Content-Type
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(options.body);
  }

  if (token) headers["Authorization"] = `Bearer ${token}`;

  let res = await fetch(`${API}${url}`, { ...options, headers });

  // Если access-токен истёк — пробуем обновить
  if (res.status === 401 && getRefreshToken()) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      headers["Authorization"] = `Bearer ${newToken}`;
      res = await fetch(`${API}${url}`, { ...options, headers });
    }
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Ошибка сервера" }));
    let message = err.detail || "Ошибка";
    if (Array.isArray(message)) {
      message = message.map((e) => e.msg || JSON.stringify(e)).join("; ");
    } else if (typeof message === "object") {
      message = JSON.stringify(message);
    }
    throw new Error(message);
  }
  return res.json();
}

async function refreshAccessToken() {
  // Предотвращаем параллельные обновления
  if (refreshingPromise) return refreshingPromise;

  const refresh = getRefreshToken();
  if (!refresh || isTokenExpired(refresh)) {
    clearTokens();
    window.location.href = "/login";
    return null;
  }

  refreshingPromise = (async () => {
    try {
      const res = await fetch(`${API}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refresh }),
      });

      if (!res.ok) {
        clearTokens();
        window.location.href = "/login";
        return null;
      }

      const data = await res.json();
      setTokens(data.access_token, data.refresh_token);
      return data.access_token;
    } catch {
      clearTokens();
      window.location.href = "/login";
      return null;
    } finally {
      refreshingPromise = null;
    }
  })();

  return refreshingPromise;
}

// ─── Трекинг активности пользователя ───
let inactivityTimer = null;

function resetActivityTimer() {
  if (inactivityTimer) clearTimeout(inactivityTimer);
  if (!getRefreshToken()) return;

  inactivityTimer = setTimeout(() => {
    const refresh = getRefreshToken();
    if (refresh) {
      // Refresh ещё жив — но пользователь неактивен, выкидываем
      api.logout();
      window.location.href = "/login";
    }
  }, INACTIVITY_TIMEOUT_MS);
}

// Слушаем события активности
const activityEvents = ["mousedown", "keydown", "scroll", "touchstart", "click"];
activityEvents.forEach((event) => {
  window.addEventListener(event, () => {
    if (getRefreshToken()) resetActivityTimer();
  }, { passive: true });
});

// ─── API ───
export const api = {
  // Auth
  register: (data) => request("/auth/register", { method: "POST", body: data }),
  login: async (data) => {
    const res = await request("/auth/login", { method: "POST", body: data });
    setTokens(res.access_token, res.refresh_token);
    return res;
  },
  logout: () => {
    // Сначала пробуем обычный logout (access-токен ещё жив)
    const access = getAccessToken();
    const refresh = getRefreshToken();
    if (access && !isTokenExpired(access)) {
      fetch(`${API}/auth/logout`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${access}` },
      }).catch(() => {});
    } else if (refresh) {
      // Access истёк (автологаут по бездействию) — отзываем через refresh-токен
      fetch(`${API}/auth/logout-refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refresh }),
      }).catch(() => {});
    }
    clearTokens();
    if (inactivityTimer) clearTimeout(inactivityTimer);
  },
  isLoggedIn: () => {
    const refresh = getRefreshToken();
    return !!refresh && !isTokenExpired(refresh);
  },

  // Users
  getMe: () => request("/users/me"),
  updateMe: (data) => request("/users/me", { method: "PUT", body: data }),
  uploadAvatar: (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return request("/users/me/avatar", { method: "POST", body: formData });
  },
  getUser: (id) => request(`/users/${id}`),
  searchUsers: (q) => request(`/users/?q=${encodeURIComponent(q)}`),

  // Posts
  createPost: (data) => request("/posts/", { method: "POST", body: data }),
  updatePost: (id, data) => request(`/posts/${id}`, { method: "PUT", body: data }),
  deletePost: (id) => request(`/posts/${id}`, { method: "DELETE" }),
  globalFeed: (skip = 0) => request(`/posts/feed?skip=${skip}&limit=20`),
  myPosts: (skip = 0) => request(`/posts/my?skip=${skip}&limit=20`),
  followingPosts: (skip = 0) => request(`/posts/following?skip=${skip}&limit=20`),
  userPosts: (id, skip = 0) => request(`/posts/user/${id}?skip=${skip}&limit=20`),

  // Subscriptions
  subscribe: (id) => request(`/subscriptions/${id}`, { method: "POST" }),
  unsubscribe: (id) => request(`/subscriptions/${id}`, { method: "DELETE" }),
  isFollowing: (id) => request(`/subscriptions/is_following/${id}`),

  // Reactions
  toggleReaction: (postId, emoji) => request(`/reactions/${postId}/toggle`, { method: "POST", body: { emoji } }),
  getReactions: (postId) => request(`/reactions/${postId}`),
};

// Инициализируем таймер при загрузке, если уже залогинен
if (getRefreshToken()) resetActivityTimer();

// Хелпер для URL аватара
export function avatarUrl(user) {
  if (!user) return "";
  if (user.avatar_url && user.avatar_url.startsWith("/")) {
    return `${API.replace("/api", "")}${user.avatar_url}`;
  }
  return user.avatar_url || "";
}

// Хелпер — инициалы пользователя
export function userInitials(user) {
  if (!user) return "?";
  return user.username.charAt(0).toUpperCase();
}
