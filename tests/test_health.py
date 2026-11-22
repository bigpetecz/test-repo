import unittest


class HealthCheckTests(unittest.TestCase):
    def test_health_returns_ok_status(self):
        from fastapi.testclient import TestClient

        from main import app

        client = TestClient(app)
        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
