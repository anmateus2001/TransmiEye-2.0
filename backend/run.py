"""Arranque de TransmiEye.

    python run.py                 → solo este equipo: http://127.0.0.1:8000
    python run.py --red           → accesible desde otros equipos de la red local
    python run.py --puerto 8080
"""
import argparse
import sys
from pathlib import Path

import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Servidor TransmiEye")
    p.add_argument("--red", action="store_true", help="escuchar en 0.0.0.0 (intranet)")
    p.add_argument("--puerto", type=int, default=8000)
    p.add_argument("--proxy", action="store_true", help="detrás de un proxy https (Caddy, Cloudflare): usa la IP real del cliente")
    a = p.parse_args()
    host = "0.0.0.0" if a.red else "127.0.0.1"
    print(f"\n  TransmiEye en http://{'localhost' if not a.red else '<ip-de-este-equipo>'}:{a.puerto}\n")
    # La IP real del cliente se toma de X-Forwarded-For solo si la conexión llega de un proxy confiable.
    # Por defecto se confía únicamente en procesos de este mismo equipo (127.0.0.1), como cloudflared:
    # así, con el enlace de Cloudflare, el bloqueo por intentos fallidos afecta a quien se equivoca y no a
    # todos los usuarios. --proxy confía en cualquier origen (Caddy en otro contenedor de Docker).
    uvicorn.run("app.main:app", host=host, port=a.puerto, log_level="warning",
                proxy_headers=True, forwarded_allow_ips="*" if a.proxy else "127.0.0.1")
