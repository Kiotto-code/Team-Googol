import io
import os
import sys
import tempfile
import unittest
from importlib import import_module

try:  # pragma: no cover - optional dependency detection
    import flask  # type: ignore
    import flask_cors  # type: ignore
    FLASK_AVAILABLE = True
except ModuleNotFoundError:
    FLASK_AVAILABLE = False

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

class EndpointFlowTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._temp_dir = tempfile.TemporaryDirectory()
        base_path = cls._temp_dir.name

        if not FLASK_AVAILABLE:
            raise unittest.SkipTest("Flask is required for endpoint tests")

        os.environ.setdefault("DISABLE_SCHEDULER", "1")
        os.environ.setdefault("DISABLE_CLIP_MODEL", "1")
        os.environ.setdefault("DATABASE_PATH", os.path.join(base_path, "test.db"))
        os.environ.setdefault("UPLOAD_FOLDER", os.path.join(base_path, "uploads"))
        os.environ.setdefault("COLLECTOR_FOLDER", os.path.join(base_path, "collectors"))
        os.environ.setdefault("ESP32_UPLOAD_FOLDER", os.path.join(base_path, "esp32"))
        os.environ.pop("GEMINI_API_KEY", None)

        for module_name in list(sys.modules):
            if module_name.startswith("backend."):
                sys.modules.pop(module_name)

        cls.database = import_module("backend.database")
        cls.database.init_database()

        app_module = import_module("backend.app")
        app_module.app.config["TESTING"] = True
        cls.app = app_module.app
        cls.client = cls.app.test_client()

        upload_module = import_module("backend.routes.upload")
        upload_module.generate_caption_with_gemini = (  # type: ignore[attr-defined]
            lambda *args, **kwargs: "Auto caption"
        )
        upload_module.is_lighting_good = (  # type: ignore[attr-defined]
            lambda *args, **kwargs: (True, 120.0, 42.0)
        )

    @classmethod
    def tearDownClass(cls):
        cls._temp_dir.cleanup()

    def _create_image_file(self, color=None):
        _ = color  # unused, kept for API similarity
        image_bytes = io.BytesIO(b"test image data")
        image_bytes.seek(0)
        return image_bytes

    def test_end_to_end_flow(self):
        user_payload = {
            "name": "Alice",
            "email": "alice@example.com",
            "password": "secret",
            "phone_number": "1234567890",
            "student_id": "S12345",
            "rfid_tag": "RFID123",
        }
        response = self.client.post("/users/register", json=user_payload)
        self.assertEqual(response.status_code, 201)
        user = response.get_json()["user"]
        user_id = user["user_id"]

        response = self.client.get(f"/users/{user_id}")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/users")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["total"], 1)

        response = self.client.get(f"/users/email/{user_payload['email']}")
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f"/users/rfid/{user_payload['rfid_tag']}")
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f"/users/student/{user_payload['student_id']}")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            f"/users/{user_id}/stats", json={"items_found": 2, "items_find": 1}
        )
        self.assertEqual(response.status_code, 200)

        box_response = self.client.post(
            "/box/register",
            json={"location": "Lobby", "status": True, "door_status": False, "load": 0},
        )
        self.assertEqual(box_response.status_code, 201)
        box_id = box_response.get_json()["box_id"]

        response = self.client.get("/box/status", query_string={"box_id": box_id})
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/box/status",
            query_string={"box_id": box_id},
            json={"door_status": True},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["door_status"])

        image_file = self._create_image_file()
        upload_response = self.client.post(
            "/upload",
            data={
                "description": "Red wallet",
                "finder_user_id": str(user_id),
                "image": (image_file, "wallet.jpg"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(upload_response.status_code, 200)
        item_id = upload_response.get_json()["item_id"]

        collector_image = self._create_image_file(color=(0, 255, 0))
        collect_response = self.client.post(
            "/collect",
            data={
                "item_id": str(item_id),
                "box_id": str(box_id),
                "image": (collector_image, "collector.jpg"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(collect_response.status_code, 200)
        case_id = collect_response.get_json()["case_id"]

        response = self.client.post(
            "/case/deposit-complete",
            json={"box_id": box_id, "case_id": case_id},
        )
        self.assertEqual(response.status_code, 200)

        claim_response = self.client.post(
            "/claim",
            json={"case_id": case_id, "receiver_id": user_id},
        )
        self.assertEqual(claim_response.status_code, 200)
        self.assertEqual(claim_response.get_json()["case_status"], "claimed")

        response = self.client.put(
            f"/case/{case_id}",
            json={"status": "retrieved", "receiver_image_url": "picked.jpg"},
        )
        self.assertEqual(response.status_code, 200)

        pickup_response = self.client.post(
            "/case/pickup-complete",
            json={"case_id": case_id, "box_id": box_id},
        )
        self.assertEqual(pickup_response.status_code, 200)
        self.assertEqual(pickup_response.get_json()["case_status"], "retrieved")

        response = self.client.get("/cases")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.get_json()["total"], 1)

        search_response = self.client.post("/search", json={"query": "wallet"})
        self.assertEqual(search_response.status_code, 200)
        self.assertGreaterEqual(search_response.get_json()["count"], 1)

        release_response = self.client.post("/release-expired")
        self.assertEqual(release_response.status_code, 200)

        delete_response = self.client.post("/delete", json={"item_id": item_id})
        self.assertEqual(delete_response.status_code, 200)

        response = self.client.delete(f"/case/{case_id}")
        self.assertEqual(response.status_code, 200)

        esp32_file = self._create_image_file(color=(0, 0, 255))
        esp32_response = self.client.post(
            "/esp32/upload/image",
            data={"file": (esp32_file, "esp32.jpg")},
            content_type="multipart/form-data",
        )
        self.assertEqual(esp32_response.status_code, 201)


if __name__ == "__main__":  # pragma: no cover - allows running directly
    unittest.main()
