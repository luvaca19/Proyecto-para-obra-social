#aqui los tokens y el login
from jose import jwt #libreria para crear y leer tokens
from datetime import datetime, timedelta #para la expiracion
from fastapi import Header, HTTPException
from typing import Annotated

SECRET_KEY = "Bebe_Koda-1318" #esta es la clave interna del servidor 
#si alquien obtiene esta clave puede obtener los tokens falsos
ALGORITHM = "HS256" #es el metodo de encriptacion (usar por ahora para no complicarse)

def crear_token(data: dict):
    to_encode = data.copy()
    #encode crea los tokens
    #decode lee el token
    expire = datetime.utcnow() + timedelta(hours=1) 
    #datetime.utc() te da la fecha actual y la hora en formato UTC: 2026-04-28 20:15:00
    #timedelta(hours=1) sirve para sumar o restar tiempo, en este caso se le suma una hora a la hora actual
    #expire tiene el valor de una hora mas de la que estamos

    to_encode.update({"exp": expire})
    #actualizamos la copia del diccionario pasado en el argumento

    token = jwt.encode(to_encode, SECRET_KEY, algorithm= ALGORITHM)
    #Toma el diccionario
    #Lo firma con la clave secreta
    #y lo convierte en un string (en el token)

    return {"access_token": token}

#==================================================================
# OBTENER USUARIO
#==================================================================

def obtener_usuario(Authorization: str = Header()):
    try:
        parts = Authorization.split(" ")

        if len(parts) != 2:
            raise HTTPException(status_code=401, detail="Formato invalido")

        token = parts[1]

        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        return data

    except:
        raise HTTPException(status_code=401, detail="token invalido")
#AGREGAR COMENTARIOS ARRIBA