from app import create_app


def test_authentication_rejects_duplicate_email_and_wrong_password():
    client = create_app().test_client()
    account = {"username": "calorify", "email": "auth@example.com", "password": "password123"}

    assert b"Account created" in client.post("/auth/register", data=account).data
    assert b"Email already registered" in client.post("/auth/register", data=account).data
    login = client.post("/auth/login", data={**account, "password": "incorrect"})
    assert b"Invalid email or password" in login.data
    assert client.get("/profile/").location.endswith("/auth/login")


def test_account_password_change_export_and_delete():
    client = create_app().test_client()
    account = {"username": "calorify", "email": "account@example.com", "password": "password123"}
    client.post("/auth/register", data=account)
    assert client.post("/auth/login", data=account).status_code == 302

    response = client.post("/profile/change-password", data={
        "current_password": "incorrect", "new_password": "replacement123",
    })
    assert b"Current password is incorrect" in response.data
    response = client.post("/profile/change-password", data={
        "current_password": account["password"], "new_password": "replacement123",
    })
    assert b"Password updated successfully" in response.data

    response = client.get("/profile/export")
    assert response.get_json()["account"]["email"] == account["email"]
    assert "attachment" in response.headers["Content-Disposition"]
    assert client.post("/auth/logout").status_code == 302
    assert b"Invalid email or password" in client.post("/auth/login", data=account).data
    assert client.post("/auth/login", data={**account, "password": "replacement123"}).status_code == 302
    assert client.post("/profile/delete").status_code == 302
    assert client.get("/profile/").location.endswith("/auth/login")
    assert b"Invalid email or password" in client.post(
        "/auth/login", data={**account, "password": "replacement123"}
    ).data
