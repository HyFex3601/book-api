from fastapi.testclient import TestClient
from app.main import app
import uuid


client = TestClient(app)



def test_get_books():
    check_book = client.get("/books")

    assert check_book.status_code == 200

def test_nonexistent_book():
    check_book = client.get("/books/99999")

    assert check_book.status_code == 404

def test_register():
    unique_name = str(uuid.uuid4())[:8]

    check_register = client.post("/register", json={"username": unique_name, "password": "testpass123"})

    assert check_register.status_code == 200

def test_login():

    login_test_user = str(uuid.uuid4())[:8]

    client.post("/register", json={"username": login_test_user, "password": "testpass123"})

    check_login = client.post("/login", data={"username": login_test_user, "password": "testpass123"})

    assert check_login.status_code == 200


def test_sql_injection_login():
    sql_injection = client.post("/login", data={"username": "' OR '1'='1'", "password": "anything"})

    assert sql_injection.status_code == 404