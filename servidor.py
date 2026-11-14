import os
import socket
import sqlite3
import threading
from datetime import datetime

# El servidor atiende a cada cliente en un hilo distinto.
from base_datos import (
    ARCHIVO,
    crear_tablas,
    guardar_followers,
    guardar_repositorios,
    validar_usuario,
)
from github_api import consultar_github


HOST = os.getenv("REDES_ESCUCHA_IP", "127.0.0.1")
PUERTO = 12345
clientes = {}
lock_clientes = threading.Lock()
detener = threading.Event()


def enviar(conexion, lock_envio, texto):
    with lock_envio:
        conexion.sendall((texto + "\n").encode("utf-8"))


def enviar_a_todos(texto):
    # Copia la lista de conexiones y manda el mismo mensaje a cada una.
    with lock_clientes:
        conectados = list(clientes.values())
    for conexion, lock_envio in conectados:
        try:
            enviar(conexion, lock_envio, texto)
        except OSError:
            pass


def atender_cliente(conexion, direccion):
    # Comprueba el usuario y responde a sus mensajes o comandos.
    usuario = None
    autenticado = False
    lock_envio = threading.Lock()
    try:
        with conexion, conexion.makefile("r", encoding="utf-8") as entrada:
            usuario = entrada.readline().strip().lower()
            clave = entrada.readline().rstrip("\r\n")
            if not validar_usuario(usuario, clave):
                enviar(conexion, lock_envio, "ERROR Usuario o contraseña incorrectos.")
                return

            with lock_clientes:
                if usuario in clientes:
                    enviar(conexion, lock_envio, "ERROR Ese usuario ya está conectado.")
                    return
                enviar(conexion, lock_envio, f"OK Bienvenido, {usuario}.")
                clientes[usuario] = (conexion, lock_envio)
                autenticado = True

            print(f"\n{usuario} conectado desde {direccion[0]}:{direccion[1]}")
            for linea in entrada:
                mensaje = linea.strip()
                if not mensaje:
                    continue

                partes = mensaje.split(maxsplit=1)
                comando = partes[0].lower()
                argumento = partes[1] if len(partes) > 1 else ""

                if comando == "/adios":
                    enviar(conexion, lock_envio, "Hasta luego. Conexión finalizada.")
                    break
                elif comando == "/usuarios":
                    with lock_clientes:
                        nombres = sorted(clientes)
                    enviar(conexion, lock_envio, "Usuarios conectados: " + ", ".join(nombres))
                elif comando == "/hora":
                    enviar(conexion, lock_envio, "Hora del servidor: " + datetime.now().strftime("%H:%M:%S"))
                elif comando == "/todos":
                    if argumento:
                        texto = argumento.strip('"')
                        enviar_a_todos(f"{usuario} para todos: {texto}")
                    else:
                        enviar(conexion, lock_envio, "Uso: /todos mensaje")
                elif comando in ("/repos", "/followers"):
                    if not argumento or " " in argumento:
                        enviar(conexion, lock_envio, f"Uso: {comando} usuario_github")
                        continue
                    try:
                        recurso = "repos" if comando == "/repos" else "followers"
                        datos = consultar_github(argumento, recurso)
                        if recurso == "repos":
                            guardar_repositorios(argumento, datos)
                        else:
                            guardar_followers(argumento, datos)
                        enviar(conexion, lock_envio, f"Guardados {len(datos)} {recurso} de {argumento}.")
                    except (ValueError, KeyError, sqlite3.Error) as error:
                        enviar(conexion, lock_envio, f"Error: {error}")
                elif comando.startswith("/"):
                    enviar(conexion, lock_envio, "Comando no reconocido.")
                else:
                    print(f"\n{usuario}: {mensaje}")
                    enviar(conexion, lock_envio, "Mensaje recibido por el servidor.")
    except (OSError, UnicodeError):
        pass
    finally:
        if autenticado:
            with lock_clientes:
                cliente_actual = clientes.get(usuario)
                if cliente_actual is not None and cliente_actual[0] is conexion:
                    del clientes[usuario]
            print(f"\n{usuario} desconectado")


def leer_consola():
    # Permite escribir mensajes desde la terminal del servidor.
    try:
        while not detener.is_set():
            texto = input("Servidor> ").strip()
            if texto == "/salir":
                break
            if not texto:
                continue
            if texto.startswith("@"):
                nombre, separador, mensaje = texto[1:].partition(" ")
                with lock_clientes:
                    destinatario = clientes.get(nombre.lower())
                if not separador or not destinatario:
                    print("Uso: @usuario mensaje (el usuario debe estar conectado).")
                else:
                    try:
                        conexion_destino, lock_destino = destinatario
                        enviar(conexion_destino, lock_destino, f"Servidor para vos: {mensaje}")
                    except OSError:
                        print("Ese usuario se desconectó.")
            else:
                enviar_a_todos(f"Servidor para todos: {texto}")
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        detener.set()


def iniciar_servidor():
    # Abre el puerto y acepta conexiones hasta que se pida salir.
    crear_tablas()
    detener.clear()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((HOST, PUERTO))
        servidor.listen(5)
        servidor.settimeout(1)
        print(f"Servidor escuchando en {HOST}:{PUERTO}")
        print(f"Base de datos: {ARCHIVO}")
        print("Escribí @usuario mensaje para responderle a alguien, o un mensaje para todos.")
        print("Escribí /salir para detener el servidor.")
        threading.Thread(target=leer_consola, daemon=True).start()

        try:
            while not detener.is_set():
                try:
                    conexion, direccion = servidor.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break
                if detener.is_set():
                    conexion.close()
                    break
                threading.Thread(
                    target=atender_cliente, args=(conexion, direccion), daemon=True
                ).start()
        except KeyboardInterrupt:
            pass
        finally:
            detener.set()
            with lock_clientes:
                conexiones = [conexion for conexion, _ in clientes.values()]
            for conexion in conexiones:
                conexion.close()
            print("Servidor detenido.")


if __name__ == "__main__":
    iniciar_servidor()
