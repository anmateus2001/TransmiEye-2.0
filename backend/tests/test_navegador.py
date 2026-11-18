"""Pruebas de las cámaras transmitidas desde un navegador (varios dispositivos a la vez).

Ejecutar desde backend/:  python -m pytest tests -q
"""
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.vision import navegador                      # noqa: E402
from app.vision.navegador import OCUPADO, Canal, HubNavegador   # noqa: E402

CUADRO = np.zeros((48, 64, 3), np.uint8)
JPEG = cv2.imencode(".jpg", CUADRO)[1].tobytes()


def test_un_solo_dispositivo_por_camara():
    c = Canal()
    assert c.reclamar("celular-1")
    assert not c.reclamar("celular-2"), "un segundo dispositivo no debe poder transmitir a la misma cámara"
    assert not c.publicar(CUADRO, "celular-2")
    assert c.publicar(CUADRO, "celular-1")


def test_reconexion_del_mismo_dispositivo():
    c = Canal()
    assert c.reclamar("usuario:sesion")
    assert c.publicar(CUADRO, "usuario:sesion")
    assert c.reclamar("usuario:sesion"), "la misma sesión debe recuperar su cámara tras un corte"


def test_liberar_al_desconectar():
    c = Canal()
    c.reclamar("celular-1")
    c.liberar("celular-1")
    assert c.reclamar("celular-2")


def test_canal_abandonado_se_libera(monkeypatch):
    c = Canal()
    c.reclamar("celular-1")
    c.publicar(CUADRO, "celular-1")
    ahora = time.monotonic()
    monkeypatch.setattr(navegador.time, "monotonic", lambda: ahora + navegador.INACTIVO_S + 1)
    assert c.reclamar("celular-2"), "si el primero dejó de enviar, otro dispositivo puede tomar la cámara"


def test_camaras_distintas_no_se_bloquean():
    hub = HubNavegador()
    assert hub.publicar_jpeg(1, JPEG, "celular-1") == (64, 48)
    assert hub.publicar_jpeg(2, JPEG, "celular-2") == (64, 48)
    assert hub.publicar_jpeg(1, JPEG, "celular-2") == OCUPADO
    assert hub.publicar_jpeg(3, b"no es un jpeg", "pc") is None
