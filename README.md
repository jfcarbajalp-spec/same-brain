# Same Brain 🧠

Juego social de predicción para 2-10 personas, cada una desde su propio móvil.
Todo en español, sin registro y sin instalar nada: solo Python.

---

## Cómo jugar

1. Doble clic en **`jugar.bat`** (o `python server.py` desde una terminal).
2. La consola muestra dos direcciones:

   ```
   En este equipo:    http://localhost:8080
   Desde los móviles: http://192.168.1.42:8080
   ```

3. Cada jugador abre esa segunda dirección en el navegador de su móvil,
   estando en la **misma wifi**.
4. Uno crea la partida y dicta el código de 4 letras. El resto entra con
   **UNIRME A PARTIDA**.
5. El host elige duración y pulsa **EMPEZAR PARTIDA**.

La primera vez, Windows preguntará por el firewall: hay que permitir el
acceso en **redes privadas**, o los móviles no llegarán al servidor.

---

## Cómo funciona una partida

Cada ronda elige automáticamente a un jugador como **EL CEREBRO**. Todos
reciben la misma pregunta, pero con instrucciones distintas:

- El cerebro ve **"¿QUÉ ELEGIRÍAS?"**
- El resto ve **"¿QUÉ CREES QUE ELEGIRÁ LUCÍA?"**

Cuando todos han respondido: cuenta atrás, reveal simultáneo y puntos.

| Situación                       | Puntos            |
|---------------------------------|-------------------|
| Predicción correcta             | +100              |
| Racha de 2 / 3 / 4 / 5+         | +25 / 50 / 75 / 100 |
| Coincidir en ronda Same Brain   | +50               |

Cada 5 rondas hay una **ronda de coincidencia** (todos responden por sí
mismos y puntúa quien coincida) y cada 7 un **dilema** binario con
porcentajes. La rotación del cerebro está equilibrada y nadie repite dos
veces seguidas.

Al final: ganador, mejor lector de mentes, más impredecible, la pareja
Same Brain, los polos opuestos y el mapa de conexiones entre todos.

---

## Arquitectura

Sin dependencias externas: **solo la biblioteca estándar de Python 3**.

```
server.py              HTTP + SSE + rutas de la API
sb/
  rooms.py             registro de salas y hilo de reloj
  game.py              motor: rondas, puntuación, rotación, afinidad y vistas
  phrases.py           copy contextual del reveal
  questions/           banco de 200 preguntas + mezclador anti-repetición
public/
  index.html
  css/styles.css
  js/app.js            arranque y enrutado de pantallas
  js/net.js            API + canal de eventos + reconexión
  js/store.js          estado del cliente y sesión persistente
  js/ui.js             plantillas, animaciones y avisos
  js/screens/          inicio · lobby · pregunta · reveal · final
```

**Tiempo real por SSE.** Cada jugador mantiene abierto un
`EventSource` contra `/api/eventos` y el servidor le empuja el estado
cuando cambia algo. Las acciones van por `POST /api/accion` con el
`playerId` y un token secreto. No hace falta WebSocket ni un servicio
externo.

**El servidor es la única fuente de verdad.** El cliente no recibe el
estado completo de la sala, sino la proyección que le corresponde
(`Sala.vista_para`). Antes del reveal, el payload de cada jugador
contiene únicamente `respondidos: 2` y su propia respuesta: las
respuestas ajenas no salen del proceso, así que no hay nada que espiar
inspeccionando el navegador.

**Presencia por latido.** El cliente hace ping cada 5 s. El servidor no
se fía de detectar sockets caídos (en Windows escribir en un socket
muerto no falla), así que da por ausente a quien lleva 16 s sin latir.
De ahí cuelgan tres cosas: dejar de esperar a quien se fue, traspasar el
rol de host si desaparece, y volver a marcar presente a quien regresa.

**Reconexión.** La sesión vive en `localStorage`. Si alguien recarga la
página o se le va la conexión, vuelve exactamente a la misma ronda con su
respuesta ya registrada.

---

## Comprobaciones

```bash
python pruebas.py
```

Ejercita el banco de preguntas, la mezcla anti-repetición, una partida
completa de 20 rondas, la tabla de puntos y rachas, la privacidad de las
respuestas, las desconexiones, el traspaso de host, las rondas anuladas,
coincidencias, dilemas y los límites de sala.

---

## Ajustes rápidos

En `sb/game.py`:

| Constante             | Qué hace                                          |
|-----------------------|---------------------------------------------------|
| `SEGUNDOS_RESPUESTA`  | tiempo para responder cada ronda (30)             |
| `MAX_JUGADORES`       | tope de la sala (10)                              |
| `GRACIA_HOST`         | espera antes de traspasar el host (20 s)          |
| `TIMEOUT_PRESENCIA`   | silencio tras el que se da a alguien por caído    |
| `tipo_de_ronda()`     | cada cuánto toca coincidencia (5) y dilema (7)    |

Para añadir preguntas, basta con editar los ficheros de
`sb/questions/`: son listas de `("texto", ["opción", ...])` y se cargan
solas.
