import hashlib
import hmac
import secrets
import sqlite3
from pathlib import Path

# Esta base guarda usuarios y los datos públicos consultados en GitHub.

ARCHIVO = Path(__file__).with_name("redes.db")


def conectar():
    # Abre la base; cada función la cierra al terminar.
    return sqlite3.connect(ARCHIVO, timeout=10)


def crear_tablas():
    base = conectar()
    try:
        base.executescript("""
            CREATE TABLE IF NOT EXISTS usuarios (
                nombre TEXT PRIMARY KEY,
                sal TEXT NOT NULL,
                clave_hash TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS repositorios (
                usuario_github TEXT NOT NULL,
                nombre TEXT NOT NULL,
                url TEXT NOT NULL,
                descripcion TEXT,
                PRIMARY KEY (usuario_github, nombre)
            );

            CREATE TABLE IF NOT EXISTS followers (
                usuario_github TEXT NOT NULL,
                nombre TEXT NOT NULL,
                url TEXT NOT NULL,
                PRIMARY KEY (usuario_github, nombre)
            );
        """)
        base.commit()
    finally:
        base.close()


def calcular_hash(clave, sal):
    # Transforma la contraseña para no guardarla como texto visible.
    return hashlib.pbkdf2_hmac(
        "sha256", clave.encode("utf-8"), bytes.fromhex(sal), 100_000
    ).hex()


def crear_usuario(nombre, clave):
    sal = secrets.token_hex(16)
    clave_hash = calcular_hash(clave, sal)
    base = conectar()
    try:
        base.execute(
            "INSERT INTO usuarios (nombre, sal, clave_hash) VALUES (?, ?, ?)",
            (nombre, sal, clave_hash),
        )
        base.commit()
    finally:
        base.close()


def validar_usuario(nombre, clave):
    # Compara la contraseña ingresada con la guardada para ese usuario.
    base = conectar()
    try:
        fila = base.execute(
            "SELECT sal, clave_hash FROM usuarios WHERE nombre = ?", (nombre,)
        ).fetchone()
    finally:
        base.close()
    if fila is None:
        return False
    return hmac.compare_digest(calcular_hash(clave, fila[0]), fila[1])


def guardar_repositorios(usuario, repositorios):
    # Reemplaza los repositorios guardados de una cuenta de GitHub.
    base = conectar()
    try:
        base.execute("DELETE FROM repositorios WHERE usuario_github = ?", (usuario,))
        base.executemany(
            "INSERT INTO repositorios VALUES (?, ?, ?, ?)",
            [
                (usuario, repo["name"], repo["html_url"], repo.get("description"))
                for repo in repositorios
            ],
        )
        base.commit()
    finally:
        base.close()


def guardar_followers(usuario, followers):
    # Reemplaza los seguidores guardados de una cuenta de GitHub.
    base = conectar()
    try:
        base.execute("DELETE FROM followers WHERE usuario_github = ?", (usuario,))
        base.executemany(
            "INSERT INTO followers VALUES (?, ?, ?)",
            [(usuario, persona["login"], persona["html_url"]) for persona in followers],
        )
        base.commit()
    finally:
        base.close()
