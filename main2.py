from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Literal

app = FastAPI()

#clases BaseModel

class Usuario():
    email: str
    clave: str
    rol: Literal{"doctor", "paciente"} #solo permite estos valores

class Doctor(BaseModel):
    nombre: str
    apellido: str
    especialidad: str
    #unir luego con horarios


class Paciente(BaseModel):
    nombre: str
    apellido: str
    plan: str
    historial: str

class Horarios(BaseModel):
    dias: str
    hora: str

#=====================================================
#CONEXION A LA BASE DE DATOS
#=====================================================

def get_db():
    return conn = psycopg2.connect(host = "localhost", database= "usuar", user= "progres", password="Serafina-1318", cursor_factory= RealDictCursor)

#======================================================
#CREAR TABLAS
#======================================================

@app.on_event("startup")
def startup():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuario(
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE,
    clave TEXT,
    rol TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctor(id SERIAL PRIMARY KEY,
    usuario_id INTEGER UNIQUE,
    nombre TEXT,
    apellido TEXT,
    especialidad TEXT,

    FOREIGN KEY (usuario_id) REFERENCES usuario(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS paciente(
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER UNIQUE,
    nombre TEXT,
    apellido TEXT,
    plan TEXT,
    
    FOREIGN KEY (usuario_id) REFERENCES usuario(id) )
    """)

    conn.commit()
    cursor.close()
    conn.close()

#===========================================================
# REGISTRO COMPLETO
#===========================================================

@app.post("/register")
def registrar_usuario(usuario: Usuario, datos: dict):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO usuario (email, clave, rol) VALUES (%s, %s, %s) RETURNING id;", (usuario.email, usuario.clave, usuario.rol))

    data = cursor.fetchone()
    usuario_id = data["id"]

    if usuario.rol == "doctor":
        cursor.execute("INSERT INTO doctor (usuario_id, nombre, apellido, especialidad) VALUES (%s, %s, %s)", (usuario_id, datos["nombre"], datos["apellido"], datos["especialidad"]))
    elif usuario.rol == "paciente":
        cursor.execute("INSERT INTO paciente (usuario_id, nombre, apellido, plan, historial) VALUES (%s, %s, %s, %s)", (usuario_id, datos["nombre"], datos["apellido"], datos["plan"], datos["historial"]))

    conn.commit()
    cursor.close()
    conn.close()

#============================================================
#VER DOCTORES
#=============================================================

@app.get("/doctores")
def ver_doctores():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT usuario.id, usuario.email, usuario.clave, usuario.rol, doctor.usuario_id, doctor.nombre, doctor.apellido, doctor.especialidad
    FROM usuario
    JOIN doctor ON usuario.id = doctor.usuario_id;
    """)

    resultado = cursor.fetchall()

    cursor.close()
    conn.close()

    return resultado

    
@app.get("/pacientes")
def ver_pacientes():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT usuario.id, usuario.email, usuario.clave, usuario.rol, paciente.usuario_id paciente.nombre, paciente.apellido, paciente.plan, paciente.historial
    FROM usuario
    JOIN paciente ON usuario.id = paciente.usuario_id;
    """)

    resultado = cursor.fetchall()

    cursor.close()
    conn.close()

    return resultado