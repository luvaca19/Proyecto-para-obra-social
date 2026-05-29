#me aparece en rojo las partes de cursor y algunas cosas de bases de datos, me puedes decir si esta algo mal? tal vez presione algo que no me di cuenta:
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Literal, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from auth import crear_token, obtener_usuario


app = FastAPI()

# =====================================================
# MODELO ÚNICO (SIN VALIDACIONES)
# =====================================================

class Registro(BaseModel):
    email: str
    clave: str
    rol: Literal["doctor", "paciente"]

class Doctor(BaseModel):
    nombre: str
    apellido: str
    especialidad: str
    
class Paciente(BaseModel):
    nombre: str
    apellido: str
    plan: str


#======================================================
#PARA MODIFICAR HISTORIAL
#======================================================
class HistorialUpdate(BaseModel):
    historial: str

#======================================================
#MODELO LOGIN
#======================================================
class Login(BaseModel):
    email: str
    clave: str
# =====================================================
# CONEXIÓN DB
# =====================================================

def get_db():
    return psycopg2.connect(
        host="localhost",
        database="usuar", 
        user="postgres",
        password="Serafina-1318",
        cursor_factory=RealDictCursor
    )


# =====================================================
# CREAR TABLAS
# =====================================================

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
    CREATE TABLE IF NOT EXISTS doctor(
        id SERIAL PRIMARY KEY,
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
        historial TEXT,
        FOREIGN KEY (usuario_id) REFERENCES usuario(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS horarios(
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER,
    doctor_id INTEGER,
    dia DATE,
    hora TIME,
    FOREIGN KEY (doctor_id) REFERENCES doctor(id)
    );
    """)

    conn.commit()
    cursor.close()
    conn.close()

#======================================================
# VALIDACIONES
#======================================================
def validar_usuario(usuario: Registro):
    if not usuario.email:
        raise HTTPException(status_code= 400, detail= "EL EMAIL NO PUEDE ESTAR VACIO" )
    if "@" not in usuario.email:
        raise HTTPException(status_code= 400, detail= "EL EMAIL DEBE LLEVAR @")
    if not (usuario.email.endswith(".ar") or usuario.email.endswith(".com")):
        raise HTTPException(status_code= 400, detail= "EL EMAIL DEBE TERMINAR EN .com O .ar")
    if not usuario.clave:
        raise HTTPException(status_code= 400, detail="LA CLAVE NO PUEDE ESTAR VACIA")
    if len(usuario.clave) <= 8:
        raise HTTPException(status_code= 400, detail="LA CLAVE DEBE SER MAYOR A 8 CARACTERES")
    # tiene letras
    if not any(c.isalpha() for c in usuario.clave):
        raise HTTPException(status_code=400, detail="LA CLAVE DEBE TENER LETRAS")
    # tiene símbolo
    if not any(not c.isalnum() for c in usuario.clave):
        raise HTTPException(status_code=400, detail="LA CLAVE DEBE TENER AL MENOS UN CARACTER ESPECIAL")

    
    
    
    
# =====================================================
# REGISTRO 
# =====================================================

@app.post("/register")
def registrar(data: Registro):
    conn = get_db()
    cursor = conn.cursor()

    try:
        #validaciones
        validar_usuario(data)
        # Crear usuario
        cursor.execute(
            "INSERT INTO usuario (email, clave, rol) VALUES (%s, %s, %s);",
            (data.email, data.clave, data.rol)
        )

            #el doctor debe guardar sus horarios con su id
            #doctor_id = cursor.fetchone()["id"]

            #cursor.execute("INSERT INTO horarios (doctor_id, dia, hora) VALUES (%s, %s, %s)", (doctor_id,))


        conn.commit()

    except HTTPException:
        raise  # deja pasar el error tal cual

    except Exception as e:
        conn.rollback() #si hay error, borra todo desde el ultimo commit
        #si usuario cumplia con las condiciones pero doctores no, se iban a guardar los datos inconsistentemente
        #entonces borra lo que se guardo
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        cursor.close()
        conn.close()

    return {"mensaje": "usuario creado"}

#=======================================================
# COMPLETAR DATOS
#=======================================================
#para probar el token en Swangger se debe ir a Authorize y pegar Bearer eyJhbGciOiJIUzI1NiIs...
#importante la palabra Bearer
@app.post("/datos/doctor")
def completar_datos_doctor(doctor: Doctor, usuario: dict= Depends(obtener_usuario)): #es asi o (usuario=  Depends(...))
    #se supone que ahora tenemos un dict con el id, email, rol
    conn = get_db()
    cursor = conn.cursor()

    if usuario["rol"] != "doctor":
        raise HTTPException(status_code=403, detail="NO ESTAS AUTORIZADO PARA USAR ESTA FUNCION")
        
    cursor.execute("INSERT INTO doctor (usuario_id, nombre, apellido, especialidad) VALUES (%s,%s,%s,%s)", (usuario["id"], doctor.nombre, doctor.apellido, doctor.especialidad))

    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "DATOS DEL DOCTOR COMPLEADOS"}
    

@app.post("/datos/paciente")
def completar_datos_paciente(paciente: Paciente, usuario: dict = Depends(obtener_usuario)): #es asi o (usuario=  Depends(...))
    #se supone que ahora tenemos un dict con el id, email, rol
    conn = get_db()
    cursor = conn.cursor()

    if usuario["rol"] != "paciente":
        raise HTTPException(status_code=403, detail="NO ESTAS AUTORIZADO PARA USAR ESTA FUNCION")
        
    cursor.execute("INSERT INTO paciente (usuario_id, nombre, apellido, plan) VALUES (%s,%s,%s,%s)", (usuario["id"], paciente.nombre, paciente.apellido, paciente.plan))
        

    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "DATOS DEL PACIENTE COMPLETADOS"}

    


# =====================================================
# VER DOCTORES
# =====================================================

@app.get("/doctores")
def ver_doctores():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT u.id, u.email, u.rol,
           d.nombre, d.apellido, d.especialidad
    FROM usuario u
    JOIN doctor d ON u.id = d.usuario_id;
    """)

    resultado = cursor.fetchall()

    cursor.close()
    conn.close()

    return resultado


# =====================================================
# VER PACIENTES
# =====================================================

@app.get("/pacientes")
def ver_pacientes(token: str = Depends(obtener_usuario)):
    if token["rol"] != "doctor":
        raise HTTPException(status_code=403, detail="NO ESTAS AUTORIZADO PARA VER ESTA FUNCION")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT u.id, u.email, u.rol,
           p.nombre, p.apellido, p.plan, p.historial
    FROM usuario u
    JOIN paciente p ON u.id = p.usuario_id;
    """)

    resultado = cursor.fetchall()

    cursor.close()
    conn.close()

    return resultado


# =====================================================
# RESET DB
# =====================================================

@app.delete("/reset")
def reset_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    TRUNCATE TABLE doctor, paciente, usuario RESTART IDENTITY CASCADE;
    """)

    conn.commit()
    cursor.close()
    conn.close()

    return {"mensaje": "base reiniciada"}

#===========================================================
#Modificar el historial (solo lo puede hacer el doctor que lo hizo)
#===========================================================
@app.put("/paciente/{usuario_id}/historial")
def modificar_historial(usuario_id: int, data: HistorialUpdate, usuario: dict = Depends(obtener_usuario)):
    conn = get_db()
    cursor = conn.cursor()

    if usuario["rol"] != "doctor": #and usuario["id"] != id del doctor que lo hizo
        raise HTTPException(status_code=403, detail="NO ESTAS AUTORIZADO PARA USAR ESTA FUNCION")

    cursor.execute("""
    UPDATE paciente
    SET historial = %s
    WHERE usuario_id = %s 
    """, (data.historial, usuario_id))

    #MEJORAR ACTUALIZACION: al ser varios historiales, en la base de datos historial (no paciente), donde habra muchos historiales... modificar por fecha, id de doctor, id de paciente... 
    #solo estara autorizado a cambiarlo el doctor que lo hizo...

    conn.commit()
    cursor.close()
    conn.close()

    return {"mensaje": "historial actualizado"}

    #=================================================================
    # VER HORARIOS
    #=================================================================
@app.get("/horarios")
def ver_horarios():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""SELECT doctor.nombre, doctor.apellido, doctor.especialidad, horarios.doctor_id, horarios.dia, horarios.hora
    FROM doctor
    JOIN horarios ON doctor.id = horarios.doctor_id;
    """)

    resultado = cursor.fetchall()

    cursor.close()
    conn.close()

    return resultado

#====================================================================
# HACER EL LOGIN Y EL TOKEN
#====================================================================
#NOTA: como programador backend tienes que en swangger copiar y enviar tu mismo el token pero en la web el token se guarda en las cookies o en otro lugar
@app.post("/login")
def ingresar(data: Login):
    
    conn = get_db()
    cursor= conn.cursor()

    cursor.execute("SELECT id, email, clave, rol FROM usuario WHERE email = %s", (data.email,))

    respuesta = cursor.fetchone()

    cursor.close()
    conn.close()

    if respuesta is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if respuesta["clave"] != data.clave:
        raise HTTPException(status_code=401, detail="Contrasena incorrecta")

    print("el usuario ha ingresado")

    datos = {"id":respuesta["id"],"email": respuesta["email"], "rol": respuesta["rol"]}
    token = crear_token(datos)

    return token


    
#solo para control, eliminar al finalizar
@app.get("/database")
def ver_todo():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM usuario")

    resultado = cursor.fetchall()  
    cursor.close()
    conn.close()

    return resultado

    