import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

client = TestClient(app)

@pytest.mark.parametrize("num, expected", [
    (5, 50),       # กรณีปกติ (Positive Integer)
    (0, 0),        # กรณีเลขศูนย์ (Zero)
    (-7, -70),     # กรณีเลขติดลบ (Negative Integer)
])
def test_mul10_valid_numbers(num, expected):
    result = client.get(f"/mul10/{num}")
    assert result.status_code == 200
    assert result.json() == {"result": expected}


def test_mul10_invalid_type():
    result = client.get("/mul10/invalid_string")
    assert result.status_code == 422