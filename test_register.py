from fastapi.testclient import TestClient
from main import app, get_db #archivo principal

client = TestClient(app)

def test_crear_usuario():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM usuarios")

    conn.commit()
    cursor.close()
    conn.close()

    response = client.post("/post", json={
        "email": "test@mail.com",
        "clave": "1234",
        "rol": "doctor"
    })

    #verificacion de que respondio bien 
    assert response.status_code == 200

    #verificar mensaje
    assert response.json()["mensaje"] == "usuario creado"
