import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import httpx

# Ensure project root is on sys.path for `import app`
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app


async def run():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        print("[1] Health checks")
        r = await client.get("/api/v1/healthz")
        print("health:", r.status_code, r.text)
        r = await client.get("/api/v1/readyz")
        print("readyz:", r.status_code, r.text)

        print("[2] Register admin user if needed")
        payload = {
            "student_id": 10001,
            "password": "secret123",
            "email": "admin@example.com",
            "name": "Admin User",
            "role": "admin",
        }
        r = await client.post("/api/v1/users/register", json=payload)
        print("register:", r.status_code, r.text)

        print("[3] Admin login")
        r = await client.post(
            "/api/v1/admin/auth/login",
            json={"identifier": str(payload["student_id"]), "password": payload["password"]},
        )
        print("login:", r.status_code, r.text)
        if r.status_code != 200:
            return
        access = r.json().get("access_token")
        headers = {"Authorization": f"Bearer {access}"}

        print("[4] Admin user CRUD")
        r = await client.post(
            "/api/v1/admin/users/",
            headers=headers,
            json={"student_id": 20001, "password": "pw", "email": "u20001@example.com", "name": "User 20001"},
        )
        print("create user:", r.status_code, r.text)
        if r.status_code == 200 or r.status_code == 201:
            uid = r.json()["user_id"]
            r = await client.get(f"/api/v1/admin/users/{uid}", headers=headers)
            print("get user:", r.status_code)
            r = await client.put(
                f"/api/v1/admin/users/{uid}", headers={**headers, "Content-Type": "application/json"}, json={"name": "Updated Name"}
            )
            print("update user:", r.status_code)
            r = await client.delete(f"/api/v1/admin/users/{uid}", headers=headers)
            print("delete user:", r.status_code)

        print("[5] Items basic flow")
        r = await client.post(
            "/api/v1/admin/items/",
            headers=headers,
            json={"description": "red wallet", "status": "uploaded"},
        )
        print("create item:", r.status_code, r.text)
        if r.status_code in (200, 201):
            item_id = r.json()["item_id"]
            r = await client.get(f"/api/v1/admin/items/{item_id}", headers=headers)
            print("get item:", r.status_code)
            r = await client.put(
                f"/api/v1/admin/items/{item_id}", headers={**headers, "Content-Type": "application/json"}, json={"status": "available"}
            )
            print("update item:", r.status_code)
            r = await client.delete(f"/api/v1/admin/items/{item_id}", headers=headers)
            print("delete item:", r.status_code)

        print("[6] Boxes")
        r = await client.post(
            "/api/v1/admin/boxes/",
            headers=headers,
            json={"location": "MMU-101", "status": True, "door_status": False, "load": 0},
        )
        print("create box:", r.status_code, r.text)
        if r.status_code in (200, 201):
            box_id = r.json()["box_id"]
            r = await client.get(f"/api/v1/admin/boxes/{box_id}", headers=headers)
            print("get box:", r.status_code)
            r = await client.put(
                f"/api/v1/admin/boxes/{box_id}", headers={**headers, "Content-Type": "application/json"}, json={"status": True, "load": 10}
            )
            print("update box:", r.status_code)

        print("[7] Cases")
        # Create an item for the case
        r = await client.post(
            "/api/v1/admin/items/",
            headers=headers,
            json={"description": "blue umbrella", "status": "uploaded"},
        )
        if r.status_code in (200, 201):
            item_id = r.json()["item_id"]
            # Create case
            r = await client.post(
                "/api/v1/admin/cases/",
                headers=headers,
                json={"item_id": item_id, "status": "open"},
            )
            print("create case:", r.status_code, r.text)

        print("[8] Reports & metrics")
        r = await client.get("/api/v1/admin/metrics", headers=headers)
        print("metrics:", r.status_code)
        r = await client.get("/api/v1/admin/reports/overview", headers=headers)
        print("report:", r.status_code)


if __name__ == "__main__":
    asyncio.run(run())
