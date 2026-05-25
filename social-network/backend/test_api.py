"""
Глубокое тестирование API Social Network.
Подменяет DATABASE_URL на SQLite перед любым импортом.
"""
import sys
import os
import asyncio

# Подменяем движок до импорта приложения
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Создаём тестовый движок
_test_engine = create_async_engine("sqlite+aiosqlite:///./test.db", echo=False)
_test_session = async_sessionmaker(_test_engine, class_=AsyncSession, expire_on_commit=False)

# Патчим модуль database до загрузки остального
import app.database as db_module
db_module.engine = _test_engine
db_module.async_session = _test_session

from app.database import Base, get_db
from app.main import app

async def override_get_db():
    async with _test_session() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

from httpx import AsyncClient, ASGITransport


async def run_tests():
    # Создаём таблицы
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        passed = 0
        failed = 0
        total = 0

        def report(name, ok, detail=""):
            nonlocal passed, failed, total
            total += 1
            if ok:
                passed += 1
                print(f"  ✅ {name}")
            else:
                failed += 1
                print(f"  ❌ {name} — {detail}")

        # ─── 1. Health ───
        print("\n═══ Health ═══")
        r = await client.get("/api/health")
        report("GET /api/health", r.status_code == 200 and r.json()["status"] == "ok")

        # ─── 2. Регистрация ───
        print("\n═══ Регистрация ═══")
        r = await client.post("/api/auth/register", json={"username": "alice", "email": "alice@test.com", "password": "pass123"})
        report("Регистрация alice", r.status_code == 200, r.text)
        alice_data = r.json()

        r = await client.post("/api/auth/register", json={"username": "bob", "email": "bob@test.com", "password": "pass456"})
        report("Регистрация bob", r.status_code == 200, r.text)
        bob_data = r.json()

        r = await client.post("/api/auth/register", json={"username": "alice", "email": "alice2@test.com", "password": "pass"})
        report("Дубликат username — 400", r.status_code == 400)

        r = await client.post("/api/auth/register", json={"username": "charlie", "email": "alice@test.com", "password": "pass"})
        report("Дубликат email — 400", r.status_code == 400)

        # ─── 3. Авторизация ───
        print("\n═══ Авторизация ═══")
        r = await client.post("/api/auth/login", json={"username": "alice", "password": "pass123"})
        report("Логин alice", r.status_code == 200, r.text)
        alice_token = r.json()["access_token"]
        alice_headers = {"Authorization": f"Bearer {alice_token}"}

        r = await client.post("/api/auth/login", json={"username": "alice", "password": "wrong"})
        report("Неверный пароль — 401", r.status_code == 401)

        r = await client.post("/api/auth/login", json={"username": "nonexistent", "password": "x"})
        report("Несуществующий пользователь — 401", r.status_code == 401)

        r = await client.post("/api/auth/login", json={"username": "bob", "password": "pass456"})
        bob_token = r.json()["access_token"]
        bob_headers = {"Authorization": f"Bearer {bob_token}"}

        # ─── 4. Профиль ───
        print("\n═══ Профиль ═══")
        r = await client.get("/api/users/me", headers=alice_headers)
        report("GET /users/me", r.status_code == 200 and r.json()["username"] == "alice")

        r = await client.put("/api/users/me", json={"bio": "Hello, I'm Alice!", "email": "alice_new@test.com"}, headers=alice_headers)
        report("PUT /users/me (bio + email)", r.status_code == 200 and r.json()["bio"] == "Hello, I'm Alice!" and r.json()["email"] == "alice_new@test.com", r.text)

        r = await client.get("/api/users/me")
        report("GET /users/me без токена — 401", r.status_code == 401)

        # ─── 5. Поиск пользователей ───
        print("\n═══ Поиск пользователей ═══")
        r = await client.get("/api/users/")
        report("GET /users/ (все)", r.status_code == 200 and len(r.json()) >= 2)

        r = await client.get("/api/users/?q=alice")
        report("GET /users/?q=alice", r.status_code == 200 and any(u["username"] == "alice" for u in r.json()))

        r = await client.get("/api/users/?q=zzz")
        report("GET /users/?q=zzz (пусто)", r.status_code == 200 and len(r.json()) == 0)

        # ─── 6. Получение профиля по ID ───
        print("\n═══ Профиль по ID ═══")
        r = await client.get(f"/api/users/{alice_data['id']}", headers=alice_headers)
        report("GET /users/{id} alice", r.status_code == 200 and r.json()["username"] == "alice")

        r = await client.get("/api/users/9999", headers=alice_headers)
        report("GET /users/9999 — 404", r.status_code == 404)

        # ─── 7. Создание постов ───
        print("\n═══ Посты — создание ═══")
        r = await client.post("/api/posts/", json={"title": "Первый пост", "content": "Привет, мир!"}, headers=alice_headers)
        report("Создание поста alice", r.status_code == 200, r.text)
        post1 = r.json()

        r = await client.post("/api/posts/", json={"title": "Пост Боба", "content": "Боб тут"}, headers=bob_headers)
        report("Создание поста bob", r.status_code == 200, r.text)
        post2 = r.json()

        r = await client.post("/api/posts/", json={"title": "Второй пост Alice", "content": "Ещё текст"}, headers=alice_headers)
        report("Второй пост alice", r.status_code == 200, r.text)

        # ─── 8. Редактирование / удаление постов ───
        print("\n═══ Посты — редактирование/удаление ═══")
        r = await client.put(f"/api/posts/{post1['id']}", json={"title": "Обновлённый пост", "content": "Новый текст"}, headers=alice_headers)
        report("PUT пост (автор)", r.status_code == 200 and r.json()["title"] == "Обновлённый пост", r.text)

        r = await client.put(f"/api/posts/{post2['id']}", json={"title": "Хак"}, headers=alice_headers)
        report("PUT чужой пост — 403", r.status_code == 403)

        r = await client.put("/api/posts/9999", json={"title": "X"}, headers=alice_headers)
        report("PUT несуществующего поста — 404", r.status_code == 404)

        # Создаём и удаляем
        r = await client.post("/api/posts/", json={"title": "На удаление", "content": "temp"}, headers=alice_headers)
        del_id = r.json()["id"]
        r = await client.delete(f"/api/posts/{del_id}", headers=alice_headers)
        report("DELETE свой пост", r.status_code == 200)

        r = await client.delete(f"/api/posts/{post2['id']}", headers=alice_headers)
        report("DELETE чужой пост — 403", r.status_code == 403)

        r = await client.delete("/api/posts/9999", headers=alice_headers)
        report("DELETE несуществующий — 404", r.status_code == 404)

        # ─── 9. Ленты ───
        print("\n═══ Ленты ═══")
        r = await client.get("/api/posts/feed", headers=alice_headers)
        report("Глобальная лента", r.status_code == 200 and len(r.json()) >= 2)

        r = await client.get("/api/posts/my", headers=alice_headers)
        report("Мои посты (alice)", r.status_code == 200 and all(p["author_username"] == "alice" for p in r.json()))

        r = await client.get("/api/posts/following", headers=alice_headers)
        report("Лента подписок (пока пусто)", r.status_code == 200)

        r = await client.get(f"/api/posts/user/{alice_data['id']}", headers=alice_headers)
        report("Посты пользователя alice", r.status_code == 200)

        # ─── 10. Подписки ───
        print("\n═══ Подписки ═══")
        bob_id = bob_data["id"]
        r = await client.post(f"/api/subscriptions/{bob_id}", headers=alice_headers)
        report("Подписка alice→bob", r.status_code == 200, r.text)

        r = await client.post(f"/api/subscriptions/{bob_id}", headers=alice_headers)
        report("Повторная подписка — 400", r.status_code == 400)

        r = await client.post(f"/api/subscriptions/{alice_data['id']}", headers=alice_headers)
        report("Подписка на себя — 400", r.status_code == 400)

        r = await client.get(f"/api/subscriptions/is_following/{bob_id}", headers=alice_headers)
        report("is_following bob — true", r.json()["is_following"] == True)

        r = await client.get("/api/subscriptions/is_following/999", headers=alice_headers)
        report("is_following 999 — false", r.json()["is_following"] == False)

        r = await client.get("/api/subscriptions/following", headers=alice_headers)
        report("Список подписок alice", r.status_code == 200 and len(r.json()) >= 1)

        # Теперь лента подписок должна вернуть посты Боба
        r = await client.get("/api/posts/following", headers=alice_headers)
        report("Лента подписок (не пусто)", r.status_code == 200 and len(r.json()) >= 1)

        # Отписка
        r = await client.delete(f"/api/subscriptions/{bob_id}", headers=alice_headers)
        report("Отписка alice→bob", r.status_code == 200)

        r = await client.delete(f"/api/subscriptions/{bob_id}", headers=alice_headers)
        report("Повторная отписка — 404", r.status_code == 404)

        # ─── 11. Реакции ───
        print("\n═══ Реакции ═══")
        r = await client.post(f"/api/reactions/{post1['id']}", json={"emoji": "👍"}, headers=bob_headers)
        report("Реакция bob👍 на пост alice", r.status_code == 200, r.text)

        r = await client.post(f"/api/reactions/{post1['id']}", json={"emoji": "❤️"}, headers=alice_headers)
        report("Реакция alice❤️ на свой пост", r.status_code == 200, r.text)

        r = await client.post(f"/api/reactions/{post1['id']}", json={"emoji": "😂"}, headers=bob_headers)
        report("Повторная реакция bob — 400", r.status_code == 400)

        r = await client.get(f"/api/reactions/{post1['id']}", headers=alice_headers)
        report("Список реакций поста", r.status_code == 200 and len(r.json()) == 2)

        r = await client.delete(f"/api/reactions/{post1['id']}", headers=bob_headers)
        report("Удаление реакции bob", r.status_code == 200)

        r = await client.delete(f"/api/reactions/{post1['id']}", headers=bob_headers)
        report("Повторное удаление реакции — 404", r.status_code == 404)

        r = await client.post("/api/reactions/9999", json={"emoji": "👍"}, headers=alice_headers)
        report("Реакция на несуществ. пост — 404", r.status_code == 404)

        # ─── 12. Реакции в объекте поста (вложенность) ───
        print("\n═══ Реакции в объекте поста ═══")
        r = await client.get("/api/posts/feed", headers=alice_headers)
        feed = r.json()
        post_with_reactions = [p for p in feed if p["id"] == post1["id"]][0]
        report("Реакции вложены в пост", len(post_with_reactions["reactions"]) >= 1)

        # ─── 13. Edge cases ───
        print("\n═══ Edge cases ═══")
        r = await client.post("/api/subscriptions/9999", headers=alice_headers)
        report("Подписка на несуществ. — 404", r.status_code == 404)

        r = await client.post("/api/posts/", json={"title": "hack", "content": "x"})
        report("Пост без токена — 401", r.status_code == 401)

        # ─── Итого ───
        print(f"\n{'='*50}")
        print(f"Всего тестов: {total}")
        print(f"Успешно: {passed}")
        print(f"Провалено: {failed}")
        print(f"{'='*50}")

    # Удаляем тестовую БД
    try:
        os.unlink("./test.db")
    except:
        pass

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
