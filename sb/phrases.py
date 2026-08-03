# -*- coding: utf-8 -*-
"""Copy contextual: frases cortas, divertidas y ligeramente irreverentes."""

import random

_NADIE = [
    "NADIE acertó 💀",
    "NADIE acertó. ¿Quién demonios eres, {cerebro}?",
    "Cero. Absoluto cero. {cerebro} es un misterio.",
    "Eso no se lo esperaba nadie.",
    "{cerebro} acaba de romper el juego.",
]

_TODOS = [
    "Demasiado fácil. {cerebro} es un libro abierto.",
    "Todos acertaron. {cerebro}, eres predecible y lo sabes.",
    "Unanimidad. Da un poco de miedo.",
    "Nadie falló. ¿Esto es una secta?",
]

_MAYORIA = [
    "La mayoría vive dentro de la cabeza de {cerebro}.",
    "Casi todos lo vieron venir.",
    "{cerebro} no engaña a casi nadie.",
    "Bastante obvio, {cerebro}.",
]

_MINORIA = [
    "{aciertos} vive dentro de la cabeza de {cerebro}.",
    "Solo {aciertos} conoce a {cerebro} de verdad.",
    "Poca gente lo vio venir.",
    "Okay... interesante.",
    "Esto requiere explicación.",
]

_FALLOS = [
    "{fallo} no tiene ni idea de quién es {cerebro}.",
    "{fallo}, esto duele.",
    "{fallo} va por libre.",
]

_ANULADA = [
    "{cerebro} se quedó sin tiempo. Ronda anulada.",
    "Sin respuesta de {cerebro}. Nadie puntúa. Gracias, {cerebro}.",
]

_COINCIDENCIA_HIVE = [
    "Esto empieza a ser preocupante.",
    "¿En serio TODOS eligieron eso?",
    "Una sola neurona compartida.",
]

_COINCIDENCIA_TRIPLE = [
    "Tres cerebros, una idea.",
    "Sospechoso.",
    "¿Lo habéis hablado antes?",
]

_COINCIDENCIA_PAREJA = [
    "Mismo cerebro detectado.",
    "Estos dos deberían preocuparse.",
    "Coincidencia peligrosa.",
]

_COINCIDENCIA_NADA = [
    "Ni una coincidencia. Cada uno en su planeta.",
    "Cada uno a lo suyo. Precioso.",
    "Cero conexión. Se nota.",
]

# Con un solo predictor (partidas de 2) las frases en plural no pegan.
_UNO_ACIERTA = [
    "{aciertos} lo clavó.",
    "{aciertos} vive dentro de la cabeza de {cerebro}.",
    "Directo. {aciertos} conoce a {cerebro}.",
    "Sin dudarlo. Da un poco de miedo.",
]

_UNO_FALLA = [
    "{fallo} no tiene ni idea de quién es {cerebro}.",
    "Ni de lejos, {fallo}.",
    "{cerebro} acaba de romper el juego.",
    "Eso no se lo esperaba nadie.",
]

_RACHA = {
    2: ["Dos seguidas. Calentando.", "Empieza la racha."],
    3: ["🔥 RACHA x3. Estás empezando a dar miedo.", "🔥 x3. Alguien está leyendo mentes."],
    4: ["🔥 RACHA x4. Esto ya no es suerte.", "x4. Vale, esto es raro."],
    5: ["🔥 RACHA x5. Fuera de control.", "x5. Que alguien le pare."],
}

_CONVERSACION = [
    "Esto necesita contexto.",
    "Cuenta la historia.",
    "Defiende tu respuesta.",
    "No juzgamos. Bueno, un poquito.",
    "Alguien tiene que explicar esto.",
]

_DILEMA = [
    "Vaya división.",
    "Aquí se ve quién es quién.",
    "Nadie va a cambiar de opinión.",
    "Curioso reparto.",
]


def _pick(lista, **kw):
    return random.choice(lista).format(**kw)


def frase_cerebro(cerebro, aciertos, fallos, total_predictores):
    """Frase para el reveal de una ronda de predicción."""
    if total_predictores == 0:
        return ""
    n = len(aciertos)
    if total_predictores == 1:
        if n == 1:
            return _pick(_UNO_ACIERTA, cerebro=cerebro, aciertos=aciertos[0])
        return _pick(_UNO_FALLA, cerebro=cerebro, fallo=fallos[0] if fallos else "Nadie")
    if n == 0:
        base = _pick(_NADIE, cerebro=cerebro)
        if fallos and random.random() < 0.4:
            base = _pick(_FALLOS, cerebro=cerebro, fallo=fallos[0])
        return base
    if n == total_predictores:
        return _pick(_TODOS, cerebro=cerebro)
    if n > total_predictores / 2:
        return _pick(_MAYORIA, cerebro=cerebro)
    return _pick(_MINORIA, cerebro=cerebro, aciertos=" y ".join(aciertos[:2]))


def frase_anulada(cerebro):
    return _pick(_ANULADA, cerebro=cerebro)


def frase_coincidencia(grupo_mayor, total_jugadores):
    if grupo_mayor >= total_jugadores and total_jugadores >= 3:
        return _pick(_COINCIDENCIA_HIVE)
    if grupo_mayor >= 3:
        return _pick(_COINCIDENCIA_TRIPLE)
    if grupo_mayor == 2:
        return _pick(_COINCIDENCIA_PAREJA)
    return _pick(_COINCIDENCIA_NADA)


def etiqueta_coincidencia(grupo_mayor, total_jugadores):
    if grupo_mayor >= total_jugadores and total_jugadores >= 3:
        return "HIVE MIND"
    if grupo_mayor >= 3:
        return "TRIPLE BRAIN 🧠🧠🧠"
    if grupo_mayor == 2:
        return "🧠 SAME BRAIN"
    return ""


def frase_racha(racha):
    if racha in _RACHA:
        return random.choice(_RACHA[racha])
    if racha > 5:
        return "🔥 RACHA x%d. Esto ya es ilegal." % racha
    return ""


def frase_dilema():
    return _pick(_DILEMA)


def frase_conversacion():
    return _pick(_CONVERSACION)
