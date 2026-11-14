import hashlib
import hmac
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path


ARCHIVO = Path(__file__).with_name("redes.db")


@contextmanager
def conectar():
    base = sqlite3.connect(ARCHIVO, timeout=10)
    try:
        with base:
            yield base
    finally:
        base.close()


def crear_tablas():
    with conectar() as base:
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


def calcular_hash(clave, sal):
    return hashlib.pbkdf2_hmac(
        "sha256", clave.encode("utf-8"), bytes.fromhex(sal), 100_000
    ).hex()


def crear_usuario(nombre, clave):
    sal = secrets.token_hex(16)
    clave_hash = calcular_hash(clave, sal)
    with conectar() as base:
        base.execute(
            "INSERT INTO usuarios (nombre, sal, clave_hash) VALUES (?, ?, ?)",
            (nombre, sal, clave_hash),
        )


def validar_usuario(nombre, clave):
    with conectar() as base:
        fila = base.execute(
            "SELECT sal, clave_hash FROM usuarios WHERE nombre = ?", (nombre,)
        ).fetchone()
    if fila is None:
        return False
    return hmac.compare_digest(calcular_hash(clave, fila[0]), fila[1])


def guardar_repositorios(usuario, repositorios):
    with conectar() as base:
        base.execute("DELETE FROM repositorios WHERE usuario_github = ?", (usuario,))
        base.executemany(
            "INSERT INTO repositorios VALUES (?, ?, ?, ?)",
            [
                (usuario, repo["name"], repo["html_url"], repo.get("description"))
                for repo in repositorios
            ],
        )


def guardar_followers(usuario, followers):
    with conectar() as base:
        base.execute("DELETE FROM followers WHERE usuario_github = ?", (usuario,))
        base.executemany(
            "INSERT INTO followers VALUES (?, ?, ?)",
            [(usuario, persona["login"], persona["html_url"]) for persona in followers],
        )
