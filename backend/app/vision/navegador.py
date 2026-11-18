"""Cámaras transmitidas desde un navegador (celular o PC) por WebSocket.

Una cámara con fuente "navegador" no se abre con OpenCV: su página /transmitir.html envía
cuadros JPEG al servidor y aquí se guardan para que el hilo de la cámara los procese igual que
cualquier otro video. Así el sistema puede vivir en la nube y usar la cámara de un celular
ubicado frente a las puertas de la estación.
"""
import threading
import time

import cv2
import numpy as np

FUENTE_NAVEGADOR = "navegador"


class Canal:
    def __init__(self):
        self.cond = threading.Condition()
        self.frame = None
        self.seq = 0
        self.ultimo = 0.0
        self.emisor = None          # identificador de la conexión que transmite
        self.recibidos = 0

    def publicar(self, frame, emisor):
        with self.cond:
            self.frame = frame
            self.seq += 1
            self.ultimo = time.monotonic()
            self.emisor = emisor
            self.recibidos += 1
            self.cond.notify_all()

    def esperar(self, ultimo_seq, timeout):
        """Devuelve (frame, seq) del siguiente cuadro o (None, ultimo_seq) si no llegó a tiempo."""
        with self.cond:
            fin = time.monotonic() + timeout
            while self.seq == ultimo_seq:
                resto = fin - time.monotonic()
                if resto <= 0:
                    return None, ultimo_seq
                self.cond.wait(resto)
            return self.frame, self.seq

    @property
    def activo(self):
        return self.frame is not None and time.monotonic() - self.ultimo < 5.0


class HubNavegador:
    def __init__(self):
        self._canales: dict[int, Canal] = {}
        self._lock = threading.Lock()

    def canal(self, cam_id: int) -> Canal:
        with self._lock:
            return self._canales.setdefault(cam_id, Canal())

    def publicar_jpeg(self, cam_id: int, datos: bytes, emisor) -> tuple[int, int] | None:
        frame = cv2.imdecode(np.frombuffer(datos, dtype=np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            return None
        self.canal(cam_id).publicar(frame, emisor)
        return frame.shape[1], frame.shape[0]

    def estado(self, cam_id: int) -> dict:
        c = self.canal(cam_id)
        return {"transmitiendo": c.activo, "recibidos": c.recibidos,
                "hace_s": round(time.monotonic() - c.ultimo, 1) if c.ultimo else None}


HUB = HubNavegador()


class EsperandoNavegador(ConnectionError):
    """La cámara es de navegador y nadie está transmitiendo todavía."""


class FuenteNavegador:
    """Misma interfaz que FuenteVideo, pero los cuadros llegan por WebSocket desde un navegador."""

    tipo = "navegador"

    def __init__(self, cam_id: int):
        self.canal = HUB.canal(cam_id)
        self.fps = 10.0
        self.resolucion = None
        self._seq = 0

    def abrir(self):
        if self.canal.frame is not None:
            h, w = self.canal.frame.shape[:2]
            self.resolucion = f"{w}x{h}"

    def leer(self, timeout: float = 2.0):
        frame, self._seq = self.canal.esperar(self._seq, timeout)
        if frame is not None:
            h, w = frame.shape[:2]
            self.resolucion = f"{w}x{h}"
        return frame

    def cerrar(self):
        pass
