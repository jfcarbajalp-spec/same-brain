// Pantalla final: ganador, premios y mapa de conexiones.

import { html, crudo, nodo, aviso, escalonar } from '../ui.js';

export function clave(p) {
  return 'final:' + (p.eresHost ? 'host' : 'no');
}

function premio(icono, titulo, valor, detalle) {
  if (!valor) return '';
  return html`
    <div class="premio">
      <div class="ico">${icono}</div>
      <div>
        <div class="tit">${titulo}</div>
        <div class="val">${valor}</div>
        ${detalle ? crudo('<div class="det">' + detalle + '</div>') : ''}
      </div>
    </div>`;
}

export function render(p, acciones) {
  const f = p.final;
  const el = nodo(html`
    <div class="pantalla">
      <div class="cabecera">
        <div class="marca">SAME BRAIN RESULTS</div>
        <div class="chip">${f.rondas} rondas</div>
      </div>

      <div class="crece pila-lg">
        <div class="trofeo">
          <div class="icono">🏆</div>
          <div class="etiqueta">Ganador</div>
          <div class="nombre">${f.ganador.nombre}</div>
          <div class="pts">${f.ganador.puntos.toLocaleString('es-ES')} puntos</div>
        </div>

        <div class="pila">
          ${crudo(premio('🧠', 'Mejor lector de mentes',
            f.mejor_lector && f.mejor_lector.nombre,
            f.mejor_lector && (f.mejor_lector.aciertos + ' de ' + f.mejor_lector.intentos + ' predicciones')))}
          ${crudo(premio('🎭', 'Más impredecible',
            f.impredecible && f.impredecible.nombre,
            f.impredecible && ('solo acertaron el ' + f.impredecible.pct + '% de las veces')))}
          ${crudo(premio('👯', 'Same brain',
            f.same_brain && (f.same_brain.a + ' + ' + f.same_brain.b),
            f.same_brain && (f.same_brain.pct + '% de respuestas iguales')))}
          ${crudo(premio('🌪️', 'Polos opuestos',
            f.polo_opuesto && (f.polo_opuesto.a + ' + ' + f.polo_opuesto.b),
            f.polo_opuesto && ('solo el ' + f.polo_opuesto.pct + '% en común')))}
        </div>

        <div>
          <div class="etiqueta" style="margin-bottom:8px">Clasificación final</div>
          <div class="ranking">
            ${f.podio.map((j, i) => crudo(html`
              <div class="fila-rank ${i === 0 ? 'primero' : ''}">
                <span class="pos">${i + 1}</span>
                <span class="nombre">${j.nombre}</span>
                <span class="pts">${j.puntos}</span>
              </div>`))}
          </div>
        </div>

        ${f.conexiones.length ? crudo(html`
          <div>
            <div class="etiqueta" style="margin-bottom:8px">Conexiones</div>
            <div class="ranking">
              ${f.conexiones.map(c => crudo(html`
                <div class="conexion">
                  <span class="par">${c.a} ↔ ${c.b}</span>
                  <span class="medidor"><i style="width:${c.pct}%"></i></span>
                  <span class="pct">${c.pct}%</span>
                </div>`))}
            </div>
            <div class="tenue" style="font-size:12px;margin-top:8px;text-align:center">
              Solo mide cuántas veces respondisteis lo mismo.
            </div>
          </div>`) : ''}
      </div>

      <div class="pila" style="margin-top:18px">
        ${p.eresHost ? crudo('<button class="btn" id="revancha">REVANCHA</button>') : crudo(`
          <div class="tarjeta centro">
            <div style="font-weight:800">Si el host pide revancha, volvéis al lobby.</div>
          </div>`)}
        <button class="btn fantasma" id="salir">NUEVA PARTIDA</button>
      </div>
    </div>
  `);

  escalonar(el, '.premio', 90);

  const revancha = el.querySelector('#revancha');
  if (revancha) {
    revancha.onclick = async () => {
      revancha.disabled = true;
      try { await acciones.revancha(); } catch (e) { aviso(e.message, 'error'); revancha.disabled = false; }
    };
  }
  el.querySelector('#salir').onclick = () => acciones.salir();
  return el;
}
