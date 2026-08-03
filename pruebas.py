# -*- coding: utf-8 -*-
"""Comprobaciones del motor sin navegador: python pruebas.py"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sb import game
from sb.questions import DILEMAS, NORMALES, TOTAL_PREGUNTAS, Baraja

fallos = []


def check(condicion, mensaje):
    if condicion:
        print("  ok   %s" % mensaje)
    else:
        print("  FALLO %s" % mensaje)
        fallos.append(mensaje)


print("\n[1] Banco de preguntas")
check(TOTAL_PREGUNTAS >= 200, "hay al menos 200 preguntas (%d)" % TOTAL_PREGUNTAS)
check(len(DILEMAS) >= 15, "hay dilemas binarios (%d)" % len(DILEMAS))
check(all(2 <= len(q["opciones"]) <= 4 for q in NORMALES + DILEMAS),
      "todas las preguntas tienen entre 2 y 4 opciones")
check(all(len(q["opciones"]) == 2 for q in DILEMAS), "los dilemas son binarios")
textos = [q["texto"] + "|" + "|".join(q["opciones"]) for q in NORMALES + DILEMAS]
check(len(set(textos)) == len(textos), "no hay preguntas duplicadas")
check(all(len(set(q["opciones"])) == len(q["opciones"]) for q in NORMALES),
      "no hay opciones repetidas dentro de una pregunta")

print("\n[2] Mezcla anti-repetición")
b = Baraja(semilla=7)
temas = [b.sacar_normal()["tema"] for _ in range(120)]
peor = 1
racha = 1
for i in range(1, len(temas)):
    racha = racha + 1 if temas[i] == temas[i - 1] else 1
    peor = max(peor, racha)
check(peor <= 2, "nunca más de 2 preguntas seguidas del mismo tema (máx %d)" % peor)
ids = [b.sacar_normal()["id"] for _ in range(len(NORMALES) - 120)]
check(len(set(ids)) == len(ids), "no se repiten preguntas dentro de la misma baraja")

print("\n[3] Partida completa de 20 rondas con 4 jugadores")
random.seed(1)
sala = game.Sala("TEST")
jugadores = [sala.añadir_jugador(n) for n in ["Jorge", "Lucia", "Marco", "Giulia"]]
check(sala.host_id == jugadores[0].id, "el creador es el host")
sala.configurar(20)
sala.empezar()

veces_cerebro = {}
consecutivos = []
ultimo = None
tipos = {"cerebro": 0, "coincidencia": 0, "dilema": 0}

for _ in range(20):
    if sala.fase == game.FASE_FINAL:
        break
    r = sala.ronda
    tipos[r["tipo"]] += 1
    if r["tipo"] == "cerebro":
        cid = r["cerebro_id"]
        veces_cerebro[cid] = veces_cerebro.get(cid, 0) + 1
        if cid == ultimo:
            consecutivos.append(cid)
        ultimo = cid
    n_op = len(r["pregunta"]["opciones"])
    for j in jugadores:
        sala.responder(j.id, random.randrange(n_op))
    check_fase = sala.fase == game.FASE_REVEAL
    if not check_fase:
        fallos.append("la ronda no pasó a reveal")
    sala.siguiente_ronda()

check(sala.fase == game.FASE_FINAL, "la partida termina sola tras 20 rondas")
check(tipos["coincidencia"] == 4, "4 rondas de coincidencia en 20 (%d)" % tipos["coincidencia"])
check(tipos["dilema"] == 2, "2 rondas de dilema en 20 (%d)" % tipos["dilema"])
check(not consecutivos, "nadie es cerebro dos veces seguidas")
reparto = sorted(veces_cerebro.values())
check(max(reparto) - min(reparto) <= 1,
      "rotación equilibrada de cerebros %s" % reparto)

f = sala.final
check(f["ganador"] is not None, "hay ganador")
check(f["mejor_lector"] is not None, "hay mejor lector de mentes")
check(f["impredecible"] is not None, "hay jugador más impredecible")
check(f["impredecible"]["pct"] < 100, "el impredecible no es alguien a quien siempre acertaron")

print("\n[3b] Premios sin contraste")
sc = game.Sala("CLON")
clones = [sc.añadir_jugador(n) for n in ["A", "B", "C"]]
sc.configurar(10)
sc.empezar()
for _ in range(4):
    for j in clones:
        sc.responder(j.id, 0)   # todos responden siempre lo mismo
    sc.siguiente_ronda()
sc.terminar()
check(sc.final["impredecible"] is None, "sin impredecible si a todos se les adivina siempre")
check(sc.final["polo_opuesto"] is None, "sin polo opuesto si todos coinciden igual")
check(sc.final["same_brain"] is not None, "sí hay pareja same brain")
check(len(f["conexiones"]) == 6, "6 parejas de afinidad con 4 jugadores")
check(all(0 <= c["pct"] <= 100 for c in f["conexiones"]), "afinidad entre 0 y 100")
check(sum(j.puntos for j in jugadores) > 0, "se han repartido puntos")

print("\n[4] Puntuación y rachas")
random.seed(2)
s = game.Sala("PTS")
a = s.añadir_jugador("A")
bj = s.añadir_jugador("B")
s.configurar(0)
s.empezar()
# Forzamos ronda de cerebro con A de cerebro.
s.ronda["tipo"] = "cerebro"
s.ronda["cerebro_id"] = a.id
s.responder(a.id, 0)
s.responder(bj.id, 0)
check(bj.puntos == 100, "acierto simple = 100 puntos (%d)" % bj.puntos)
esperado = [100, 225, 375, 550, 750]
for i, total in enumerate(esperado[1:], start=2):
    s.siguiente_ronda()
    s.ronda["tipo"] = "cerebro"
    s.ronda["cerebro_id"] = a.id
    s.responder(a.id, 0)
    s.responder(bj.id, 0)
    check(bj.puntos == total, "racha x%d acumula %d puntos (%d)" % (i, total, bj.puntos))
check(bj.racha == 5, "la racha llega a 5")
s.siguiente_ronda()
s.ronda["tipo"] = "cerebro"
s.ronda["cerebro_id"] = a.id
s.responder(a.id, 0)
s.responder(bj.id, 1)
check(bj.racha == 0, "el fallo rompe la racha")

print("\n[5] Privacidad antes del reveal")
random.seed(3)
s = game.Sala("PRIV")
p1 = s.añadir_jugador("Uno")
p2 = s.añadir_jugador("Dos")
p3 = s.añadir_jugador("Tres")
s.configurar(10)
s.empezar()
s.ronda["tipo"] = "cerebro"
s.ronda["cerebro_id"] = p1.id
s.responder(p1.id, 2)
s.responder(p2.id, 3)
vista = s.vista_para(p3.id)
crudo = repr(vista)
check("reveal" not in vista, "sin bloque reveal mientras se responde")
check(vista["ronda"]["miRespuesta"] is None, "no ve respuesta propia inexistente")
check(vista["ronda"]["respondidos"] == 2, "solo ve el contador de respuestas")
check("respuestas" not in crudo, "la vista no contiene el diccionario de respuestas")
v2 = s.vista_para(p2.id)
check(v2["ronda"]["miRespuesta"] == 3, "cada uno ve solo su propia respuesta")
check(all(("respuesta" not in j) for j in vista["jugadores"]),
      "la lista de jugadores no lleva respuestas")
s.responder(p3.id, 2)
check(s.fase == game.FASE_REVEAL, "al responder el último se dispara el reveal")
rev = s.vista_para(p2.id)["reveal"]
check(rev["respuesta_cerebro"] == 2, "tras el reveal sí se ve la respuesta del cerebro")

print("\n[6] Desconexiones y host")
random.seed(4)
s = game.Sala("NET")
h = s.añadir_jugador("Host")
o = s.añadir_jugador("Otro")
s.configurar(10)
s.empezar()
s.marcar_conexion(h.id, False)
h.visto -= 100  # simulamos que pasó la gracia
check(s.host_caido_desde is not None, "se registra la caída del host")
s.host_caido_desde -= game.GRACIA_HOST + 1
s.comprobar_tiempo()
check(s.host_id == o.id, "el rol de host se traspasa solo")
check(s.fase == game.FASE_PREGUNTA, "la ronda sigue abierta si falta alguien conectado")
check(h.id not in s._pendientes(), "ya no se espera al jugador desconectado")
s.responder(o.id, 0)
check(s.fase == game.FASE_REVEAL, "responde el último conectado y se revela sin esperar al caído")

sp = game.Sala("PRES")
ph = sp.añadir_jugador("Host")
po = sp.añadir_jugador("Otro")
sp.configurar(10)
sp.empezar()
po.visto -= game.TIMEOUT_PRESENCIA + 1   # deja de dar señales de vida
check(sp.barrer_presencia() is True, "el barrido detecta a quien deja de latir")
check(po.conectado is False, "el jugador silencioso pasa a desconectado")
sp.marcar_conexion(po.id, True)
check(po.conectado is True, "un latido lo devuelve a conectado")
check(sp.marcar_conexion(po.id, True) is False, "latir estando conectado no cambia nada")

s2 = game.Sala("OUT")
x = s2.añadir_jugador("X")
y = s2.añadir_jugador("Y")
s2.salir(x.id)
check(s2.host_id == y.id, "si el host se va, el host pasa al siguiente")

print("\n[7] Ronda anulada si el cerebro no responde")
random.seed(5)
s = game.Sala("NULA")
c = s.añadir_jugador("Cerebro")
d = s.añadir_jugador("Otro")
s.configurar(10)
s.empezar()
s.ronda["tipo"] = "cerebro"
s.ronda["cerebro_id"] = c.id
s.responder(d.id, 0)
s.ronda["limite"] = 0
s.comprobar_tiempo()
check(s.fase == game.FASE_REVEAL, "el tiempo agotado fuerza el reveal")
check(s.reveal["anulada"] is True, "la ronda queda anulada")
check(d.puntos == 0, "nadie puntúa en ronda anulada")

print("\n[8] Coincidencias y dilemas")
random.seed(6)
s = game.Sala("COIN")
js = [s.añadir_jugador(n) for n in ["A", "B", "C", "D"]]
s.configurar(10)
s.empezar()
s.ronda["tipo"] = "coincidencia"
s.ronda["cerebro_id"] = None
for j, op in zip(js, [0, 0, 1, 2]):
    s.responder(j.id, op)
rev = s.reveal
check(js[0].puntos == 50 and js[1].puntos == 50, "coincidencia da 50 puntos a cada uno")
check(js[2].puntos == 0, "quien no coincide no puntúa")
check(rev["etiqueta"] == "🧠 SAME BRAIN", "etiqueta de pareja correcta")

s.siguiente_ronda()
s.ronda["tipo"] = "coincidencia"
for j in js:
    s.responder(j.id, 1)
check(s.reveal["etiqueta"] == "HIVE MIND", "todos iguales = HIVE MIND")

s.siguiente_ronda()
s.ronda["tipo"] = "dilema"
s.ronda["pregunta"] = {"texto": "x", "opciones": ["A", "B"], "tema": "dilemas", "id": "z"}
for j, op in zip(js, [0, 0, 1, 0]):
    s.responder(j.id, op)
pcts = [d["pct"] for d in s.reveal["reparto"]]
check(pcts == [75, 25], "porcentajes del dilema correctos %s" % pcts)

print("\n[9] Límites de sala")
s = game.Sala("LIM")
for i in range(game.MAX_JUGADORES):
    s.añadir_jugador("J%d" % i)
try:
    s.añadir_jugador("Sobra")
    check(False, "rechaza al jugador 11")
except ValueError:
    check(True, "rechaza al jugador 11")
s2 = game.Sala("MIN")
s2.añadir_jugador("Solo")
try:
    s2.empezar()
    check(False, "no deja empezar con 1 jugador")
except ValueError:
    check(True, "no deja empezar con 1 jugador")
s3 = game.Sala("DUP")
s3.añadir_jugador("Ana")
segundo = s3.añadir_jugador("Ana")
check(segundo.nombre == "Ana 2", "los nombres repetidos se diferencian")

print("")
if fallos:
    print("  %d fallo(s):" % len(fallos))
    for f_ in fallos:
        print("   - %s" % f_)
    sys.exit(1)
print("  Todo correcto ✓")
