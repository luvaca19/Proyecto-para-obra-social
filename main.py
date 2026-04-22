from fastapi import FastAPI, HTTPException 
from pydantic import BaseModel
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI()

class Usuario(BaseModel):
    email: str
    clave: str
    rol: str

    nombre: str
    especialidad: Optional[str]
    plan: Optional[str]

def get_db():
    try:
        conn = psycopg2.connect(host= "localhost", database= "usuar", user= "postgres", password = "Serafina-1318", cursor_factory= RealDictCursor)
        print("La base de datos esta conectada")
        return conn
    except Exception as e: #si ocurre cualquier error, lo guarda en la variable e
        print("Error conectando:", e)
        raise e #vuelve a lanzar el error

@app.on_event("startup")
def startup():
    conn = get_db()
    cursor =  conn.cursor()
    #crear tablas

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE, 
    clave TEXT,
    rol TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctores(
    id SERIAL PRIMARY KEY,
    usuario_id INT,
    nombre TEXT,
    especialidad TEXT,

    FOREIGN KEY (usuario_id) REFERENCES usuarioS(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pacientes (
    id SERIAL PRIMARY KEY,
    usuario_id INT,
    nombre TEXT,
    plan TEXT,

    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    );
    """)
    
#agregar UNIQUE al usuaerio
    cursor.close()
    conn.commit()
    conn.close()


@app.post("/post")
def crear_usuario(usuario: Usuario):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO usuarios (email, clave, rol) VALUES (%s, %s, %s) RETURNING id, rol", (usuario.email, usuario.clave, usuario.rol))
    
    data = cursor.fetchone()

    usuario_id = data["id"]
    usuario_rol = data["rol"]  

    if usuario_rol == "doctor":
        cursor.execute("INSERT INTO doctores (usuario_id, nombre, especialidad) VALUES (%s, %s, %s)", (usuario_id, usuario.nombre, usuario.especialidad))
    else:
        cursor.execute("INSERT INTO pacientes (usuario_id, nombre, plan) VALUES (%s, %s, %s)", (usuario_id, usuario.nombre, usuario.plan))
    cursor.close()
    conn.commit()
    conn.close()

    return {"mensaje": "usuario creado"}           

@app.get("/database")
def ver_usuario():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM usuarios")

    usuarios = cursor.fetchall()

    cursor.close()
    conn.close()

    print("mostrando usuarios: ", usuarios)

    return usuarios

@app.get("/post")
def traer_usuario():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT email, rol FROM usuarios")

    usuarios = cursor.fetchall()

    cursor.close()
    conn.commit()
    conn.close()

    return usuarios

@app.get("/post/doctores")
def ver_doctores():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
                   SELECT usuarios.email, usuarios.rol, doctores.nombre, doctores.especialidad
                   FROM usuarios
                   JOIN doctores ON usuarios.id = doctores.usuario_id; 
                   
    """)

    doctores = cursor.fetchall()

    cursor.close()
    conn.close()
    
    return doctores

    
    
    