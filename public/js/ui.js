// Utilidades de render y micro-animaciones.

const app = document.getElementById('app');
const capa = document.getElementById('capa');
const avisos = document.getElementById('avisos');

export function escapar(valor) {
  return String(valor == null ? '' : valor)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// Plantilla que escapa todo lo interpolado salvo lo marcado con crudo().
export function html(cadenas, ...valores) {
  return cadenas.reduce((acc, trozo, i) => {
    const v = valores[i - 1];
    let texto;
    if (v == null || v === false) texto = '';
    else if (v && v.__crudo) texto = v.valor;
    else if (Array.isArray(v)) texto = v.map(x => (x && x.__crudo ? x.valor : escapar(x))).join('');
    else texto = escapar(v);
    return acc + texto + trozo;
  });
}

export function crudo(valor) {
  return { __crudo: true, valor: valor == null ? '' : String(valor) };
}

export function nodo(cadena) {
  const cont = document.createElement('div');
  cont.innerHTML = cadena.trim();
  return cont.firstElementChild;
}

export function montar(elemento) {
  app.replaceChildren(elemento);
  return elemento;
}

export function inicial(nombre) {
  return (nombre || '?').trim().charAt(0).toUpperCase();
}

const COLORES = ['#c6ff3d', '#8b5cff', '#ff4d8d', '#ffc44d', '#4de1ff', '#7CFFB2', '#ff8a4d', '#d78bff', '#9be8ff', '#ffe066'];

export function colorDe(id) {
  let suma = 0;
  const texto = String(id || '');
  for (let i = 0; i < texto.length; i++) suma = (suma * 31 + texto.charCodeAt(i)) % 100000;
  return COLORES[suma % COLORES.length];
}

export function aviso(mensaje, tipo) {
  const el = nodo(html`<div class="aviso ${tipo === 'error' ? 'error' : ''}">${mensaje}</div>`);
  avisos.appendChild(el);
  setTimeout(() => {
    el.style.transition = 'opacity .3s, transform .3s';
    el.style.opacity = '0';
    el.style.transform = 'translateY(8px)';
    setTimeout(() => el.remove(), 320);
  }, 3200);
}

// Cuenta atrás 3 · 2 · 1 · REVEAL sobre una capa a pantalla completa.
export function cuentaAtras() {
  return new Promise(resolve => {
    const pasos = ['3', '2', '1', 'REVEAL'];
    let i = 0;
    capa.classList.add('visible');
    const mostrar = () => {
      if (i >= pasos.length) {
        capa.classList.remove('visible');
        capa.replaceChildren();
        resolve();
        return;
      }
      const esUltimo = i === pasos.length - 1;
      capa.replaceChildren(nodo(html`<div class="cuenta ${esUltimo ? 'reveal' : ''}">${pasos[i]}</div>`));
      vibrar(esUltimo ? 40 : 12);
      i++;
      setTimeout(mostrar, esUltimo ? 620 : 560);
    };
    mostrar();
  });
}

export function vibrar(ms) {
  if (navigator.vibrate) {
    try { navigator.vibrate(ms); } catch (e) { /* da igual */ }
  }
}

export function retraso(elemento, ms) {
  elemento.style.animationDelay = ms + 'ms';
  return elemento;
}

export function escalonar(contenedor, selector, paso = 55) {
  contenedor.querySelectorAll(selector).forEach((el, i) => retraso(el, i * paso));
}
