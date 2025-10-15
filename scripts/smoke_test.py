import os
import time
import json
import httpx

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")


def get(url, token=None, **kwargs):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = httpx.get(BASE_URL + url, headers=headers, timeout=10, **kwargs)
    r.raise_for_status()
    return r


def post(url, json_body=None, token=None, **kwargs):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = httpx.post(BASE_URL + url, headers=headers, json=json_body, timeout=20, **kwargs)
    r.raise_for_status()
    return r


def main():
    print("[1] Health checks")
    assert get("/api/v1/healthz").json()["status"] == "ok"
    ready = get("/api/v1/readyz").json()
    assert ready["status"] in {"ready", "degraded"}

    print("[2] Public user register & login (admin auth needs an admin user)")
    # Create a user; if email or student_id exists, we fall back to login
    sid = 10001
    email = "admin@example.com"
    try:
        r = post(
            "/api/v1/users/register",
            json_body={
                "student_id": sid,
                "password": "secret123",
                "email": email,
                "name": "Admin User",
                "role": "admin",
            },
        )
        user = r.json()
        print("Registered:", user["user_id"])
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            print("User already registered, continuing...")
        else:
            raise

    print("[3] Admin login to get tokens")
    r = post(
        "/api/v1/admin/auth/login",
        json_body={"identifier": str(sid), "password": "secret123"},
    )
    auth = r.json()
    access = auth["access_token"]

    print("[4] Admin create/list/get/update/delete user")
    r = post(
        "/api/v1/admin/users/",
        json_body={
            "student_id": 20001,
            "password": "pw",
            "email": "u20001@example.com",
            "name": "User 20001",
        },
        token=access,
    )
    u = r.json()
    uid = u["user_id"]
    print("Created user:", uid)

    r = get("/api/v1/admin/users/?limit=1", token=access)
    assert r.json()["meta"]["limit"] == 1

    r = get(f"/api/v1/admin/users/{uid}", token=access)
    assert r.json()["user_id"] == uid

    r = httpx.put(
        BASE_URL + f"/api/v1/admin/users/{uid}",
        headers={"Authorization": f"Bearer {access}", "Content-Type": "application/json"},
        json={"name": "Updated Name"},
        timeout=10,
    )
    r.raise_for_status()

    r = httpx.delete(
        BASE_URL + f"/api/v1/admin/users/{uid}",
        headers={"Authorization": f"Bearer {access}"},
        timeout=10,
    )
    r.raise_for_status()

    print("[5] Items basic flow: create, list, get, update, delete")
    r = post(
        "/api/v1/admin/items/",
        json_body={"description": "red wallet", "status": "uploaded"},
        token=access,
    )
    item = r.json()
    item_id = item["item_id"]

    r = get("/api/v1/admin/items/?limit=1", token=access)
    assert r.json()["meta"]["limit"] == 1

    r = get(f"/api/v1/admin/items/{item_id}", token=access)
    assert r.json()["item_id"] == item_id

    r = httpx.put(
        BASE_URL + f"/api/v1/admin/items/{item_id}",
        headers={"Authorization": f"Bearer {access}", "Content-Type": "application/json"},
        json={"status": "available"},
        timeout=10,
    )
    r.raise_for_status()

    r = httpx.delete(
        BASE_URL + f"/api/v1/admin/items/{item_id}",
        headers={"Authorization": f"Bearer {access}"},
        timeout=10,
    )
    r.raise_for_status()

    print("[6] Boxes: create, list, get, update")
    r = post(
        "/api/v1/admin/boxes/",
        json_body={"location": "MMU-101", "status": True, "door_status": False, "load": 0},
        token=access,
    )
    box = r.json()
    box_id = box["box_id"]

    r = get("/api/v1/admin/boxes/?limit=1", token=access)
    assert r.json()["limit"] == 1

    r = get(f"/api/v1/admin/boxes/{box_id}", token=access)
    assert r.json()["box_id"] == box_id

    r = httpx.put(
        BASE_URL + f"/api/v1/admin/boxes/{box_id}",
        headers={"Authorization": f"Bearer {access}", "Content-Type": "application/json"},
        json={"status": True, "load": 10},
        timeout=10,
    )
    r.raise_for_status()

    print("[7] Cases: create, list, get, update, delete")
    # Need an item to attach to a case
    r = post(
        "/api/v1/admin/items/",
        json_body={"description": "blue umbrella", "status": "uploaded"},
        token=access,
    )
    item_id = r.json()["item_id"]

    r = post(
        "/api/v1/admin/cases/",
        json_body={"item_id": item_id, "box_id": box_id, "status": "open"},
        token=access,
    )
    case = r.json()
    cid = case["found_id"]

    r = get("/api/v1/admin/cases?limit=1", token=access)
    assert r.json()["limit"] == 1

    r = get(f"/api/v1/admin/cases/{cid}", token=access)
    assert r.json()["found_id"] == cid

    r = httpx.put(
        BASE_URL + f"/api/v1/admin/cases/{cid}",
        headers={"Authorization": f"Bearer {access}", "Content-Type": "application/json"},
        json={"remarks": "note"},
        timeout=10,
    )
    r.raise_for_status()

    r = httpx.delete(
        BASE_URL + f"/api/v1/admin/cases/{cid}",
        headers={"Authorization": f"Bearer {access}"},
        timeout=10,
    )
    r.raise_for_status()

    print("[8] Admin reports & metrics")
    r = get("/api/v1/admin/metrics", token=access)
    assert b"lost_and_found_users_total" in r.content

    r = get("/api/v1/admin/reports/overview", token=access)
    _ = r.json()

    print("OK: smoke tests completed")


if __name__ == "__main__":
    main()
