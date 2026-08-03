# -*- coding: utf-8 -*-
"""Banco de preguntas + mezclador anti-repetición.

Las categorías NUNCA se muestran al jugador: solo se usan internamente
para evitar que salgan muchas preguntas del mismo tipo seguidas.
"""

import random

from . import absurdas, amor, comida, dilemas, personalidad, viajes, vida

# Temas que alimentan las rondas normales (cerebro + coincidencia).
_MODULOS_NORMALES = [personalidad, viajes, comida, absurdas, vida, amor]


def _cargar(modulo, prefijo):
    salida = []
    for i, (texto, opciones) in enumerate(modulo.PREGUNTAS):
        salida.append({
            "id": "%s%03d" % (prefijo, i),
            "texto": texto,
            "opciones": list(opciones),
            "tema": modulo.TEMA,
        })
    return salida


NORMALES = []
for _m in _MODULOS_NORMALES:
    NORMALES.extend(_cargar(_m, _m.TEMA[:3]))

DILEMAS = _cargar(dilemas, "dil")

TOTAL_PREGUNTAS = len(NORMALES) + len(DILEMAS)


def _espaciar(items, ventana=2):
    """Reordena para que no aparezcan >`ventana` preguntas del mismo tema seguidas.

    Algoritmo voraz: en cada paso elige el primer candidato cuyo tema no
    haya salido en las últimas `ventana` posiciones. Si no hay ninguno
    (final de la baraja), acepta el que toque.
    """
    restantes = list(items)
    salida = []
    while restantes:
        recientes = [q["tema"] for q in salida[-ventana:]]
        elegido = None
        for i, q in enumerate(restantes):
            if q["tema"] not in recientes:
                elegido = restantes.pop(i)
                break
        if elegido is None:
            elegido = restantes.pop(0)
        salida.append(elegido)
    return salida


class Baraja:
    """Reparte preguntas sin repetir hasta agotar el banco."""

    def __init__(self, semilla=None):
        self._rnd = random.Random(semilla)
        self._normales = self._nueva_baraja_normal()
        self._dilemas = self._nueva_baraja_dilemas()

    def _nueva_baraja_normal(self):
        mazo = list(NORMALES)
        self._rnd.shuffle(mazo)
        return _espaciar(mazo)

    def _nueva_baraja_dilemas(self):
        mazo = list(DILEMAS)
        self._rnd.shuffle(mazo)
        return mazo

    def sacar_normal(self):
        if not self._normales:
            self._normales = self._nueva_baraja_normal()
        return self._normales.pop(0)

    def sacar_dilema(self):
        if not self._dilemas:
            self._dilemas = self._nueva_baraja_dilemas()
        return self._dilemas.pop(0)
