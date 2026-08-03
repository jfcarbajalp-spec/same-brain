// Estado del cliente + sesión persistente (para sobrevivir a un F5).

const CLAVE = 'samebrain.sesion';

export const estado = {
  vista: 'inicio',     // inicio | crear | unirse  (mientras no hay partida)
  sesion: null,        // {codigo, playerId, token, nombre}
  partida: null,       // última proyección recibida del servidor
  conectado: false,
};

const oyentes = new Set();

export function suscribir(fn) {
  oyentes.add(fn);
  return () => oyentes.delete(fn);
}

export function notificar() {
  oyentes.forEach(fn => {
    try { fn(estado); } catch (e) { console.error(e); }
  });
}

export function irA(vista) {
  estado.vista = vista;
  notificar();
}

export function guardarSesion(sesion) {
  estado.sesion = sesion;
  try { localStorage.setItem(CLAVE, JSON.stringify(sesion)); } catch (e) { /* modo privado */ }
}

export function cargarSesion() {
  try {
    const bruto = localStorage.getItem(CLAVE);
    if (!bruto) return null;
    const s = JSON.parse(bruto);
    if (s && s.codigo && s.playerId && s.token) return s;
  } catch (e) { /* nada */ }
  return null;
}

export function olvidarSesion() {
  estado.sesion = null;
  estado.partida = null;
  try { localStorage.removeItem(CLAVE); } catch (e) { /* nada */ }
}

export function aplicarPartida(datos) {
  estado.partida = datos;
  notificar();
}

export function marcarConexion(ok) {
  if (estado.conectado === ok) return;
  estado.conectado = ok;
  notificar();
}
