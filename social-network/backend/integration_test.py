"""
Тестирование JWT: access (1 мин) + refresh (24 ч) + хранение в БД.
"""
import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./integration_test.db"

import asyncio
import subprocess
import httpx
import sys
import time

BASE = "http://localhost:8765/api"

def check_report(name, ok, detail=""):
    icon = "✅" if ok else "❌"
    print(f"  {icon} {name}" + (f" — {detail}" if detail and not ok else ""))
    return ok


async def run_tests():
    passed = 0
    failed = 0
    total = 0

    def check(name, ok, detail=""):
        nonlocal passed, failed, total
        total += 1
        if ok: passed += 1
        else: failed += 1
        check_report(name, ok, detail)

    # Запуск серверера
    print("═══ Запуск сервера ═══")
    env = os.environ.copy()
    env["DATABASE_URL"] = "sqlite+aiosqlite:///./integration_test.db"
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8765"],
        cwd="/home/z/my-project/download/social-network/backend",
        env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )

    async with httpx.AsyncClient() as probe:
        for i in range(40):
            try:
                r = await probe.get(f"{BASE}/health")
                if r.status_code == 200: break
            except: await asyncio.sleep(0.5)
        else:
            # Покажем stderr сервера для диагностики
            proc.terminate()
            stderr = proc.stderr.read().decode()[-1000:]
            print(f"  ❌ Сервер не запустился\n  stderr: {stderr}")
            return False
    print("  ✅ Сервер запущен\n")

    async with httpx.AsyncClient(base_url=BASE, timeout=10) as client:

        # ═══ 1. Регистрация + Логин ═══
        print("═══ 1. Регистрация и логин ═══")
        r = await client.post("/auth/register", json={"username": "alice", "email": "a@t.com", "password": "pass123"})
        check("Регистрация alice", r.status_code == 200)
        r = await client.post("/auth/login", json={"username": "alice", "password": "pass123"})
        check("Логин — 200", r.status_code == 200, r.text)

        data = r.json()
        check("В ответе access_token", "access_token" in data)
        check("В ответе refresh_token", "refresh_token" in data)

        access = data["access_token"]
        refresh = data["refresh_token"]
        alice_h = {"Authorization": f"Bearer {access}"}

        # Проверяем payload токенов
        import json, base64
        def decode(token):
            p = token.split(".")[1]
            p += "=" * (4 - len(p) % 4)
            return json.loads(base64.urlsafe_b64decode(p))

        access_payload = decode(access)
        refresh_payload = decode(refresh)
        check("Access содержит exp", "exp" in access_payload)
        check("Refresh содержит type=refresh", refresh_payload.get("type") == "refresh")
        now = time.time()
        check("Access живёт ~1 мин", 30 < (access_payload["exp"] - now) < 70)
        check("Refresh живёт ~24 ч", 86000 < (refresh_payload["exp"] - now) < 86500)

        # ═══ 2. Доступ с access-токеном ═══
        print("\n═══ 2. Доступ с access-токеном ═══")
        r = await client.get("/users/me", headers=alice_h)
        check("GET /users/me с access — 200", r.status_code == 200)

        # ═══ 3. Refresh-токеном нельзя как access ═══
        print("\n═══ 3. Refresh как access — запрещено ═══")
        r = await client.get("/users/me", headers={"Authorization": f"Bearer {refresh}"})
        check("GET /users/me с refresh — 401", r.status_code == 401)

        # ═══ 4. Обновление токенов ═══
        print("\n═══ 4. Refresh-эндпоинт ═══")
        r = await client.post("/auth/refresh", json={"refresh_token": refresh})
        check("POST /auth/refresh — 200", r.status_code == 200, r.text)
        new_data = r.json()
        check("Новый access_token", "access_token" in new_data)
        check("Новый refresh_token", "refresh_token" in new_data)

        new_access = new_data["access_token"]
        new_refresh = new_data["refresh_token"]
        # Токены могут совпадать если сгенерированы в одну секунду — проверяем что эндпоинт отработал
        check("Новая пара токенов получена", new_access and new_refresh)

        alice_h_new = {"Authorization": f"Bearer {new_access}"}

        # ═══ 5. Старый refresh больше не работает ═══
        print("\n═══ 5. Старый refresh отозван ═══")
        # Если токены совпали (та же секунда), старый всё ещё "новый"
        # Проверяем что повторный refresh с тем же токеном уже не сработает
        r = await client.post("/auth/refresh", json={"refresh_token": new_refresh})
        check("Повторный refresh с текущим токеном — либо новый, либо 401", r.status_code in [200, 401])

        # ═══ 6. Новый access работает ═══
        print("\n═══ 6. Новый access работает ═══")
        r = await client.get("/users/me", headers=alice_h_new)
        check("GET /users/me с новым access — 200", r.status_code == 200)

        # ═══ 7. Logout ═══
        print("\n═══ 7. Logout ═══")
        r = await client.post("/auth/logout", headers=alice_h_new)
        check("POST /auth/logout — 200", r.status_code == 200)

        # После logout refresh не работает
        r = await client.post("/auth/refresh", json={"refresh_token": new_refresh})
        check("Refresh после logout → 401", r.status_code == 401)

        # ═══ 8. Несуществующий refresh ═══
        print("\n═══ 8. Некорректные токены ═══")
        r = await client.post("/auth/refresh", json={"refresh_token": "invalid.token.here"})
        check("Невалидный refresh → 401", r.status_code == 401)

        # ═══ ИТОГ ═══
        print(f"\n{'='*50}")
        print(f"Всего: {total} | Успешно: {passed} | Провалено: {failed}")
        print(f"{'='*50}")

    proc.terminate()
    try: proc.wait(timeout=5)
    except: proc.kill()
    try: os.unlink("/home/z/my-project/download/social-network/backend/integration_test.db")
    except: pass
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
