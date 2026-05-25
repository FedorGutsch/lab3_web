"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { api, UserOut } from "@/lib/api";
import { useAuth } from "@/lib/store";

export function ProfileSection() {
  const { user, setUser } = useAuth();
  const [editing, setEditing] = useState(false);
  const [username, setUsername] = useState(user?.username || "");
  const [email, setEmail] = useState(user?.email || "");
  const [bio, setBio] = useState(user?.bio || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!user) return null;

  const handleSave = async () => {
    setLoading(true);
    setError("");
    try {
      const updated = await api.updateMe({ username, email, bio });
      setUser(updated);
      setEditing(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="shadow-sm border-0 bg-white dark:bg-gray-900">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Мой профиль</CardTitle>
          {!editing && (
            <Button variant="outline" size="sm" onClick={() => setEditing(true)}>
              Редактировать
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {editing ? (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Имя пользователя</Label>
              <Input value={username} onChange={(e) => setUsername(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Email</Label>
              <Input value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>О себе</Label>
              <Textarea value={bio} onChange={(e) => setBio(e.target.value)} rows={3} />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <div className="flex gap-2">
              <Button onClick={handleSave} disabled={loading} className="bg-emerald-600 hover:bg-emerald-700 text-white">
                Сохранить
              </Button>
              <Button variant="outline" onClick={() => setEditing(false)}>Отмена</Button>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center gap-4">
              <Avatar className="w-16 h-16">
                <AvatarFallback className="bg-emerald-100 text-emerald-700 text-xl font-bold">
                  {user.username[0]?.toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{user.username}</h3>
                <p className="text-sm text-muted-foreground">{user.email}</p>
              </div>
            </div>
            {user.bio && <p className="text-sm text-gray-600 dark:text-gray-400">{user.bio}</p>}
            <div className="flex gap-3">
              <Badge variant="secondary" className="bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400">
                {user.subscribers_count} подписчиков
              </Badge>
              <Badge variant="secondary" className="bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-400">
                {user.subscriptions_count} подписок
              </Badge>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function UserCard({
  user,
  currentUserId,
  onViewProfile,
  onSubscriptionChanged,
}: {
  user: UserOut;
  currentUserId: number;
  onViewProfile: (user: UserOut) => void;
  onSubscriptionChanged?: () => void;
}) {
  const [subscribed, setSubscribed] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user.id !== currentUserId) {
      api.checkSubscription(user.id).then((r) => setSubscribed(r.subscribed)).catch(() => {});
    }
  }, [user.id, currentUserId]);

  const toggleSub = async () => {
    setLoading(true);
    try {
      if (subscribed) {
        await api.unsubscribe(user.id);
      } else {
        await api.subscribe(user.id);
      }
      setSubscribed(!subscribed);
      onSubscriptionChanged?.();
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="shadow-sm border-0 bg-white dark:bg-gray-900 hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <button
            onClick={() => onViewProfile(user)}
            className="flex items-center gap-3 hover:opacity-80 transition-opacity"
          >
            <Avatar className="w-10 h-10">
              <AvatarFallback className="bg-emerald-100 text-emerald-700 text-sm font-bold">
                {user.username[0]?.toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div className="text-left">
              <p className="font-medium text-gray-900 dark:text-gray-100">@{user.username}</p>
              <p className="text-xs text-muted-foreground">{user.subscribers_count} подписчиков</p>
            </div>
          </button>
          {user.id !== currentUserId && (
            <Button
              size="sm"
              variant={subscribed ? "outline" : "default"}
              onClick={toggleSub}
              disabled={loading}
              className={subscribed ? "" : "bg-emerald-600 hover:bg-emerald-700 text-white"}
            >
              {subscribed ? "Отписаться" : "Подписаться"}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function SearchSection({
  currentUserId,
  onViewProfile,
}: {
  currentUserId: number;
  onViewProfile: (user: UserOut) => void;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<UserOut[]>([]);
  const [searching, setSearching] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const users = await api.searchUsers(query.trim());
      setResults(users);
    } catch {
      // ignore
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <Input
          placeholder="Поиск пользователей..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
        />
        <Button onClick={handleSearch} disabled={searching} className="bg-emerald-600 hover:bg-emerald-700 text-white shrink-0">
          {searching ? "..." : "Найти"}
        </Button>
      </div>
      {results.length > 0 && (
        <div className="space-y-2 max-h-80 overflow-y-auto">
          {results.map((u) => (
            <UserCard key={u.id} user={u} currentUserId={currentUserId} onViewProfile={onViewProfile} />
          ))}
        </div>
      )}
    </div>
  );
}

export function UserProfileView({
  user,
  currentUserId,
  onBack,
  onSubscriptionChanged,
}: {
  user: UserOut;
  currentUserId: number;
  onBack: () => void;
  onSubscriptionChanged?: () => void;
}) {
  const [posts, setPosts] = useState<import("@/lib/api").PostOut[]>([]);
  const [subscribed, setSubscribed] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user.id !== currentUserId) {
      api.checkSubscription(user.id).then((r) => setSubscribed(r.subscribed)).catch(() => {});
    }
  }, [user.id, currentUserId]);

  useEffect(() => {
    // Fetch user's posts
    const fetchPosts = async () => {
      try {
        const allPosts = await api.getPosts("all");
        setPosts(allPosts.filter((p) => p.author_id === user.id));
      } catch {
        // ignore
      }
    };
    fetchPosts();
  }, [user.id]);

  const toggleSub = async () => {
    setLoading(true);
    try {
      if (subscribed) {
        await api.unsubscribe(user.id);
      } else {
        await api.subscribe(user.id);
      }
      setSubscribed(!subscribed);
      onSubscriptionChanged?.();
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <Button variant="ghost" onClick={onBack} className="gap-2 text-muted-foreground">
        ← Назад
      </Button>
      <Card className="shadow-sm border-0 bg-white dark:bg-gray-900">
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <Avatar className="w-16 h-16">
              <AvatarFallback className="bg-emerald-100 text-emerald-700 text-xl font-bold">
                {user.username[0]?.toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">@{user.username}</h2>
              <p className="text-sm text-muted-foreground">{user.bio || "Нет описания"}</p>
              <div className="flex gap-3 mt-2">
                <Badge variant="secondary" className="bg-emerald-50 text-emerald-700">{user.subscribers_count} подписчиков</Badge>
                <Badge variant="secondary" className="bg-teal-50 text-teal-700">{user.subscriptions_count} подписок</Badge>
              </div>
            </div>
            {user.id !== currentUserId && (
              <Button
                onClick={toggleSub}
                disabled={loading}
                variant={subscribed ? "outline" : "default"}
                className={subscribed ? "" : "bg-emerald-600 hover:bg-emerald-700 text-white"}
              >
                {subscribed ? "Отписаться" : "Подписаться"}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
      <div className="space-y-3">
        <h3 className="font-semibold text-gray-700 dark:text-gray-300">Посты ({posts.length})</h3>
        {posts.map((p) => (
          <Card key={p.id} className="shadow-sm border-0 bg-white dark:bg-gray-900">
            <CardContent className="p-4">
              <h4 className="font-medium text-gray-900 dark:text-gray-100">{p.title}</h4>
              {p.content && <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{p.content}</p>}
              <p className="text-xs text-muted-foreground mt-2">
                {new Date(p.created_at).toLocaleDateString("ru-RU", { day: "numeric", month: "short", year: "numeric" })}
              </p>
            </CardContent>
          </Card>
        ))}
        {posts.length === 0 && <p className="text-sm text-muted-foreground">Нет постов</p>}
      </div>
    </div>
  );
}
