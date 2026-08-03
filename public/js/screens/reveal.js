// Reveal: qué eligió cada uno, quién acertó y la frase del día.

import { html, crudo, nodo, aviso, escalonar } from '../ui.js';

export function clave(p) {
  // El rol de host entra en la clave: si se traspasa a mitad del reveal,
  // el nuevo host tiene que ver aparecer su botón sin recargar nada.
  return 'reveal:' + (p.reveal ? p.reveal.ronda : 0) + ':' + (p.eresHost ? 'host' : 'no');
}

function opcionTexto(rev, idx) {
  if (idx == null || !rev.opciones[idx]) return 'sin respuesta';
  return rev.opciones[idx];
}

function filaResultado(rev, r, p) {
  const soyYo = p.yo && r.id === p.yo.id;
  const clases = ['resultado'];
  if (r.sin_respuesta) clases.push('ko');
  else if (r.acierto) clases.push('ok');
  else clases.push('ko');
  if (soyYo) clases.push('yo');

  let marca = '✗';
  if (r.sin_respuesta) marca = '⏳';
  else if (r.acierto) marca = '+' + (r.puntos + r.bonus) + ' ✓';

  return html`
    <div class="${clases.join(' ')}">
      <div class="cuerpo">
        <div class="quien">${r.nombre}${soyYo ? crudo(' <span class="tenue">(tú)</span>') : ''}</div>
        <div class="eligio">${opcionTexto(rev, r.respuesta)}</div>
      </div>
      <div style="text-align:right">
        <div class="marca">${marca}</div>
        ${r.bonus ? crudo('<div class="tenue" style="font-size:12px;font-weight:800">🔥 racha +' + r.bonus + '</div>') : ''}
      </div>
    </div>`;
}

function cuerpoCerebro(rev, p) {
  if (rev.anulada) {
    return html`
      <div class="tarjeta centro">
        <div style="font-size:40px">⌛</div>
        <div style="font-weight:800;margin-top:8px">RONDA ANULADA</div>
        <div class="tenue" style="margin-top:4px">Nadie puntúa esta vez.</div>
      </div>`;
  }
  const rachas = rev.resultados.filter(r => r.frase_racha).map(r => r.frase_racha);
  return html`
    <div class="eleccion">
      <div class="quien">${rev.cerebro.nombre} eligió</div>
      <div class="que">${opcionTexto(rev, rev.respuesta_cerebro)}</div>
    </div>
    <div class="resultados">
      ${rev.resultados.map(r => crudo(filaResultado(rev, r, p)))}
    </div>
    ${rachas.map(f => crudo('<div class="frase-racha">' + f + '</div>'))}`;
}

function cuerpoCoincidencia(rev, p) {
  return html`
    ${rev.etiqueta ? crudo('<div class="gran-etiqueta">' + rev.etiqueta + '</div>') : ''}
    <div class="pila">
      ${rev.grupos.map(g => crudo(html`
        <div class="grupo-coincidencia ${g.coincide ? 'match' : ''}">
          <div class="opt">${opcionTexto(rev, g.opcion)}</div>
          <div class="quienes">${g.jugadores.join(' · ')}${g.coincide ? ' · +50' : ''}</div>
        </div>`))}
    </div>`;
}

function cuerpoDilema(rev) {
  return html`
    <div class="pila">
      ${rev.reparto.map(d => crudo(html`
        <div class="barra-dilema" data-pct="${d.pct}">
          <div class="relleno"></div>
          <div class="contenido">
            <div class="pct">${d.pct}%</div>
            <div>
              <div class="txt">${opcionTexto(rev, d.opcion)}</div>
              <div class="quienes">${d.jugadores.length ? d.jugadores.join(' · ') : 'nadie'}</div>
            </div>
          </div>
        </div>`))}
    </div>`;
}

function bloqueRanking(rev) {
  if (!rev.ranking) return '';
  return html`
    <div>
      <div class="etiqueta" style="margin-bottom:8px">Clasificación</div>
      <div class="ranking">
        ${rev.ranking.map(r => crudo(html`
          <div class="fila-rank ${r.pos === 1 ? 'primero' : ''}">
            <span class="pos">${r.pos}</span>
            <span class="nombre">${r.nombre}</span>
            <span class="pts">${r.puntos}</span>
          </div>`))}
      </div>
    </div>`;
}

export function render(p, acciones) {
  const rev = p.reveal;
  let cuerpo;
  if (rev.tipo === 'cerebro') cuerpo = cuerpoCerebro(rev, p);
  else if (rev.tipo === 'coincidencia') cuerpo = cuerpoCoincidencia(rev, p);
  else cuerpo = cuerpoDilema(rev);

  const total = p.rondasTotales ? '/' + p.rondasTotales : '';
  const el = nodo(html`
    <div class="pantalla">
      <div class="cabecera">
        <div class="chip">RONDA ${rev.ronda}${crudo(total)}</div>
        <div class="chip lima">${p.yo ? p.yo.puntos : 0} pts</div>
      </div>

      <div class="crece pila-lg">
        <div class="texto-pregunta" style="font-size:19px;margin:0">${rev.pregunta}</div>
        ${crudo(cuerpo)}
        ${rev.frase ? crudo('<div class="frase">' + rev.frase + '</div>') : ''}
        ${rev.conversacion ? crudo('<div class="conversacion">' + rev.conversacion + '</div>') : ''}
        ${crudo(bloqueRanking(rev))}
      </div>

      <div class="pila" style="margin-top:18px">
        ${p.eresHost ? crudo(html`
          <button class="btn" id="siguiente">${rev.ultima ? 'VER RESULTADOS' : 'SIGUIENTE'}</button>
          ${!rev.ultima ? crudo('<button class="btn fantasma pequeno" id="terminar" style="width:100%">Terminar partida</button>') : ''}
        `) : crudo(`
          <div class="tarjeta centro">
            <div style="font-weight:800">Comentad la respuesta 👀</div>
            <div class="tenue" style="font-size:14px;margin-top:4px">El host pasa a la siguiente.</div>
          </div>`)}
      </div>
    </div>
  `);

  escalonar(el, '.resultado', 90);
  escalonar(el, '.grupo-coincidencia', 90);
  escalonar(el, '.barra-dilema', 90);

  requestAnimationFrame(() => {
    el.querySelectorAll('.barra-dilema').forEach(b => {
      b.querySelector('.relleno').style.width = (b.dataset.pct || 0) + '%';
    });
  });

  const siguiente = el.querySelector('#siguiente');
  if (siguiente) {
    siguiente.onclick = async () => {
      siguiente.disabled = true;
      try { await acciones.siguiente(); } catch (e) { aviso(e.message, 'error'); siguiente.disabled = false; }
    };
  }
  const terminar = el.querySelector('#terminar');
  if (terminar) {
    terminar.onclick = async () => {
      terminar.disabled = true;
      try { await acciones.terminar(); } catch (e) { aviso(e.message, 'error'); terminar.disabled = false; }
    };
  }
  return el;
}

export function actualizar(el, p) {
  const chip = el.querySelector('.chip.lima');
  if (chip && p.yo) chip.textContent = p.yo.puntos + ' pts';
}
