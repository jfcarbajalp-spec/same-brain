// Pantallas sin partida: inicio, crear y unirse.

import { html, nodo, aviso } from '../ui.js';
import { estado, irA } from '../store.js';

const CLAVE_NOMBRE = 'samebrain.nombre';

function nombreGuardado() {
  try { return localStorage.getItem(CLAVE_NOMBRE) || ''; } catch (e) { return ''; }
}

function guardarNombre(n) {
  try { localStorage.setItem(CLAVE_NOMBRE, n); } catch (e) { /* nada */ }
}

export function clave() {
  return 'home:' + estado.vista;
}

export function render(_, acciones) {
  if (estado.vista === 'crear') return pantallaNombre(acciones);
  if (estado.vista === 'unirse') return pantallaUnirse(acciones);
  return pantallaInicio();
}

function pantallaInicio() {
  const el = nodo(html`
    <div class="pantalla">
      <div class="crece" style="display:grid;place-items:center;padding:30px 0">
        <div class="centro">
          <div class="titulo-marca">Same<br>Brain 🧠</div>
          <p class="subtitulo">¿Qué tan bien conoces a los demás?</p>
        </div>
      </div>
      <div class="pila">
        <button class="btn" data-ir="crear">CREAR PARTIDA</button>
        <button class="btn violeta" data-ir="unirse">UNIRME A PARTIDA</button>
      </div>
      <div class="pie">2-10 jugadores · cada uno en su móvil · sin registro</div>
    </div>
  `);
  el.querySelectorAll('[data-ir]').forEach(b => {
    b.onclick = () => irA(b.dataset.ir);
  });
  return el;
}

function pantallaNombre(acciones) {
  const el = nodo(html`
    <div class="pantalla">
      <div class="cabecera">
        <button class="btn fantasma pequeno" data-volver>← Volver</button>
        <div class="chip">CREAR PARTIDA</div>
      </div>
      <div class="crece" style="display:grid;place-items:center">
        <div style="width:100%">
          <h2 style="font-size:30px;margin-bottom:6px">¿Cómo te llamas?</h2>
          <p class="tenue" style="margin:0 0 18px">Así te verán los demás.</p>
          <input class="campo" id="nombre" maxlength="14" placeholder="Tu nombre"
                 autocomplete="off" autocapitalize="words" value="${nombreGuardado()}">
        </div>
      </div>
      <button class="btn" id="ok">CREAR SALA</button>
    </div>
  `);

  const campo = el.querySelector('#nombre');
  const boton = el.querySelector('#ok');
  el.querySelector('[data-volver]').onclick = () => irA('inicio');

  const enviar = async () => {
    const nombre = campo.value.trim();
    if (!nombre) { campo.focus(); return aviso('Escribe tu nombre.', 'error'); }
    guardarNombre(nombre);
    boton.disabled = true;
    boton.textContent = 'CREANDO…';
    try {
      await acciones.crear(nombre);
    } catch (e) {
      aviso(e.message, 'error');
      boton.disabled = false;
      boton.textContent = 'CREAR SALA';
    }
  };
  boton.onclick = enviar;
  campo.onkeydown = e => { if (e.key === 'Enter') enviar(); };
  setTimeout(() => campo.focus(), 120);
  return el;
}

function pantallaUnirse(acciones) {
  const el = nodo(html`
    <div class="pantalla">
      <div class="cabecera">
        <button class="btn fantasma pequeno" data-volver>← Volver</button>
        <div class="chip">UNIRME</div>
      </div>
      <div class="crece pila-lg" style="padding-top:14px">
        <div>
          <div class="etiqueta" style="margin-bottom:8px">Código de sala</div>
          <input class="campo codigo" id="codigo" maxlength="4" placeholder="····"
                 autocomplete="off" autocapitalize="characters" autocorrect="off"
                 spellcheck="false" inputmode="text">
        </div>
        <div>
          <div class="etiqueta" style="margin-bottom:8px">Tu nombre</div>
          <input class="campo" id="nombre" maxlength="14" placeholder="Tu nombre"
                 autocomplete="off" autocapitalize="words" value="${nombreGuardado()}">
        </div>
      </div>
      <button class="btn violeta" id="ok">ENTRAR</button>
    </div>
  `);

  const codigo = el.querySelector('#codigo');
  const nombre = el.querySelector('#nombre');
  const boton = el.querySelector('#ok');
  el.querySelector('[data-volver]').onclick = () => irA('inicio');

  codigo.oninput = () => {
    codigo.value = codigo.value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 4);
    if (codigo.value.length === 4 && !nombre.value.trim()) nombre.focus();
  };

  const enviar = async () => {
    const c = codigo.value.trim().toUpperCase();
    const n = nombre.value.trim();
    if (c.length !== 4) { codigo.focus(); return aviso('El código tiene 4 caracteres.', 'error'); }
    if (!n) { nombre.focus(); return aviso('Escribe tu nombre.', 'error'); }
    guardarNombre(n);
    boton.disabled = true;
    boton.textContent = 'ENTRANDO…';
    try {
      await acciones.unirse(c, n);
    } catch (e) {
      aviso(e.message, 'error');
      boton.disabled = false;
      boton.textContent = 'ENTRAR';
    }
  };
  boton.onclick = enviar;
  nombre.onkeydown = e => { if (e.key === 'Enter') enviar(); };
  setTimeout(() => codigo.focus(), 120);
  return el;
}
