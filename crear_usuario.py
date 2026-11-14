import sqlite3
from getpass import getpass

from base_datos import crear_tablas, crear_usuario


crear_tablas()
nombre = input("Nombre de usuario: ").strip().lower()
clave = getpass("Contraseña: ")

if not nombre or not clave or " " in nombre or "\n" in nombre or "\n" in clave:
    print("Ingresá un nombre y una contraseña válidos.")
else:
    try:
        crear_usuario(nombre, clave)
        print(f"Usuario {nombre} creado.")
    except sqlite3.IntegrityError:
        print("Ese usuario ya existe.")
