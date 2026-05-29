from main2 import validar_usuario, Registro 
import pytest
from fastapi import HTTPException

#caso correcto
def test_usuario_valido():
    usuario = Registro(
        email= "test@gmail.com",
        clave="Ludmila-1318",
        rol= "doctor",
        nombre= "juan",
        apellido= "perez"
    )

    validar_usuario(usuario)

#caso arroba
def test_sin_arroba():
    usuario = Registro(
        email= "testgmail.com",
        clave="Ludmila-1318",
        rol= "doctor",
        nombre= "juan",
        apellido= "perez"
    )

    with pytest.raises(HTTPException):
        validar_usuario(usuario)

#caso: email vacio
def test_email_vacio():
    usuario = Registro(
        email= "",
        clave="Ludmila-1318",
        rol= "doctor",
        nombre= "juan",
        apellido= "perez"
    )

    with pytest.raises(HTTPException):
        validar_usuario(usuario)

#caso: no termina en .com
def test_terminacion_com():
    usuario = Registro(
        email= "testgmail",
        clave="Ludmila-1318",
        rol= "doctor",
        nombre= "juan",
        apellido= "perez"
    )

    with pytest.raises(HTTPException):
        validar_usuario(usuario)

#caso: no termina en .ar
def test_terminacion_ar():
    usuario = Registro(
        email= "testgmail",
        clave="Ludmila-1318",
        rol= "doctor",
        nombre= "juan",
        apellido= "perez"
    )

    with pytest.raises(HTTPException):
        validar_usuario(usuario)
#caso: clave vacia
def test_clave_vacia():
    usuario = Registro(
        email= "testgmail.com",
        clave="",
        rol= "doctor",
        nombre= "juan",
        apellido= "perez"
    )

    with pytest.raises(HTTPException):
        validar_usuario(usuario)

#caso: clave menor a 8 caracteres
def test_clave_menor():
    usuario = Registro(
        email= "testgmail.com",
        clave="Lu-1318",
        rol= "doctor",
        nombre= "juan",
        apellido= "perez"
    )

    with pytest.raises(HTTPException):
        validar_usuario(usuario)

#caso: clave debe tener letras
def test_clave_sin_letras():
    usuario = Registro(
        email= "testgmail.com",
        clave="1315-1318",
        rol= "doctor",
        nombre= "juan",
        apellido= "perez"
    )

    with pytest.raises(HTTPException):
        validar_usuario(usuario)
#caso: clave debe tener numeros
def test_clave_sin_numeros():
    usuario = Registro(
        email= "testgmail.com",
        clave="Ludmila-luli",
        rol= "doctor",
        nombre= "juan",
        apellido= "perez"
    )

    with pytest.raises(HTTPException):
        validar_usuario(usuario)