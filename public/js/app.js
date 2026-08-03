// Arranque, acciones y enrutado entre pantallas.

import { api, conectar } from './net.js';
import {
  estado, suscribir, notificar, irA,
  guardarSesion, cargarSesion, olvidarSesion, aplicarPartida, marcarConexion,
} from './store.js';
import { montar, aviso, cuentaAtras } from './ui.js';

import * as home from './screens/home.js';
import * as lobby from './screens/lobby.js';
import * as question from './screens/question.js';
import * as reveal from './screens/reveal.js';
import * as final from './screens/final.js';

let conexion = null;
let nodoActual = null;
let claveActual = null;
let moduloActual = null;
let ultimaRondaRevelada = 0;
let animando = false;
let primerEstado = true;

// ---------------------------------------------------------------- acciones
const acciones = {
  async crear(nombre) {
    const r = await api('/api/crear', { nombre });
    iniciarSesion(r);
  },

  async unirse(codigo, nombre) {
    const r = await api('/api/unirse', { codigo, nombre });
    iniciarSesion(r);
  },

  async accion(nombre, valor) {
    if (!estado.sesion) return;
    const r = await api('/api/accion', Object.assign({}, estado.sesion, {
      accion: nombre, valor,
    }));
    if (r.estado && !r.estado.fuera) aplicarPartida(r.estado);
    return r;
  },

  responder(i) { return acciones.accion('responder', i); },
  config(rondas) { return acciones.accion('config', rondas); },
  empezar() { return acciones.accion('empezar'); },
  siguiente() { return acciones.accion('siguiente'); },
  terminar() { return acciones.accion('terminar'); },
  revancha() { return acciones.accion('revancha'); },

  async salir() {
    try { await acciones.accion('salir'); } catch (e) { /* da igual */ }
    cerrarTodo();
    irA('inicio');
  },
};

function cerrarTodo() {
  if (conexion) { conexion.cerrar(); conexion = null; }
  olvidarSesion();
  ultimaRondaRevelada = 0;
  claveActual = null;
  moduloActual = null;
}

function iniciarSesion(datos) {
  const sesion = {
    codigo: datos.codigo,
    playerId: datos.playerId,
    token: datos.token,
    nombre: datos.nombre,
  };
  guardarSesion(sesion);
  abrirCanal(sesion);
}

function abrirCanal(sesion) {
  if (conexion) conexion.cerrar();
  conexion = conectar(sesion, {
    onEstado: datos => aplicarPartida(datos),
    onConexion: ok => marcarConexion(ok),
    onFatal: e => {
      aviso(e.message || 'La sala ya no existe.', 'error');
      cerrarTodo();
      irA('inicio');
    },
  });
}

// ---------------------------------------------------------------- enrutado
function moduloPara(p) {
  if (!estado.sesion || !p) return home;
  if (p.fase === 'lobby') return lobby;
  if (p.fase === 'pregunta' && p.ronda) return question;
  if (p.fase === 'reveal' && p.reveal) return reveal;
  if (p.fase === 'final' && p.final) return final;
  return home;
}

function pintar() {
  if (animando) return;
  const p = estado.partida;
  const modulo = moduloPara(p);
  const datos = modulo === home ? null : p;
  const nuevaClave = modulo.clave(datos || {});

  if (modulo === moduloActual && nuevaClave === claveActual && nodoActual) {
    if (modulo.actualizar) modulo.actualizar(nodoActual, datos, acciones);
    return;
  }

  if (nodoActual && nodoActual.__limpiar) nodoActual.__limpiar();
  nodoActual = montar(modulo.render(datos, acciones));
  claveActual = nuevaClave;
  moduloActual = modulo;
}

// El 3·2·1 solo se lanza al entrar en un reveal nuevo, no al reconectar.
async function alCambiarEstado() {
  const p = estado.partida;
  if (p && p.fase === 'reveal' && p.reveal && p.reveal.ronda !== ultimaRondaRevelada) {
    const esNuevo = !primerEstado;
    ultimaRondaRevelada = p.reveal.ronda;
    if (esNuevo) {
      animando = true;
      await cuentaAtras();
      animando = false;
    }
  }
  primerEstado = false;
  pintar();
}

suscribir(() => { alCambiarEstado(); });

// ---------------------------------------------------------------- arranque
async function arrancar() {
  const sesion = cargarSesion();
  if (!sesion) {
    irA('inicio');
    return;
  }
  estado.sesion = sesion;
  try {
    const r = await api('/api/estado', sesion);
    aplicarPartida(r.estado);
    abrirCanal(sesion);
  } catch (e) {
    olvidarSesion();
    irA('inicio');
  }
}

window.addEventListener('beforeunload', () => {
  if (conexion) conexion.cerrar();
});

arrancar();
