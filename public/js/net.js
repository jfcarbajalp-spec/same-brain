// Comunicación con el servidor: POST para acciones, SSE para recibir estado.

export async function api(ruta, cuerpo) {
  const resp = await fetch(ruta, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cuerpo || {}),
  });
  let datos = {};
  try { datos = await resp.json(); } catch (e) { /* respuesta vacía */ }
  if (!resp.ok) {
    const error = new Error(datos.error || 'Algo ha fallado.');
    error.codigo = resp.status;
    throw error;
  }
  return datos;
}

/**
 * Mantiene abierto el canal de eventos y lo reabre solo si se cae.
 * Si la sesión deja de ser válida (sala caducada, token malo) avisa por onFatal.
 */
export function conectar(sesion, { onEstado, onConexion, onFatal }) {
  let fuente = null;
  let cerrado = false;
  let intentos = 0;
  let temporizador = null;

  // El servidor no puede fiarse de detectar la caída del socket, así que
  // le mandamos un latido corto mientras la pestaña siga viva.
  const latido = setInterval(() => {
    if (cerrado) return;
    api('/api/ping', sesion).catch(() => { /* ya lo verá el stream */ });
  }, 5000);

  const url = '/api/eventos?codigo=' + encodeURIComponent(sesion.codigo) +
    '&playerId=' + encodeURIComponent(sesion.playerId) +
    '&token=' + encodeURIComponent(sesion.token);

  function abrir() {
    if (cerrado) return;
    fuente = new EventSource(url);

    fuente.onopen = () => {
      intentos = 0;
      onConexion && onConexion(true);
    };

    fuente.onmessage = ev => {
      if (!ev.data) return;
      try { onEstado && onEstado(JSON.parse(ev.data)); } catch (e) { console.error(e); }
    };

    fuente.onerror = () => {
      onConexion && onConexion(false);
      if (cerrado) return;
      try { fuente.close(); } catch (e) { /* nada */ }
      fuente = null;
      reintentar();
    };
  }

  function reintentar() {
    if (cerrado || temporizador) return;
    intentos++;
    const espera = Math.min(800 * intentos, 5000);
    temporizador = setTimeout(async () => {
      temporizador = null;
      if (cerrado) return;
      try {
        // Comprobamos que la sesión sigue viva antes de reabrir el stream.
        const r = await api('/api/estado', sesion);
        if (r.estado) onEstado && onEstado(r.estado);
        abrir();
      } catch (e) {
        if (e.codigo === 403 || e.codigo === 404) {
          cerrado = true;
          onFatal && onFatal(e);
        } else {
          reintentar();
        }
      }
    }, espera);
  }

  // Al volver a la pestaña, forzamos comprobación inmediata.
  const alVolver = () => {
    if (document.visibilityState !== 'visible' || cerrado) return;
    api('/api/ping', sesion).catch(() => { /* el stream se encargará */ });
    if (!fuente) {
      clearTimeout(temporizador);
      temporizador = null;
      intentos = 0;
      reintentar();
    }
  };
  document.addEventListener('visibilitychange', alVolver);

  abrir();

  return {
    cerrar() {
      cerrado = true;
      clearInterval(latido);
      clearTimeout(temporizador);
      document.removeEventListener('visibilitychange', alVolver);
      if (fuente) { try { fuente.close(); } catch (e) { /* nada */ } }
      fuente = null;
    },
  };
}
