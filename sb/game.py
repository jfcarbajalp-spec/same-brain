# -*- coding: utf-8 -*-
"""Motor de juego de Same Brain.

Toda la lógica vive en el servidor. Los clientes solo reciben la
proyección de estado que les corresponde (ver `vista_para`), de modo que
las respuestas ajenas nunca salen del proceso antes del reveal.
"""

import itertools
import queue
import random
import threading
import time

from . import phrases
from .questions import Baraja

MAX_JUGADORES = 10
MIN_JUGADORES = 2
SEGUNDOS_RESPUESTA = 30
GRACIA_HOST = 20          # segundos antes de traspasar el rol de host
GRACIA_DESCONEXION = 8    # segundos antes de dejar de esperar a alguien
# Cada cliente late cada 5 s. Si dejamos de oírle, lo damos por caído: no
# sirve fiarse de que falle la escritura en el socket (en Windows no falla).
TIMEOUT_PRESENCIA = 16

FASE_LOBBY = "lobby"
FASE_PREGUNTA = "pregunta"
FASE_REVEAL = "reveal"
FASE_FINAL = "final"

TIPO_CEREBRO = "cerebro"
TIPO_COINCIDENCIA = "coincidencia"
TIPO_DILEMA = "dilema"

BONUS_RACHA = {2: 25, 3: 50, 4: 75}


def bonus_por_racha(racha):
    if racha >= 5:
        return 100
    return BONUS_RACHA.get(racha, 0)


def tipo_de_ronda(numero):
    """Cada 5 rondas toca coincidencia; cada 7, dilema; el resto, cerebro."""
    if numero % 5 == 0:
        return TIPO_COINCIDENCIA
    if numero % 7 == 0:
        return TIPO_DILEMA
    return TIPO_CEREBRO


class Jugador(object):
    def __init__(self, pid, nombre, token):
        self.id = pid
        self.nombre = nombre
        self.token = token
        self.puntos = 0
        self.conectado = True
        self.visto = time.monotonic()
        self.aciertos = 0          # predicciones correctas
        self.intentos = 0          # predicciones hechas
        self.racha = 0
        self.mejor_racha = 0
        self.veces_cerebro = 0
        self.leido_ok = 0          # veces que otros le adivinaron
        self.leido_total = 0

    def reset_partida(self):
        self.puntos = 0
        self.aciertos = 0
        self.intentos = 0
        self.racha = 0
        self.mejor_racha = 0
        self.veces_cerebro = 0
        self.leido_ok = 0
        self.leido_total = 0

    def publico(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "puntos": self.puntos,
            "conectado": self.conectado,
            "racha": self.racha,
        }


class Sala(object):
    def __init__(self, codigo):
        self.codigo = codigo
        self.lock = threading.RLock()
        self.jugadores = {}
        self.orden_entrada = []
        self.host_id = None
        self.fase = FASE_LOBBY
        self.rondas_totales = 20      # 0 = infinito
        self.ronda_num = 0
        self.ronda = None
        self.reveal = None
        self.final = None
        self.baraja = Baraja()
        self.cola_cerebros = []
        self.ultimo_cerebro = None
        self.afinidad = {}            # (idA, idB) -> [coincidencias, oportunidades]
        self.version = 0
        self.creada = time.monotonic()
        self.actividad = time.monotonic()
        self.host_caido_desde = None
        self._suscriptores = []       # [(player_id, Queue)]

    # ------------------------------------------------------------------
    # Jugadores
    # ------------------------------------------------------------------
    def _nombre_libre(self, nombre):
        usados = set(j.nombre.lower() for j in self.jugadores.values())
        base = nombre
        n = 2
        while nombre.lower() in usados:
            nombre = "%s %d" % (base, n)
            n += 1
        return nombre

    def añadir_jugador(self, nombre):
        if len(self.jugadores) >= MAX_JUGADORES:
            raise ValueError("La sala está llena (máximo %d jugadores)." % MAX_JUGADORES)
        if self.fase not in (FASE_LOBBY, FASE_FINAL) and len(self.jugadores) >= MAX_JUGADORES:
            raise ValueError("La sala está llena.")
        pid = "p" + "".join(random.choice("abcdefghijkmnpqrstuvwxyz23456789") for _ in range(10))
        token = "".join(random.choice("abcdefghijkmnpqrstuvwxyz23456789") for _ in range(24))
        jug = Jugador(pid, self._nombre_libre(nombre), token)
        self.jugadores[pid] = jug
        self.orden_entrada.append(pid)
        if self.host_id is None:
            self.host_id = pid
        self.actividad = time.monotonic()
        return jug

    def jugador(self, pid, token=None):
        j = self.jugadores.get(pid)
        if j is None:
            return None
        if token is not None and j.token != token:
            return None
        return j

    def conectados(self):
        return [self.jugadores[p] for p in self.orden_entrada
                if p in self.jugadores and self.jugadores[p].conectado]

    def lista_jugadores(self):
        return [self.jugadores[p] for p in self.orden_entrada if p in self.jugadores]

    def marcar_conexion(self, pid, conectado):
        """Devuelve True si el estado de conexión ha cambiado."""
        j = self.jugadores.get(pid)
        if not j:
            return False
        cambio = j.conectado != conectado
        j.conectado = conectado
        if conectado:
            j.visto = time.monotonic()
        elif cambio:
            j.visto = time.monotonic()
        if pid == self.host_id:
            if conectado:
                self.host_caido_desde = None
            elif cambio:
                self.host_caido_desde = time.monotonic()
        self.actividad = time.monotonic()
        return cambio

    def barrer_presencia(self):
        """Marca como caído a quien lleva demasiado sin dar señales de vida."""
        ahora = time.monotonic()
        cambio = False
        for j in list(self.jugadores.values()):
            if j.conectado and ahora - j.visto > TIMEOUT_PRESENCIA:
                if self.marcar_conexion(j.id, False):
                    cambio = True
        return cambio

    def traspasar_host(self):
        """Pasa el rol de host al jugador conectado más antiguo."""
        for pid in self.orden_entrada:
            j = self.jugadores.get(pid)
            if j and j.conectado and pid != self.host_id:
                self.host_id = pid
                self.host_caido_desde = None
                return True
        return False

    def salir(self, pid):
        if pid not in self.jugadores:
            return
        del self.jugadores[pid]
        if pid in self.orden_entrada:
            self.orden_entrada.remove(pid)
        if self.ronda:
            self.ronda["respuestas"].pop(pid, None)
        if self.host_id == pid:
            self.host_id = None
            self.traspasar_host()
            if self.host_id == pid:
                self.host_id = None
        if self.host_id is None and self.orden_entrada:
            self.host_id = self.orden_entrada[0]

    # ------------------------------------------------------------------
    # Ciclo de partida
    # ------------------------------------------------------------------
    def configurar(self, rondas):
        if rondas not in (10, 20, 30, 0):
            raise ValueError("Duración no válida.")
        self.rondas_totales = rondas

    def empezar(self):
        if len(self.conectados()) < MIN_JUGADORES:
            raise ValueError("Hacen falta al menos %d jugadores." % MIN_JUGADORES)
        for j in self.jugadores.values():
            j.reset_partida()
        self.afinidad = {}
        self.baraja = Baraja()
        self.cola_cerebros = []
        self.ultimo_cerebro = None
        self.ronda_num = 0
        self.final = None
        self.siguiente_ronda()

    def _siguiente_cerebro(self):
        """Rotación equilibrada, evitando repetir cerebro consecutivo."""
        disponibles = [j.id for j in self.conectados()]
        if not disponibles:
            return None
        self.cola_cerebros = [p for p in self.cola_cerebros if p in disponibles]
        if not self.cola_cerebros:
            nueva = list(disponibles)
            random.shuffle(nueva)
            if len(nueva) > 1 and nueva[0] == self.ultimo_cerebro:
                nueva.append(nueva.pop(0))
            self.cola_cerebros = nueva
        elegido = self.cola_cerebros.pop(0)
        if elegido == self.ultimo_cerebro and self.cola_cerebros:
            self.cola_cerebros.append(elegido)
            elegido = self.cola_cerebros.pop(0)
        self.ultimo_cerebro = elegido
        return elegido

    def siguiente_ronda(self):
        if self.rondas_totales and self.ronda_num >= self.rondas_totales:
            self.terminar()
            return
        self.ronda_num += 1
        tipo = tipo_de_ronda(self.ronda_num)
        if tipo == TIPO_DILEMA:
            pregunta = self.baraja.sacar_dilema()
        else:
            pregunta = self.baraja.sacar_normal()

        cerebro_id = None
        if tipo == TIPO_CEREBRO:
            cerebro_id = self._siguiente_cerebro()
            if cerebro_id is None:
                tipo = TIPO_COINCIDENCIA
            else:
                self.jugadores[cerebro_id].veces_cerebro += 1

        self.ronda = {
            "tipo": tipo,
            "pregunta": pregunta,
            "cerebro_id": cerebro_id,
            "respuestas": {},
            "inicio": time.monotonic(),
            "limite": time.monotonic() + SEGUNDOS_RESPUESTA,
        }
        self.reveal = None
        self.fase = FASE_PREGUNTA
        self.actividad = time.monotonic()

    def responder(self, pid, opcion):
        if self.fase != FASE_PREGUNTA or not self.ronda:
            return False
        jug = self.jugadores.get(pid)
        if not jug:
            return False
        opciones = self.ronda["pregunta"]["opciones"]
        if not isinstance(opcion, int) or opcion < 0 or opcion >= len(opciones):
            return False
        if pid in self.ronda["respuestas"]:
            return False
        self.ronda["respuestas"][pid] = opcion
        self.actividad = time.monotonic()
        if self._todos_respondieron():
            self.hacer_reveal()
        return True

    def _pendientes(self):
        ahora = time.monotonic()
        pend = []
        for j in self.lista_jugadores():
            if j.id in self.ronda["respuestas"]:
                continue
            if j.conectado:
                pend.append(j.id)
            elif ahora - j.visto < GRACIA_DESCONEXION:
                pend.append(j.id)  # margen por si es un refresco de página
        return pend

    def _todos_respondieron(self):
        return not self._pendientes()

    def comprobar_tiempo(self):
        """Llamado por el hilo de reloj. Devuelve True si cambió algo."""
        cambio = self.barrer_presencia()
        if self.fase == FASE_PREGUNTA and self.ronda:
            if time.monotonic() >= self.ronda["limite"] or self._todos_respondieron():
                self.hacer_reveal()
                cambio = True
        if (self.host_caido_desde is not None
                and time.monotonic() - self.host_caido_desde > GRACIA_HOST):
            if self.traspasar_host():
                cambio = True
            self.host_caido_desde = None
        return cambio

    # ------------------------------------------------------------------
    # Reveal y puntuación
    # ------------------------------------------------------------------
    def _actualizar_afinidad(self):
        respuestas = self.ronda["respuestas"]
        ids = sorted(respuestas.keys())
        for a, b in itertools.combinations(ids, 2):
            clave = (a, b)
            par = self.afinidad.setdefault(clave, [0, 0])
            par[1] += 1
            if respuestas[a] == respuestas[b]:
                par[0] += 1

    def hacer_reveal(self):
        if self.fase != FASE_PREGUNTA or not self.ronda:
            return
        tipo = self.ronda["tipo"]
        self._actualizar_afinidad()
        if tipo == TIPO_CEREBRO:
            self.reveal = self._reveal_cerebro()
        elif tipo == TIPO_COINCIDENCIA:
            self.reveal = self._reveal_coincidencia()
        else:
            self.reveal = self._reveal_dilema()

        self.reveal["ronda"] = self.ronda_num
        self.reveal["pregunta"] = self.ronda["pregunta"]["texto"]
        self.reveal["opciones"] = self.ronda["pregunta"]["opciones"]
        self.reveal["tipo"] = tipo
        self.reveal["ultima"] = bool(self.rondas_totales and self.ronda_num >= self.rondas_totales)
        if self.ronda_num % 5 == 0:
            self.reveal["ranking"] = self._ranking()
        if random.random() < 0.3:
            self.reveal["conversacion"] = phrases.frase_conversacion()
        self.fase = FASE_REVEAL
        self.actividad = time.monotonic()

    def _reveal_cerebro(self):
        respuestas = self.ronda["respuestas"]
        cerebro = self.jugadores.get(self.ronda["cerebro_id"])
        resp_cerebro = respuestas.get(self.ronda["cerebro_id"])

        if cerebro is None or resp_cerebro is None:
            for j in self.lista_jugadores():
                if j.id != self.ronda["cerebro_id"]:
                    j.racha = 0
            return {
                "anulada": True,
                "cerebro": {"id": getattr(cerebro, "id", None),
                            "nombre": getattr(cerebro, "nombre", "?")},
                "respuesta_cerebro": None,
                "resultados": [],
                "frase": phrases.frase_anulada(getattr(cerebro, "nombre", "?")),
            }

        resultados = []
        aciertos_nombres = []
        fallos_nombres = []
        total_predictores = 0
        for j in self.lista_jugadores():
            if j.id == cerebro.id:
                continue
            eleccion = respuestas.get(j.id)
            if eleccion is None:
                j.racha = 0
                resultados.append({
                    "id": j.id, "nombre": j.nombre, "respuesta": None,
                    "acierto": False, "puntos": 0, "bonus": 0,
                    "racha": 0, "sin_respuesta": True,
                })
                continue
            total_predictores += 1
            j.intentos += 1
            cerebro.leido_total += 1
            if eleccion == resp_cerebro:
                j.aciertos += 1
                j.racha += 1
                j.mejor_racha = max(j.mejor_racha, j.racha)
                cerebro.leido_ok += 1
                extra = bonus_por_racha(j.racha)
                j.puntos += 100 + extra
                aciertos_nombres.append(j.nombre)
                resultados.append({
                    "id": j.id, "nombre": j.nombre, "respuesta": eleccion,
                    "acierto": True, "puntos": 100, "bonus": extra,
                    "racha": j.racha, "frase_racha": phrases.frase_racha(j.racha),
                })
            else:
                j.racha = 0
                fallos_nombres.append(j.nombre)
                resultados.append({
                    "id": j.id, "nombre": j.nombre, "respuesta": eleccion,
                    "acierto": False, "puntos": 0, "bonus": 0, "racha": 0,
                })

        return {
            "anulada": False,
            "cerebro": {"id": cerebro.id, "nombre": cerebro.nombre},
            "respuesta_cerebro": resp_cerebro,
            "resultados": resultados,
            "frase": phrases.frase_cerebro(cerebro.nombre, aciertos_nombres,
                                           fallos_nombres, total_predictores),
        }

    def _reveal_coincidencia(self):
        respuestas = self.ronda["respuestas"]
        n_opciones = len(self.ronda["pregunta"]["opciones"])
        grupos = []
        mayor = 0
        for idx in range(n_opciones):
            miembros = [self.jugadores[p] for p in self.orden_entrada
                        if p in self.jugadores and respuestas.get(p) == idx]
            if not miembros:
                continue
            mayor = max(mayor, len(miembros))
            grupos.append({
                "opcion": idx,
                "jugadores": [m.nombre for m in miembros],
                "coincide": len(miembros) >= 2,
            })
            if len(miembros) >= 2:
                for m in miembros:
                    m.puntos += 50

        resultados = []
        for j in self.lista_jugadores():
            eleccion = respuestas.get(j.id)
            gano = eleccion is not None and any(
                g["opcion"] == eleccion and g["coincide"] for g in grupos)
            resultados.append({
                "id": j.id, "nombre": j.nombre, "respuesta": eleccion,
                "acierto": gano, "puntos": 50 if gano else 0, "bonus": 0,
                "racha": j.racha, "sin_respuesta": eleccion is None,
            })

        total = len([r for r in resultados if not r.get("sin_respuesta")])
        return {
            "anulada": False,
            "grupos": grupos,
            "etiqueta": phrases.etiqueta_coincidencia(mayor, total),
            "resultados": resultados,
            "frase": phrases.frase_coincidencia(mayor, total),
        }

    def _reveal_dilema(self):
        respuestas = self.ronda["respuestas"]
        n_opciones = len(self.ronda["pregunta"]["opciones"])
        total = len(respuestas)
        reparto = []
        for idx in range(n_opciones):
            miembros = [self.jugadores[p].nombre for p in self.orden_entrada
                        if p in self.jugadores and respuestas.get(p) == idx]
            pct = int(round(100.0 * len(miembros) / total)) if total else 0
            reparto.append({"opcion": idx, "pct": pct, "jugadores": miembros})
        resultados = [{
            "id": j.id, "nombre": j.nombre, "respuesta": respuestas.get(j.id),
            "acierto": False, "puntos": 0, "bonus": 0, "racha": j.racha,
            "sin_respuesta": j.id not in respuestas,
        } for j in self.lista_jugadores()]
        return {
            "anulada": False,
            "reparto": reparto,
            "resultados": resultados,
            "frase": phrases.frase_dilema(),
        }

    # ------------------------------------------------------------------
    # Resultados
    # ------------------------------------------------------------------
    def _ranking(self):
        orden = sorted(self.lista_jugadores(), key=lambda j: -j.puntos)
        return [{"id": j.id, "nombre": j.nombre, "puntos": j.puntos,
                 "pos": i + 1} for i, j in enumerate(orden)]

    def _pct_afinidad(self, a, b):
        clave = (a, b) if a < b else (b, a)
        par = self.afinidad.get(clave)
        if not par or par[1] == 0:
            return None, 0
        return int(round(100.0 * par[0] / par[1])), par[1]

    def conexiones(self):
        salida = []
        ids = [j.id for j in self.lista_jugadores()]
        for a, b in itertools.combinations(ids, 2):
            pct, muestras = self._pct_afinidad(a, b)
            if pct is None:
                continue
            salida.append({
                "a": self.jugadores[a].nombre,
                "b": self.jugadores[b].nombre,
                "pct": pct,
                "muestras": muestras,
            })
        salida.sort(key=lambda c: -c["pct"])
        return salida

    def terminar(self):
        jugadores = self.lista_jugadores()
        if not jugadores:
            self.fase = FASE_LOBBY
            return
        orden = sorted(jugadores, key=lambda j: -j.puntos)
        ganador = orden[0]

        lectores = [j for j in jugadores if j.intentos > 0]
        mejor_lector = max(lectores, key=lambda j: (j.aciertos, j.puntos)) if lectores else None

        leidos = [j for j in jugadores if j.leido_total > 0]
        impredecible = None
        if leidos:
            candidato = min(leidos, key=lambda j: (float(j.leido_ok) / j.leido_total, -j.leido_total))
            # Si a todos les adivinaron siempre, no hay nadie impredecible.
            if candidato.leido_ok < candidato.leido_total:
                impredecible = candidato

        cons = self.conexiones()
        fiables = [c for c in cons if c["muestras"] >= 2] or cons
        # El polo opuesto solo tiene gracia si de verdad coincide menos.
        hay_contraste = len(fiables) > 1 and fiables[-1]["pct"] < fiables[0]["pct"]

        self.final = {
            "ganador": {"nombre": ganador.nombre, "puntos": ganador.puntos},
            "podio": [{"nombre": j.nombre, "puntos": j.puntos} for j in orden],
            "mejor_lector": ({"nombre": mejor_lector.nombre, "aciertos": mejor_lector.aciertos,
                              "intentos": mejor_lector.intentos} if mejor_lector else None),
            "impredecible": ({"nombre": impredecible.nombre,
                              "pct": int(round(100.0 * impredecible.leido_ok / impredecible.leido_total))}
                             if impredecible else None),
            "same_brain": (fiables[0] if fiables else None),
            "polo_opuesto": (fiables[-1] if hay_contraste else None),
            "conexiones": cons,
            "rondas": self.ronda_num,
        }
        self.fase = FASE_FINAL
        self.ronda = None
        self.reveal = None
        self.actividad = time.monotonic()

    def revancha(self):
        for j in self.jugadores.values():
            j.reset_partida()
        self.afinidad = {}
        self.ronda_num = 0
        self.ronda = None
        self.reveal = None
        self.final = None
        self.cola_cerebros = []
        self.ultimo_cerebro = None
        self.fase = FASE_LOBBY
        self.actividad = time.monotonic()

    # ------------------------------------------------------------------
    # Proyección de estado (privacidad)
    # ------------------------------------------------------------------
    def vista_para(self, pid):
        jug = self.jugadores.get(pid)
        vista = {
            "v": self.version,
            "codigo": self.codigo,
            "fase": self.fase,
            "hostId": self.host_id,
            "eresHost": pid == self.host_id,
            "rondasTotales": self.rondas_totales,
            "rondaNum": self.ronda_num,
            "minJugadores": MIN_JUGADORES,
            "maxJugadores": MAX_JUGADORES,
            "jugadores": [j.publico() for j in self.lista_jugadores()],
            "yo": ({"id": jug.id, "nombre": jug.nombre, "puntos": jug.puntos,
                    "racha": jug.racha} if jug else None),
        }

        if self.fase == FASE_PREGUNTA and self.ronda:
            r = self.ronda
            cerebro = self.jugadores.get(r["cerebro_id"]) if r["cerebro_id"] else None
            soy_cerebro = bool(cerebro and cerebro.id == pid)
            if r["tipo"] == TIPO_CEREBRO:
                if soy_cerebro:
                    titulo = "¿QUÉ ELEGIRÍAS?"
                else:
                    titulo = "¿QUÉ CREES QUE ELEGIRÁ %s?" % cerebro.nombre.upper()
            elif r["tipo"] == TIPO_COINCIDENCIA:
                titulo = "RESPONDE POR TI"
            else:
                titulo = "¿QUÉ PREFERIRÍAS?"
            # Solo se envía el número de respuestas, nunca quién falta.
            vista["ronda"] = {
                "tipo": r["tipo"],
                "titulo": titulo,
                "pregunta": r["pregunta"]["texto"],
                "opciones": r["pregunta"]["opciones"],
                "cerebro": ({"id": cerebro.id, "nombre": cerebro.nombre} if cerebro else None),
                "soyCerebro": soy_cerebro,
                "miRespuesta": r["respuestas"].get(pid),
                "respondidos": len(r["respuestas"]),
                "esperados": len(r["respuestas"]) + len(self._pendientes()),
                "segundos": max(0, int(round(r["limite"] - time.monotonic()))),
                "segundosTotal": SEGUNDOS_RESPUESTA,
            }
        elif self.fase == FASE_REVEAL and self.reveal:
            vista["reveal"] = self.reveal
        elif self.fase == FASE_FINAL and self.final:
            vista["final"] = self.final

        return vista

    # ------------------------------------------------------------------
    # Publicación a los clientes (SSE)
    # ------------------------------------------------------------------
    def suscribir(self, pid):
        q = queue.Queue(maxsize=64)
        self._suscriptores.append((pid, q))
        return q

    def desuscribir(self, pid, q):
        try:
            self._suscriptores.remove((pid, q))
        except ValueError:
            pass

    def publicar(self):
        self.version += 1
        for pid, q in list(self._suscriptores):
            try:
                q.put_nowait(self.vista_para(pid))
            except queue.Full:
                pass

    def hay_suscriptor(self, pid):
        return any(p == pid for p, _ in self._suscriptores)
