# -*- coding: utf-8 -*-
"""Registro de salas en memoria + hilo de mantenimiento."""

import random
import threading
import time

from .game import Sala

# Sin vocales ni caracteres ambiguos (0/O, 1/I) para dictar el código en voz alta.
ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
TTL_SALA = 3 * 60 * 60      # 3 h sin actividad -> se borra
# Dos segundos bastan para los temporizadores y gastan la mitad de CPU, que
# en el plan gratuito del hosting es un recurso muy escaso.
TICK = 2.0


class Registro(object):
    def __init__(self):
        self.lock = threading.RLock()
        self.salas = {}

    def nuevo_codigo(self):
        while True:
            codigo = "".join(random.choice(ALFABETO) for _ in range(4))
            if codigo not in self.salas:
                return codigo

    def crear(self):
        with self.lock:
            codigo = self.nuevo_codigo()
            sala = Sala(codigo)
            self.salas[codigo] = sala
            return sala

    def obtener(self, codigo):
        if not codigo:
            return None
        with self.lock:
            return self.salas.get(codigo.strip().upper())

    def borrar(self, codigo):
        with self.lock:
            self.salas.pop(codigo, None)

    def limpiar(self):
        ahora = time.monotonic()
        with self.lock:
            muertas = [c for c, s in self.salas.items()
                       if ahora - s.actividad > TTL_SALA]
            for c in muertas:
                del self.salas[c]

    def tick(self):
        """Un paso de reloj: temporizadores de ronda y traspaso de host."""
        with self.lock:
            salas = list(self.salas.values())
        for sala in salas:
            with sala.lock:
                # El contador lo lleva cada cliente por su cuenta a partir de
                # los segundos que recibe: aquí solo publicamos si algo cambió.
                if sala.comprobar_tiempo():
                    sala.publicar()


REGISTRO = Registro()


def arrancar_reloj():
    def bucle():
        ultimo_limpiado = time.monotonic()
        while True:
            time.sleep(TICK)
            try:
                REGISTRO.tick()
                if time.monotonic() - ultimo_limpiado > 300:
                    REGISTRO.limpiar()
                    ultimo_limpiado = time.monotonic()
            except Exception:
                pass

    hilo = threading.Thread(target=bucle, name="reloj", daemon=True)
    hilo.start()
    return hilo
