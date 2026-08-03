// Pantalla de pregunta: opciones grandes y espera sin revelar nada.

import { html, crudo, nodo, aviso, vibrar, escalonar } from '../ui.js';

const LETRAS = ['A', 'B', 'C', 'D', 'E'];

export function clave(p) {
  const r = p.ronda || {};
  return ['pregunta', p.rondaNum, r.miRespuesta == null ? 'abierta' : 'enviada'].join(':');
}

function cabeceraRonda(p) {
  const r = p.ronda;
  if (r.tipo === 'cerebro' && r.cerebro) {
    return html`
      <div class="cabecera-ronda">
        <div class="etiqueta">Esta ronda</div>
        <div class="cerebro-nombre">${r.cerebro.nombre} 🧠</div>
      </div>`;
  }
  if (r.tipo === 'coincidencia') {
    return html`
      <div class="cabecera-ronda">
        <div class="etiqueta">Ronda especial</div>
        <div class="cerebro-nombre">SAME BRAIN 🧠</div>
      </div>`;
  }
  return html`
    <div class="cabecera-ronda">
      <div class="etiqueta">Ronda especial</div>
      <div class="cerebro-nombre">DILEMA ⚖️</div>
    </div>`;
}

function bloqueOpciones(r) {
  return html`
    <div class="opciones ${r.tipo === 'dilema' ? 'dos' : ''}">
      ${r.opciones.map((texto, i) => crudo(html`
        <button class="opcion ${r.tipo === 'dilema' ? 'dilema' : ''}" data-op="${i}">
          <span class="letra">${LETRAS[i]}</span>
          <span class="txt">${texto}</span>
        </button>`))}
    </div>`;
}

function bloqueEspera(p) {
  const r = p.ronda;
  const puntos = [];
  for (let i = 0; i < r.esperados; i++) {
    puntos.push(crudo('<span class="punto ' + (i < r.respondidos ? 'on' : '') + '"></span>'));
  }
  return html`
    <div class="enviado">
      <div class="tic">✓</div>
      <div class="estado">RESPUESTA ENVIADA</div>
      <div class="tenue" style="margin-top:6px">Esperando al resto…</div>
      <div class="puntos-mini">${puntos}</div>
      <div class="contador-respuestas" id="contador">
        ${r.respondidos}/${r.esperados} jugadores respondieron
      </div>
    </div>`;
}

function pintarCuerpo(el, p, acciones) {
  const r = p.ronda;
  const cuerpo = el.querySelector('#cuerpo');
  if (r.miRespuesta == null) {
    cuerpo.innerHTML = bloqueOpciones(r);
    escalonar(cuerpo, '.opcion', 50);
    cuerpo.querySelectorAll('[data-op]').forEach(b => {
      b.onclick = async () => {
        cuerpo.querySelectorAll('.opcion').forEach(o => { o.disabled = true; });
        b.classList.add('elegida');
        vibrar(18);
        try {
          await acciones.responder(parseInt(b.dataset.op, 10));
        } catch (e) {
          aviso(e.message, 'error');
          cuerpo.querySelectorAll('.opcion').forEach(o => { o.disabled = false; });
          b.classList.remove('elegida');
        }
      };
    });
  } else {
    cuerpo.innerHTML = bloqueEspera(p);
  }
}

function arrancarReloj(el, p) {
  const barra = el.querySelector('.barra-tiempo');
  const relleno = barra.querySelector('i');
  const total = p.ronda.segundosTotal || 30;
  let restante = p.ronda.segundos;

  const pintar = () => {
    const pct = Math.max(0, Math.min(100, (restante / total) * 100));
    relleno.style.width = pct + '%';
    barra.classList.toggle('urgente', restante <= 5);
  };
  pintar();
  el.__temporizador = setInterval(() => {
    restante = Math.max(0, restante - 1);
    pintar();
  }, 1000);
  el.__sincronizar = seg => { restante = seg; pintar(); };
  el.__limpiar = () => clearInterval(el.__temporizador);
}

export function render(p, acciones) {
  const r = p.ronda;
  const total = p.rondasTotales ? '/' + p.rondasTotales : '';
  const el = nodo(html`
    <div class="pantalla">
      <div class="cabecera">
        <div class="chip">RONDA ${p.rondaNum}${crudo(total)}</div>
        <div class="chip lima">${p.yo ? p.yo.puntos : 0} pts</div>
      </div>
      <div class="barra-tiempo"><i style="width:100%"></i></div>
      ${crudo(cabeceraRonda(p))}
      <div class="instruccion">${r.titulo}</div>
      <div class="texto-pregunta">${r.pregunta}</div>
      <div id="cuerpo" class="crece"></div>
    </div>
  `);
  pintarCuerpo(el, p, acciones);
  arrancarReloj(el, p);
  return el;
}

export function actualizar(el, p) {
  const r = p.ronda;
  if (el.__sincronizar) el.__sincronizar(r.segundos);
  const contador = el.querySelector('#contador');
  if (contador) {
    contador.textContent = r.respondidos + '/' + r.esperados + ' jugadores respondieron';
    const puntos = el.querySelectorAll('.punto');
    puntos.forEach((pt, i) => pt.classList.toggle('on', i < r.respondidos));
  }
  const chip = el.querySelector('.chip.lima');
  if (chip && p.yo) chip.textContent = p.yo.puntos + ' pts';
}
