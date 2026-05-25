"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/lib/store";
import { api, PostOut, UserOut } from "@/lib/api";
import { AuthForm } from "@/components/AuthForm";
import { CreatePost, PostCard } from "@/components/PostComponents";
import { ProfileSection, UserCard, SearchSection, UserProfileView } from "@/components/UserComponents";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

type View = "feed" | "profile" | "search" | "user-profile";

export default function Home() {
  const { user, loading, fetchMe, logout } = useAuth();
  const [view, setView] = useState<View>("feed");
  const [posts, setPosts] = useState<PostOut[]>([]);
  const [feedType, setFeedType] = useState<"all" | "mine" | "subscriptions">("all");
  const [subscriptions, setSubscriptions] = useState<UserOut[]>([]);
  const [viewingUser, setViewingUser] = useState<UserOut | null>(null);
  const [postsLoading, setPostsLoading] = useState(false);

  useEffect(() => {
    fetchMe();
  }, [fetchMe]);

  const loadPosts = useCallback(async () => {
    if (!user) return;
    setPostsLoading(true);
    try {
      const data = await api.getPosts(feedType);
      setPosts(data);
    } catch {
      // ignore
    } finally {
      setPostsLoading(false);
    }
  }, [user, feedType]);

  useEffect(() => {
    loadPosts();
  }, [loadPosts]);

  const loadSubscriptions = useCallback(async () => {
    if (!user) return;
    try {
      const data = await api.getSubscriptions();
      setSubscriptions(data);
    } catch {
      // ignore
    }
  }, [user]);

  useEffect(() => {
    loadSubscriptions();
  }, [loadSubscriptions]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950">
        <div className="animate-pulse text-emerald-600 font-medium">Загрузка...</div>
      </div>
    );
  }

  if (!user) {
    return <AuthForm />;
  }

  const handleViewProfile = (u: UserOut) => {
    setViewingUser(u);
    setView("user-profile");
  };

  const handleBackFromProfile = () => {
    setViewingUser(null);
    setView("feed");
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b dark:border-gray-800">
        <div className="max-w-2xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-emerald-600 rounded-lg flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <span className="font-bold text-emerald-700 dark:text-emerald-400 text-lg">СоцСеть</span>
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant={view === "feed" ? "default" : "ghost"}
              size="sm"
              onClick={() => setView("feed")}
              className={view === "feed" ? "bg-emerald-600 hover:bg-emerald-700 text-white" : ""}
            >
              Лента
            </Button>
            <Button
              variant={view === "search" ? "default" : "ghost"}
              size="sm"
              onClick={() => setView("search")}
              className={view === "search" ? "bg-emerald-600 hover:bg-emerald-700 text-white" : ""}
            >
              Поиск
            </Button>
            <Button
              variant={view === "profile" ? "default" : "ghost"}
              size="sm"
              onClick={() => setView("profile")}
              className={view === "profile" ? "bg-emerald-600 hover:bg-emerald-700 text-white" : ""}
            >
              Профиль
            </Button>
            <Separator orientation="vertical" className="h-6 mx-1" />
            <Button variant="ghost" size="sm" onClick={logout} className="text-red-500 hover:text-red-600">
              Выйти
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-2xl mx-auto w-full px-4 py-6">
        {view === "feed" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Tabs value={feedType} onValueChange={(v) => setFeedType(v as typeof feedType)}>
                <TabsList className="bg-gray-100 dark:bg-gray-800">
                  <TabsTrigger value="all">Все</TabsTrigger>
                  <TabsTrigger value="mine">Мои</TabsTrigger>
                  <TabsTrigger value="subscriptions">Подписки</TabsTrigger>
                </TabsList>
              </Tabs>
              <CreatePost onCreated={loadPosts} />
            </div>

            {postsLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="animate-pulse bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm">
                    <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-1/3 mb-3" />
                    <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-2/3 mb-2" />
                    <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-1/2" />
                  </div>
                ))}
              </div>
            ) : posts.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <p className="text-lg mb-2">Постов пока нет</p>
                <p className="text-sm">
                  {feedType === "subscriptions" ? "Подпишитесь на пользователей, чтобы видеть их посты" : "Создайте первый пост!"}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {posts.map((post) => (
                  <PostCard
                    key={post.id}
                    post={post}
                    currentUserId={user.id}
                    onDeleted={loadPosts}
                    onReactionToggled={loadPosts}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {view === "profile" && (
          <div className="space-y-4">
            <ProfileSection />
            <Separator />
            <div>
              <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-3">Мои подписки ({subscriptions.length})</h3>
              {subscriptions.length > 0 ? (
                <ScrollArea className="max-h-96">
                  <div className="space-y-2">
                    {subscriptions.map((u) => (
                      <UserCard
                        key={u.id}
                        user={u}
                        currentUserId={user.id}
                        onViewProfile={handleViewProfile}
                        onSubscriptionChanged={loadSubscriptions}
                      />
                    ))}
                  </div>
                </ScrollArea>
              ) : (
                <p className="text-sm text-muted-foreground">Вы ни на кого не подписаны</p>
              )}
            </div>
          </div>
        )}

        {view === "search" && (
          <SearchSection currentUserId={user.id} onViewProfile={handleViewProfile} />
        )}

        {view === "user-profile" && viewingUser && (
          <UserProfileView
            user={viewingUser}
            currentUserId={user.id}
            onBack={handleBackFromProfile}
            onSubscriptionChanged={() => {
              loadSubscriptions();
              fetchMe();
            }}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t dark:border-gray-800 bg-white/50 dark:bg-gray-900/50 mt-auto">
        <div className="max-w-2xl mx-auto px-4 py-4 text-center text-xs text-muted-foreground">
          СоцСеть · FastAPI + React + PostgreSQL
        </div>
      </footer>
    </div>
  );
}
