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
OCUPADO = "ocupado"


INACTIVO_S = 5.0     # sin cuadros durante este tiempo, la cámara queda libre para otro dispositivo


class Canal:
    """Un canal por cámara. Solo un dispositivo puede transmitir a la vez: si dos celulares enviaran a
    la misma cámara, sus cuadros se intercalarían (dos escenas distintas) y el seguimiento fallaría."""

    def __init__(self):
        self.cond = threading.Condition()
        self.frame = None
        self.seq = 0
        self.ultimo = 0.0
        self.emisor = None          # conexión dueña del canal
        self.reclamado = 0.0
        self.recibidos = 0

    def _ocupado_por_otro(self, emisor) -> bool:
        if self.emisor is None or self.emisor == emisor:
            return False
        return time.monotonic() - max(self.ultimo, self.reclamado) < INACTIVO_S

    def reclamar(self, emisor) -> bool:
        """Intenta tomar el canal para este dispositivo. False si otro transmite en este momento."""
        with self.cond:
            if self._ocupado_por_otro(emisor):
                return False
            self.emisor, self.reclamado = emisor, time.monotonic()
            return True

    def liberar(self, emisor):
        with self.cond:
            if self.emisor == emisor:
                self.emisor = None

    def publicar(self, frame, emisor) -> bool:
        with self.cond:
            if self._ocupado_por_otro(emisor):
                return False
            self.frame = frame
            self.seq += 1
            self.ultimo = time.monotonic()
            self.emisor = emisor
            self.recibidos += 1
            self.cond.notify_all()
            return True

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
        return self.frame is not None and time.monotonic() - self.ultimo < INACTIVO_S


class HubNavegador:
    def __init__(self):
        self._canales: dict[int, Canal] = {}
        self._lock = threading.Lock()

    def canal(self, cam_id: int) -> Canal:
        with self._lock:
            return self._canales.setdefault(cam_id, Canal())

    def publicar_jpeg(self, cam_id: int, datos: bytes, emisor):
        """Devuelve (ancho, alto), None si el JPEG no es válido u OCUPADO si otro dispositivo transmite."""
        frame = cv2.imdecode(np.frombuffer(datos, dtype=np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            return None
        if not self.canal(cam_id).publicar(frame, emisor):
            return OCUPADO
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
