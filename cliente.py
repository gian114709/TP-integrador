import os
import socket
import threading
from getpass import getpass

# El cliente se conecta al servidor y envía los mensajes que escribe el usuario.

HOST = os.getenv("REDES_SERVIDOR_IP", "127.0.0.1")
PUERTO = 12345


def recibir_mensajes(entrada, desconectado):
    # Este hilo muestra los mensajes que llegan mientras el usuario escribe.
    for linea in entrada:
        print("\n" + linea.rstrip("\r\n") + "\n> ", end="", flush=True)
    desconectado.set()


def iniciar_cliente():
    # Pide los datos, inicia sesión y mantiene abierta la conversación.
    usuario = input("Usuario: ").strip().lower()
    clave = getpass("Contraseña: ")

    try:
        with socket.create_connection((HOST, PUERTO)) as conexion:
            with conexion.makefile("r", encoding="utf-8") as entrada:
                conexion.sendall((usuario + "\n" + clave + "\n").encode("utf-8"))
                respuesta = entrada.readline().rstrip("\r\n")
                print(respuesta)
                if not respuesta.startswith("OK "):
                    return

                desconectado = threading.Event()
                receptor = threading.Thread(
                    target=recibir_mensajes, args=(entrada, desconectado), daemon=True
                )
                receptor.start()

                while not desconectado.is_set():
                    mensaje = input("> ")
                    conexion.sendall((mensaje + "\n").encode("utf-8"))
                    if mensaje.strip().lower() == "/adios":
                        receptor.join(timeout=2)
                        break
    except ConnectionRefusedError:
        print("No se pudo conectar. Iniciá primero servidor.py.")
    except (KeyboardInterrupt, EOFError):
        print("\nCliente cerrado.")
    except OSError as error:
        print(f"Conexión cerrada: {error}")


if __name__ == "__main__":
    iniciar_cliente()
