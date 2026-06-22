from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Depends
from typing import Literal, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from auth import crear_token, obtener_usuario
from datetime import datetime, timedelta

app = FastAPI()

# =====================================================
# CONEXIÓN DB
# =====================================================

def get_db():
    return psycopg2.connect( host="localhost", database="usuar", user="postgres", password="Serafina1318", cursor_factory=RealDictCursor )


# =====================================================
# CREAR TABLAS
# =====================================================

@app.on_event("startup")
def startup():
    conn = get_db()
    cursor = conn.cursor()

    # TABLA USUARIO
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuario(
        id SERIAL PRIMARY KEY,
        email TEXT UNIQUE,
        clave TEXT,
        rol TEXT
    );
    """)

    #TABLA DOCTOR
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

    #TABLA PACIENTE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS paciente(
        id SERIAL PRIMARY KEY,
        usuario_id INTEGER UNIQUE,
        nombre TEXT,
        apellido TEXT,
        plan TEXT,
        FOREIGN KEY (usuario_id) REFERENCES usuario(id)
    );
    """) #hay que sacar el historial y eliminar la tabla

    #TABLA HORARIOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS horarios(
        id SERIAL PRIMARY KEY,
        doctor_id INTEGER,
        dia_semana TEXT,
        hora_inicial TIME,
        hora_final TIME,
        duracion_turno TIME,
        FOREIGN KEY (doctor_id) REFERENCES doctor(id)
        )
    """)

    #TABLA TURNOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS turnos(
    id SERIAL PRIMARY KEY,
    doctor_id INTEGER,
    paciente_id INTEGER,
    fecha DATE,
    hora TIME,
    estado TEXT,

    FOREIGN KEY (doctor_id) REFERENCES doctor(id),
    FOREIGN KEY (paciente_id) REFERENCES paciente(id)
    )
    """)
    conn.commit()
    cursor.close()
    conn.close()

#======================================================
# CLASE REGISTRO
#======================================================
class Registro(BaseModel):
    email: str
    clave: str
    rol: Literal["doctor", "paciente"]

#======================================================
# VALIDACIONES PARA REGISTRO
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

#============================================
# REGISTRO
#============================================

@app.post("/registro")
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

#============================================
# LOGIN
#============================================
class Login(BaseModel):
    email: str
    clave: str

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

#======================================================
# COMPLETAR DATOS DOCTOR
#======================================================

class Doctor(BaseModel):
    nombre: str
    apellido: str
    especialidad: str

@app.post("/completar-doctor")
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

#======================================================
# COMPLETAR DATOS PACIENTE
#======================================================
class Paciente(BaseModel):
    nombre: str
    apellido: str
    plan: str

@app.post("/completar-paciente")
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

class Horario(BaseModel):
    dia_semana: str
    hora_de_inicio: str
    hora_de_finalizacion: str
    duracion_de_turno: str

@app.post("/agregar-horario")
def agregar_horario(horario: Horario, usuario: dict = Depends(obtener_usuario)):
    conn = get_db()
    cursor = conn.cursor()
    if usuario["rol"] != "doctor":
        raise HTTPException(status_code=403, detail="NO ESTAS AUTORIZADO PARA USAR ESTA FUNCION")

    cursor.execute(
    "SELECT id FROM doctor WHERE usuario_id = %s",
    (usuario["id"],))

    doctor = cursor.fetchone()

    cursor.execute("INSERT INTO horarios (doctor_id, dia_semana, hora_inicial, hora_final, duracion_turno) VALUES (%s, %s, %s, %s, %s)", (doctor["id"], horario.dia_semana, horario.hora_de_inicio, horario.hora_de_finalizacion, horario.duracion_de_turno))

    #faltan el manejo de errores con sus advertencias
    #que el dia sea uno de la semana
    #que los horarios sean correctos y en formato indicado (que se hace cuando los turnos pasan de un dia para el otro... aunque no creo, las consultas son de dia... aunque una consulta para la guardia estaria bueno)
    conn.commit()
    cursor.close()
    conn.close()

#=====================================================================
# RESERVAR TURNO
#=====================================================================

class Turno(BaseModel):
    doctor_id: int
    dia_semana: str
    hora: str
    fecha: str
    #como paso el id del medico

dias_semana = {
    "lunes": 0,
    "martes": 1,
    "miercoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sabado": 5,
    "domingo": 6
}


@app.post("/reservar-turno")
def reservar_turno(turno: Turno):
    #verificaciones:
    #¿Existe el médico?
    #¿Ese día coincide con los días que trabaja?
    #¿La hora está dentro de su horario laboral?
    #¿La hora coincide con un turno válido según la duración?
    #¿Ya existe un turno reservado para ese médico, fecha y hora?

    print("turno: ", turno) #turno:  doctor_id=1 dia_semana='lunes' hora='8:00' fecha='08/06/2025'

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM doctor WHERE id= %s", (turno.doctor_id,))

    resultado = cursor.fetchone()

    if resultado["id"] is None:
        raise HTTPException(
            status_code=404,
            detail="Doctor no encontrado"
        )

    print("resultado: ", resultado)
    #resultado:  RealDictRow({'id': 1, 'usuario_id': 1, 'nombre': 'Ludmila', 'apellido': 'Vaca', 'especialidad': 'Programacion'})
    print("resultado['id']: ", resultado["id"])
    #resultado['id']:  1
    

    #controlamos la fecha

    try:
        fecha = datetime.strptime(turno.fecha, "%d/%m/%Y")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="EL FORMATO DE LA FECHA DEBE SER DD/MM/AAAA"
        )

   #ACA ABAJO PONER EL SELECT

    #EXTRAER LA HORA DE INICIO Y FINALIZACION DEL TURNO Y LA DURACION DEL MISMO
    cursor.execute("SELECT * FROM horarios WHERE doctor_id = %s", (turno.doctor_id,)) 

    #Despues cambiar a fetchall() para que acceda a varios horarios de un medico
    hora = cursor.fetchone()
    #hora["hora_inicial"]


#HAY ERROR, AQUI DEBE ESTAR EL SELECT TRAE LO DE HORA (ESTA ABAJO) Y DEBERIA SER hora["dia_semana"] en lugar de turno.dia_semana aqui justo abajo: 
#ERROR CORREGIDO
    if fecha.weekday() != dias_semana[hora["dia_semana"]]:
        raise HTTPException(
            status_code= 404,
            detail = "Ese dia el medico no atiende"
        )

    try:
        hora_solicitada = datetime.strptime(
            turno.hora, 
            "%H:%M:%S"
        )
    except ValueError:
        raise HTTPException(
            status_code= 400,
            detail= "EL FORMATO DE LA HORA DEBE SER HORA:MINUTOS:SEGUNDOS"
        )


    #Los print de abajo son del SELECT que estaba aqui antes
    print("hora['hora_de_inicio']: ", hora["hora_inicial"])
    print("hora['hora_final']: ", hora["hora_final"])
    print("hora['duracion_turno']", hora["duracion_turno"])

    #Ya las tenemos (luego borrar los print )
    #ahora usamos combine para unir fecha con hora y usar timedelta (duda para despues: hay una opcion distinta a timedelta para sumar minutos y que no necesite usar combine? )

    inicio = datetime.combine(
        fecha, #datetime.today() es para poner la fecha de hoy
        hora["hora_inicial"]
    )

    fin = datetime.combine(
        fecha, 
        hora["hora_final"]
    )

    print("INICIO = ", inicio)
    print("FIN = ", fin)

    #extraemos los minutos de la duracion del turno

    duracion = hora["duracion_turno"].minute + (hora["duracion_turno"].hour * 60)

    print("DURACION = ", duracion)

    #Generacion de posibles turnos

    actual = inicio
    posibles_horarios = []


    while actual < fin:
        posibles_horarios.append(actual.time())
        actual += timedelta(minutes=duracion)

    
    print("posibles_horarios = ", posibles_horarios)
    
    cursor.execute(
    """
    SELECT hora
    FROM turnos
    WHERE doctor_id = %s
    AND fecha = %s
    """,
    (turno.doctor_id, fecha)
    )

    horarios_ocupados = cursor.fetchall()

    ocupados = []

    for fila in horarios_ocupados:
        ocupados.append(fila["hora"])

    disponibles = []

    for horario in posibles_horarios:
        if horario not in ocupados:
            disponibles.append(horario)

    
    print("DISPONIBLES = ", disponibles)

    disponibles_mostrar = []

    for hora in disponibles:
        hora = hora.strftime("%H:%M")
        disponibles_mostrar.append(hora)

    print("DISPONIBLES PARA MOSTRAR= ", disponibles_mostrar)

    #LUEGO BORRAR LOS PRINT

    if hora_solicitada.time() not in disponibles:
        raise HTTPException(
            status_code = 400,
            detail = "ESE HORARIO YA ESTA RESERVADO"
        )

    #EMPEZAMOS CON LA RESERVACION?
    
    conn.commit()
    cursor.close()
    conn.close()

    return 0

if __name__ == "__main__":

    turno_prueba = Turno(
        doctor_id=1,
        dia_semana="lunes",
        hora="08:00:00",
        fecha="15/06/2026"
    )

    print(reservar_turno(turno_prueba))

