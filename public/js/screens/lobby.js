// Sala de espera: código, jugadores, duración y arranque.

import { html, crudo, nodo, inicial, colorDe, aviso, escalonar } from '../ui.js';

const DURACIONES = [
  { valor: 10, titulo: 'RÁPIDA', detalle: '10 rondas' },
  { valor: 20, titulo: 'NORMAL', detalle: '20 rondas' },
  { valor: 30, titulo: 'LARGA', detalle: '30 rondas' },
  { valor: 0, titulo: 'INFINITO', detalle: 'hasta que digas basta' },
];

export function clave(p) {
  return 'lobby:' + p.codigo;
}

function firma(p) {
  return p.jugadores.map(j => j.id + j.conectado).join('|') + '#' + p.hostId +
    '#' + p.rondasTotales + '#' + p.eresHost;
}

function filaJugador(j, p) {
  const esHost = j.id === p.hostId;
  const soyYo = p.yo && j.id === p.yo.id;
  return html`
    <div class="jugador ${j.conectado ? '' : 'desconectado'}">
      <div class="avatar" style="background:${colorDe(j.id)}">${inicial(j.nombre)}</div>
      <div class="nombre">${j.nombre}${soyYo ? crudo(' <span class="tenue">(tú)</span>') : ''}</div>
      ${esHost ? crudo('<span class="insignia">HOST</span>') : ''}
      <span style="color:var(--lima);font-weight:900">${j.conectado ? '✓' : '…'}</span>
    </div>`;
}

function cuerpo(p) {
  // Solo cuentan los conectados: el servidor tampoco deja empezar sin ellos.
  const listos = p.jugadores.filter(j => j.conectado).length;
  const faltan = Math.max(0, p.minJugadores - listos);
  return html`
    <div class="pila-lg crece">
      <div class="codigo-sala">
        <div class="etiqueta">Código de sala</div>
        <div class="valor">${p.codigo}</div>
      </div>

      <div>
        <div class="etiqueta" style="margin-bottom:10px">
          Jugadores · ${listos}/${p.maxJugadores}
        </div>
        <div class="jugadores">
          ${p.jugadores.map(j => crudo(filaJugador(j, p)))}
        </div>
      </div>

      ${p.eresHost ? crudo(html`
        <div>
          <div class="etiqueta" style="margin-bottom:10px">Duración</div>
          <div class="opciones-duracion">
            ${DURACIONES.map(d => crudo(html`
              <button class="duracion ${p.rondasTotales === d.valor ? 'activa' : ''}" data-rondas="${d.valor}">
                ${d.titulo}<small>${d.detalle}</small>
              </button>`))}
          </div>
        </div>`) : ''}
    </div>

    ${p.eresHost ? crudo(html`
      <button class="btn" id="empezar" ${faltan ? crudo('disabled') : ''}>
        ${faltan ? 'FALTA ' + faltan + ' JUGADOR' + (faltan > 1 ? 'ES' : '') : 'EMPEZAR PARTIDA'}
      </button>`) : crudo(`
      <div class="tarjeta centro">
        <div style="font-weight:800">Esperando al host…</div>
        <div class="tenue" style="font-size:14px;margin-top:4px">En cuanto empiece, aparece la primera pregunta.</div>
      </div>`)}
  `;
}

function enlazar(el, p, acciones) {
  el.querySelectorAll('[data-rondas]').forEach(b => {
    b.onclick = () => acciones.config(parseInt(b.dataset.rondas, 10));
  });
  const empezar = el.querySelector('#empezar');
  if (empezar) {
    empezar.onclick = async () => {
      empezar.disabled = true;
      try { await acciones.empezar(); } catch (e) { aviso(e.message, 'error'); empezar.disabled = false; }
    };
  }
  const copiar = el.querySelector('#copiar');
  if (copiar) {
    copiar.onclick = async () => {
      const url = location.origin + '/';
      try {
        if (navigator.share) await navigator.share({ title: 'Same Brain', text: 'Entra con el código ' + p.codigo, url });
        else { await navigator.clipboard.writeText(p.codigo + ' · ' + url); aviso('Código copiado ✓'); }
      } catch (e) { /* cancelado */ }
    };
  }
  escalonar(el, '.jugador', 45);
}

export function render(p, acciones) {
  const el = nodo(html`
    <div class="pantalla">
      <div class="cabecera">
        <div class="marca">SAME BRAIN 🧠</div>
        <button class="btn fantasma pequeno" id="copiar">Compartir</button>
      </div>
      <div id="cuerpo" style="display:flex;flex-direction:column;flex:1;gap:16px"></div>
    </div>
  `);
  el.querySelector('#cuerpo').innerHTML = cuerpo(p);
  enlazar(el, p, acciones);
  el.dataset.firma = firma(p);
  return el;
}

export function actualizar(el, p, acciones) {
  if (el.dataset.firma === firma(p)) return;
  el.querySelector('#cuerpo').innerHTML = cuerpo(p);
  enlazar(el, p, acciones);
  el.dataset.firma = firma(p);
}
