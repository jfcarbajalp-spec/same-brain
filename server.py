# -*- coding: utf-8 -*-
"""Same Brain — servidor HTTP + SSE, solo biblioteca estándar de Python.

Uso:
    python server.py [puerto]

Después, cada jugador abre http://<IP-del-portatil>:<puerto> desde su móvil
estando en la misma red wifi.
"""

import json
import mimetypes
import os
import posixpath
import queue
import socket
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sb import game  # noqa: E402
from sb.questions import TOTAL_PREGUNTAS  # noqa: E402
from sb.rooms import REGISTRO, arrancar_reloj  # noqa: E402

RAIZ = os.path.dirname(os.path.abspath(__file__))
PUBLICO = os.path.join(RAIZ, "public")
HEARTBEAT = 10  # segundos entre pings del stream

ACCIONES_HOST = {"config", "empezar", "siguiente", "terminar", "revancha"}


class Error(Exception):
    def __init__(self, mensaje, codigo=400):
        Exception.__init__(self, mensaje)
        self.mensaje = mensaje
        self.codigo = codigo


def limpiar_nombre(nombre):
    nombre = (nombre or "").strip()
    nombre = " ".join(nombre.split())
    # Los nombres viajan dentro de frases que el cliente pinta como HTML,
    # así que aquí se quedan fuera los caracteres con significado en markup.
    nombre = "".join(c for c in nombre if c.isprintable() and c not in "<>&\"'`")
    if not nombre:
        raise Error("Escribe un nombre.")
    return nombre[:14]


def buscar_sala(datos, exigir_token=True):
    sala = REGISTRO.obtener(datos.get("codigo"))
    if sala is None:
        raise Error("Esa sala no existe.", 404)
    if not exigir_token:
        return sala, None
    jug = sala.jugador(datos.get("playerId"), datos.get("token"))
    if jug is None:
        raise Error("Sesión no válida. Vuelve a entrar.", 403)
    return sala, jug


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "SameBrain"

    # -- utilidades ----------------------------------------------------
    def log_message(self, formato, *args):
        if self.path.startswith("/api/eventos"):
            return
        sys.stderr.write("  %s\n" % (formato % args))

    def responder_json(self, datos, codigo=200):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    def leer_json(self):
        try:
            largo = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            largo = 0
        if largo <= 0 or largo > 64 * 1024:
            return {}
        try:
            return json.loads(self.rfile.read(largo).decode("utf-8"))
        except Exception:
            raise Error("Petición no válida.")

    # -- GET -----------------------------------------------------------
    def do_GET(self):
        partes = urlparse(self.path)
        ruta = unquote(partes.path)
        try:
            if ruta == "/api/eventos":
                return self.stream_eventos(parse_qs(partes.query))
            if ruta == "/api/salud":
                return self.responder_json({"ok": True, "preguntas": TOTAL_PREGUNTAS,
                                            "salas": len(REGISTRO.salas)})
            return self.servir_estatico(ruta)
        except Error as e:
            return self.responder_json({"error": e.mensaje}, e.codigo)
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception as e:  # pragma: no cover
            return self.responder_json({"error": "Error interno: %s" % e}, 500)

    def do_HEAD(self):
        # Algunos clientes (y las sondas de arranque) piden HEAD antes que GET.
        ruta = unquote(urlparse(self.path).path)
        if ruta.startswith("/api/"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self.servir_estatico(ruta, solo_cabeceras=True)

    def servir_estatico(self, ruta, solo_cabeceras=False):
        if ruta in ("/", ""):
            ruta = "/index.html"
        ruta = posixpath.normpath(ruta).lstrip("/")
        destino = os.path.normpath(os.path.join(PUBLICO, ruta))
        if not destino.startswith(PUBLICO) or not os.path.isfile(destino):
            self.send_error(404, "No encontrado")
            return
        tipo = mimetypes.guess_type(destino)[0] or "application/octet-stream"
        if tipo.startswith("text/") or tipo in ("application/javascript",):
            tipo += "; charset=utf-8"
        with open(destino, "rb") as f:
            cuerpo = f.read()
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        if not solo_cabeceras:
            self.wfile.write(cuerpo)

    # -- SSE -----------------------------------------------------------
    def stream_eventos(self, params):
        codigo = (params.get("codigo") or [""])[0]
        pid = (params.get("playerId") or [""])[0]
        token = (params.get("token") or [""])[0]
        sala = REGISTRO.obtener(codigo)
        if sala is None:
            raise Error("Esa sala ya no existe.", 404)
        jug = sala.jugador(pid, token)
        if jug is None:
            raise Error("Sesión no válida.", 403)

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-transform")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True

        with sala.lock:
            cola = sala.suscribir(pid)
            sala.marcar_conexion(pid, True)
            inicial = sala.vista_para(pid)
            sala.publicar()

        try:
            self._enviar_evento(inicial)
            while True:
                try:
                    vista = cola.get(timeout=HEARTBEAT)
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
                    continue
                self._enviar_evento(vista)
        except (BrokenPipeError, ConnectionResetError, OSError, ValueError):
            pass
        finally:
            with sala.lock:
                sala.desuscribir(pid, cola)
                if not sala.hay_suscriptor(pid):
                    sala.marcar_conexion(pid, False)
                sala.publicar()

    def _enviar_evento(self, vista):
        carga = json.dumps(vista, ensure_ascii=False)
        self.wfile.write(("data: %s\n\n" % carga).encode("utf-8"))
        self.wfile.flush()

    # -- POST ----------------------------------------------------------
    def do_POST(self):
        ruta = urlparse(self.path).path
        try:
            datos = self.leer_json()
            if ruta == "/api/crear":
                return self.responder_json(self.api_crear(datos))
            if ruta == "/api/unirse":
                return self.responder_json(self.api_unirse(datos))
            if ruta == "/api/estado":
                return self.responder_json(self.api_estado(datos))
            if ruta == "/api/ping":
                return self.responder_json(self.api_ping(datos))
            if ruta == "/api/accion":
                return self.responder_json(self.api_accion(datos))
            return self.responder_json({"error": "Ruta desconocida."}, 404)
        except Error as e:
            return self.responder_json({"error": e.mensaje}, e.codigo)
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception as e:  # pragma: no cover
            return self.responder_json({"error": "Error interno: %s" % e}, 500)

    def api_crear(self, datos):
        nombre = limpiar_nombre(datos.get("nombre"))
        sala = REGISTRO.crear()
        with sala.lock:
            jug = sala.añadir_jugador(nombre)
        return {"codigo": sala.codigo, "playerId": jug.id, "token": jug.token,
                "nombre": jug.nombre}

    def api_unirse(self, datos):
        nombre = limpiar_nombre(datos.get("nombre"))
        sala, _ = buscar_sala(datos, exigir_token=False)
        with sala.lock:
            if sala.fase not in (game.FASE_LOBBY, game.FASE_FINAL):
                # se permite entrar en marcha: jugará desde la ronda siguiente
                pass
            try:
                jug = sala.añadir_jugador(nombre)
            except ValueError as e:
                raise Error(str(e))
            sala.publicar()
        return {"codigo": sala.codigo, "playerId": jug.id, "token": jug.token,
                "nombre": jug.nombre}

    def api_estado(self, datos):
        sala, jug = buscar_sala(datos)
        with sala.lock:
            sala.marcar_conexion(jug.id, True)
            return {"estado": sala.vista_para(jug.id)}

    def api_ping(self, datos):
        """Latido del cliente: es la señal fiable de que sigue ahí."""
        sala, jug = buscar_sala(datos)
        with sala.lock:
            if sala.marcar_conexion(jug.id, True):
                sala.publicar()
        return {"ok": True}

    def api_accion(self, datos):
        sala, jug = buscar_sala(datos)
        accion = datos.get("accion")
        valor = datos.get("valor")
        with sala.lock:
            sala.marcar_conexion(jug.id, True)
            if accion in ACCIONES_HOST and jug.id != sala.host_id:
                raise Error("Solo el host puede hacer eso.", 403)

            if accion == "config":
                try:
                    sala.configurar(int(valor))
                except (TypeError, ValueError) as e:
                    raise Error(str(e) or "Duración no válida.")
            elif accion == "empezar":
                try:
                    sala.empezar()
                except ValueError as e:
                    raise Error(str(e))
            elif accion == "responder":
                if not isinstance(valor, int):
                    raise Error("Respuesta no válida.")
                sala.responder(jug.id, valor)
            elif accion == "siguiente":
                if sala.fase == game.FASE_REVEAL:
                    sala.siguiente_ronda()
            elif accion == "terminar":
                sala.terminar()
            elif accion == "revancha":
                sala.revancha()
            elif accion == "salir":
                sala.salir(jug.id)
            else:
                raise Error("Acción desconocida.")

            sala.publicar()
            vista = sala.vista_para(jug.id) if jug.id in sala.jugadores else {"fuera": True}
        return {"ok": True, "estado": vista}


def ip_local():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def main():
    # La consola de Windows suele venir en cp1252 y los emojis la rompen.
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    # En un hosting el puerto lo impone la plataforma por variable de entorno.
    alojado = bool(os.environ.get("PORT"))
    puerto = int(os.environ.get("PORT") or 8080)
    if len(sys.argv) > 1 and not alojado:
        try:
            puerto = int(sys.argv[1])
        except ValueError:
            pass

    arrancar_reloj()
    servidor = ThreadingHTTPServer(("0.0.0.0", puerto), Handler)
    servidor.daemon_threads = True

    print("")
    print("  SAME BRAIN 🧠  ·  %d preguntas cargadas" % TOTAL_PREGUNTAS)
    print("  " + "-" * 46)
    if alojado:
        print("  Servidor público escuchando en el puerto %d" % puerto)
    else:
        print("  En este equipo:    http://localhost:%d" % puerto)
        print("  Desde los móviles: http://%s:%d" % (ip_local(), puerto))
        print("")
        print("  (todos en la misma wifi; si Windows pregunta por el")
        print("   firewall, permite el acceso en redes privadas)")
        print("  Ctrl+C para parar.")
    print("")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n  Hasta luego.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
