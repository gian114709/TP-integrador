import re

import requests

# Este archivo consulta los datos públicos de la API de GitHub.

def consultar_github(usuario, recurso):
    # Trae repositorios o seguidores; avanza de página si hay más resultados.
    if recurso not in ("repos", "followers"):
        raise ValueError("Recurso de GitHub no válido.")
    if not re.fullmatch(r"[A-Za-z0-9-]{1,39}", usuario):
        raise ValueError("Nombre de usuario de GitHub no válido.")

    url = f"https://api.github.com/users/{usuario}/{recurso}"
    encabezados = {"Accept": "application/vnd.github+json", "User-Agent": "TP-Redes"}

    resultados = []
    pagina = 1
    while True:
        try:
            respuesta = requests.get(
                url,
                params={"per_page": 100, "page": pagina},
                headers=encabezados,
                timeout=10,
            )
        except requests.RequestException as error:
            raise ValueError("No se pudo conectar con GitHub.") from error

        if respuesta.status_code == 404:
            raise ValueError("No se encontró ese usuario de GitHub.")
        if respuesta.status_code in (403, 429):
            raise ValueError("GitHub rechazó la consulta o se alcanzó su límite de uso.")
        if not respuesta.ok:
            raise ValueError(f"Error de GitHub: HTTP {respuesta.status_code}.")

        try:
            datos = respuesta.json()
        except ValueError as error:
            raise ValueError("GitHub devolvió una respuesta que no es JSON.") from error
        if not isinstance(datos, list):
            raise ValueError("GitHub devolvió una respuesta inesperada.")
        resultados.extend(datos)
        if len(datos) < 100:
            return resultados
        pagina += 1
