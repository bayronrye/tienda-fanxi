"""Genera informe_productos_ganadores.html a partir de data/productos_filtrados.json.

Ejecutar despues de filtrar_catalogo.py. Los datos se incrustan en el HTML para que
el archivo se abra con doble clic (file://) sin servidor.
"""

import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ENTRADA = BASE / "data" / "productos_filtrados.json"
SALIDA = BASE / "informe_productos_ganadores.html"

PLANTILLA = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Productos ganadores · Salud y Fitness</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com/3.4.16"></script>
<script>
  tailwind.config = {
    darkMode: 'media',
    theme: { extend: { fontFamily: { sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'] } } },
  };
</script>
<style>
  details > summary { list-style: none; }
  details > summary::-webkit-details-marker { display: none; }
  details[open] > summary .chev { transform: rotate(90deg); }
</style>
</head>
<body class="bg-slate-50 font-sans text-slate-900 antialiased dark:bg-slate-950 dark:text-slate-100">
<div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-12 lg:px-8">

  <header>
    <p class="text-sm font-semibold text-emerald-700 dark:text-emerald-400">AutoDS · Salud y Fitness</p>
    <h1 class="mt-1 text-3xl font-bold tracking-tight sm:text-4xl">Informe de productos ganadores</h1>
    <p id="subtitulo" class="mt-3 max-w-3xl text-slate-600 dark:text-slate-400"></p>
    <dl id="resumen" class="mt-6 grid grid-cols-2 gap-3 lg:grid-cols-4"></dl>
  </header>

  <section aria-labelledby="t-criterios" class="mt-8 rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
    <h2 id="t-criterios" class="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Los 4 criterios</h2>
    <ol id="criterios" class="mt-3 grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-4"></ol>
  </section>

  <section aria-labelledby="t-top" class="mt-12">
    <h2 id="t-top" class="text-2xl font-bold tracking-tight">Top Ganadores</h2>
    <p class="mt-1 text-slate-600 dark:text-slate-400">Cumplen los 4 criterios. Ordenados de mejor a peor por margen neto y volumen de ventas.</p>
    <div id="grid-top" class="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3"></div>
  </section>

  <section aria-labelledby="t-obs" class="mt-14">
    <h2 id="t-obs" class="text-2xl font-bold tracking-tight">En Observación</h2>
    <p class="mt-1 text-slate-600 dark:text-slate-400">Cumplen 2 o 3 criterios. La etiqueta roja indica qué criterio les falta.</p>
    <div class="mt-5 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
      <div id="filtros" role="group" aria-label="Filtrar por criterio que falta" class="flex flex-wrap gap-2"></div>
      <div class="flex flex-col gap-2 sm:flex-row">
        <label class="sr-only" for="buscar">Buscar</label>
        <input id="buscar" type="search" placeholder="Buscar producto o proveedor"
          class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 dark:border-slate-700 dark:bg-slate-900 sm:w-64">
        <label class="sr-only" for="orden">Ordenar</label>
        <select id="orden" class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 dark:border-slate-700 dark:bg-slate-900">
          <option value="recomendado">Orden recomendado</option>
          <option value="margen">Mayor margen neto</option>
          <option value="pedidos">Más pedidos</option>
          <option value="costo">Menor costo</option>
        </select>
      </div>
    </div>
    <p id="contador" class="mt-3 text-sm text-slate-500 dark:text-slate-400" aria-live="polite"></p>
    <div id="grid-obs" class="mt-3 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3"></div>
    <p id="vacio" class="mt-3 hidden rounded-xl border border-dashed border-slate-300 p-8 text-center text-slate-500 dark:border-slate-700">Ningún producto coincide con el filtro.</p>
  </section>

  <section class="mt-14 space-y-4">
    <details class="rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <summary id="t-resto" class="flex cursor-pointer items-center justify-between gap-3 px-5 py-4 font-semibold"></summary>
      <div class="border-t border-slate-200 px-5 py-4 dark:border-slate-800">
        <div class="overflow-x-auto">
          <table class="w-full min-w-[36rem] text-left text-sm">
            <thead class="text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400">
              <tr><th class="py-2 pr-4 font-semibold">Producto</th><th class="py-2 pr-4 font-semibold">Criterios</th><th class="py-2 pr-4 font-semibold">Le falta</th><th class="py-2 pr-4 text-right font-semibold">Costo</th><th class="py-2 text-right font-semibold">Precio</th></tr>
            </thead>
            <tbody id="tabla-descartados"></tbody>
          </table>
        </div>
        <h3 class="mt-6 text-sm font-semibold">Excluidos por datos insuficientes</h3>
        <ul id="excluidos" class="mt-2 space-y-1.5 text-sm text-slate-600 dark:text-slate-400"></ul>
      </div>
    </details>

    <details class="rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <summary class="flex cursor-pointer items-center justify-between gap-3 px-5 py-4 font-semibold">Metodología y parámetros <span class="chev text-slate-400 transition-transform" aria-hidden="true">›</span></summary>
      <dl id="metodologia" class="space-y-3 border-t border-slate-200 px-5 py-4 text-sm dark:border-slate-800"></dl>
    </details>
  </section>

  <footer class="mt-10 border-t border-slate-200 pt-6 text-xs leading-relaxed text-slate-500 dark:border-slate-800 dark:text-slate-400">
    Solución y Factor Wow son evaluación de analista sobre título y descripción (<code>data/evaluacion_cualitativa.json</code>).
    Rentabilidad y Validación se calculan en <code>filtrar_catalogo.py</code>. El margen neto descuenta la comisión de pago, no publicidad ni devoluciones.
    Datos de AutoDS consultados en modo solo lectura.
  </footer>
</div>

<script id="datos" type="application/json">__DATOS__</script>
<script>
(() => {
  const D = JSON.parse(document.getElementById('datos').textContent);
  const P = D.parametros;

  const CRIT = [
    ['c1', 'Solución', 'Resuelve un dolor o problema físico evidente, según título y descripción.'],
    ['c2', 'Factor Wow', 'Ángulo novedoso que detiene el scroll; no es un producto genérico.'],
    ['c3', 'Rentabilidad 3x', `Precio recomendado ≥ (costo de la mejor variante + envío) × ${P.multiplicador_rentabilidad}.`],
    ['c4', 'Validación', `≥ ${P.min_pedidos} pedidos, con stock y listado actualizado hace ≤ ${P.max_dias_sin_actualizar} días.`],
  ];
  const NOMBRE = Object.fromEntries(CRIT.map(([k, n]) => [k, n]));
  const TIPOS = {
    neck_stretcher: 'Estirador cervical',
    ems_neck_massager: 'Masajeador EMS de cuello',
    posture_corrector: 'Corrector de postura',
    smart_posture: 'Corrector de postura inteligente',
    sleep_aid: 'Dispositivo para dormir',
    back_stretcher: 'Estirador lumbar',
    bunion_corrector: 'Corrector de juanetes',
    ems_foot_mat: 'Alfombrilla EMS para pies',
    eye_massager: 'Masajeador ocular',
    acupressure_mat: 'Esterilla de acupresión',
    knee_sleeve: 'Rodillera de compresión',
    foam_roller: 'Rodillo de espuma',
    scalp_massager: 'Masajeador capilar',
    nasal_dilator: 'Dilatador nasal magnético',
    plantar_splint: 'Férula para fascitis plantar',
    shapewear: 'Faja moldeadora',
  };

  const usd = (n) => '$' + Number(n).toFixed(2);
  const num = (n) => Number(n).toLocaleString('es-ES');
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const faltan = (p) => CRIT.map(([k]) => k).filter((k) => !p.criterios[k].cumple);
  const tipo = (p) => TIPOS[p.tipo] || p.tipo;
  const thumb = (url) => (/alicdn\.com/.test(url) ? `${url}_480x480.jpg` : url);
  const ROJO = 'text-red-600 dark:text-red-400';

  // Cabecera
  const evaluados = D.top_ganadores.length + D.en_observacion.length + D.descartados.length;
  document.getElementById('subtitulo').textContent =
    `Métricas de producto consultadas en AutoDS el ${P.fecha_extraccion}` +
    (P.fecha_anclas && P.fecha_anclas !== P.fecha_extraccion ? ` · precios de la competencia del ${P.fecha_anclas}` : '') +
    ' · región US · precios en USD. ' +
    `${evaluados} productos evaluados con los criterios de requi.txt.`;
  document.getElementById('resumen').innerHTML = [
    ['Evaluados', evaluados, 'text-slate-900 dark:text-white'],
    ['Top ganadores', D.resumen.top_ganadores, 'text-emerald-700 dark:text-emerald-400'],
    ['En observación', D.resumen.en_observacion, 'text-amber-700 dark:text-amber-400'],
    ['Descartados', `${D.resumen.descartados} <span class="text-base font-medium text-slate-500">+${D.resumen.excluidos} excluidos</span>`, 'text-slate-900 dark:text-white'],
  ].map(([label, valor, cls]) => `
    <div class="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <dt class="text-sm text-slate-500 dark:text-slate-400">${label}</dt>
      <dd class="mt-1 text-3xl font-bold tabular-nums ${cls}">${valor}</dd>
    </div>`).join('');
  document.getElementById('criterios').innerHTML = CRIT.map(([, n, d], i) => `
    <li class="flex gap-3">
      <span class="flex h-7 w-7 flex-none items-center justify-center rounded-full bg-emerald-600/10 text-sm font-bold text-emerald-700 dark:text-emerald-400">${i + 1}</span>
      <div><p class="font-semibold">${n}</p><p class="mt-0.5 text-slate-600 dark:text-slate-400">${d}</p></div>
    </li>`).join('');

  // Tarjeta de producto
  function metric(label, valor, nota, cls = '') {
    return `<div class="rounded-xl bg-slate-50 px-3 py-2.5 dark:bg-slate-800/60">
      <dt class="text-xs font-medium text-slate-500 dark:text-slate-400">${label}</dt>
      <dd class="mt-0.5 text-lg font-semibold tabular-nums ${cls}">${valor}</dd>
      <dd class="text-xs leading-snug text-slate-500 dark:text-slate-400">${nota}</dd>
    </div>`;
  }

  function card(p, rank) {
    const esTop = p.criterios_cumplidos === 4;
    const falta = faltan(p);
    const badge = esTop
      ? `<span class="rounded-full bg-emerald-600 px-2.5 py-1 text-xs font-semibold text-white shadow">#${rank} · 4/4 criterios</span>`
      : `<span class="rounded-full bg-white/95 px-2.5 py-1 text-xs font-semibold text-slate-900 shadow">${p.criterios_cumplidos}/4 criterios</span>`;
    const tags = falta.map((k) =>
      `<span class="inline-flex items-center rounded-md bg-red-600 px-2 py-0.5 text-xs font-semibold text-white">Falta: ${NOMBRE[k]}</span>`).join('');
    const chips = CRIT.map(([k, n]) => {
      const ok = p.criterios[k].cumple;
      const cls = ok
        ? 'bg-emerald-50 text-emerald-800 ring-emerald-600/20 dark:bg-emerald-500/10 dark:text-emerald-300 dark:ring-emerald-400/20'
        : 'bg-red-50 text-red-700 ring-red-600/20 dark:bg-red-500/10 dark:text-red-300 dark:ring-red-400/20';
      return `<li class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${cls}"><span aria-hidden="true">${ok ? '✓' : '✗'}</span>${n}<span class="sr-only">: ${ok ? 'cumple' : 'no cumple'}</span></li>`;
    }).join('');
    const motivos = CRIT.map(([k, n]) => {
      const ok = p.criterios[k].cumple;
      return `<li><span class="font-semibold ${ok ? 'text-emerald-700 dark:text-emerald-400' : ROJO}">${ok ? '✓' : '✗'} ${n}:</span> ${esc(p.criterios[k].motivo)}</li>`;
    }).join('');
    const competencia = p.ancla.listados.map((a) =>
      `<li class="flex justify-between gap-3"><span class="truncate" title="${esc(a.title)}">${esc(a.seller)}</span><span class="tabular-nums">${usd(a.price)}</span></li>`).join('');
    const enlace = (href, texto) =>
      `<a href="${esc(href)}" target="_blank" rel="noopener" class="font-medium text-emerald-700 underline-offset-2 hover:underline dark:text-emerald-400">${texto} ↗</a>`;
    const links = [p.url_proveedor && enlace(p.url_proveedor, 'Ver proveedor'), enlace(p.url_autods, 'Ver en AutoDS')].filter(Boolean).join('');
    const confianza = p.ancla.confianza === 'baja' ? ' · <span class="text-amber-700 dark:text-amber-400">confianza baja</span>' : '';
    const pedidos = p.pedidos == null
      ? 'Sin datos'
      : `${num(p.pedidos)} <span class="text-xs font-medium text-slate-500 dark:text-slate-400">pedidos</span>`;
    const reviews = (p.reviews ? `${num(p.reviews)} reviews` : 'Sin reviews') + (p.rating ? ` · ★ ${p.rating}` : '');

    return `<article class="flex flex-col overflow-hidden rounded-2xl border bg-white shadow-sm dark:bg-slate-900 ${esTop ? 'border-emerald-500 ring-1 ring-emerald-500/30' : 'border-slate-200 dark:border-slate-800'}">
      <div class="relative aspect-[4/3] bg-slate-100 dark:bg-slate-800">
        <img src="${esc(thumb(p.imagen))}" data-full="${esc(p.imagen)}" alt="${esc(tipo(p))}" loading="lazy" class="h-full w-full object-cover">
        <div class="absolute left-3 top-3">${badge}</div>
      </div>
      <div class="flex flex-1 flex-col gap-4 p-5">
        <div>
          <p class="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">${esc(tipo(p))}</p>
          <h3 class="mt-1 line-clamp-2 font-semibold leading-snug" title="${esc(p.titulo)}">${esc(p.titulo)}</h3>
          <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">${esc(p.proveedor)} · ${esc(p.sitio)}</p>
        </div>
        ${falta.length ? `<div class="flex flex-wrap gap-1.5">${tags}</div>` : ''}
        <dl class="grid grid-cols-2 gap-2.5">
          ${metric('Costo real', usd(p.costo_total), `Variante óptima ${usd(p.costo_variante)} + envío ${usd(p.envio)}`)}
          ${metric('Precio recomendado', usd(p.precio_recomendado), `Mediana de ${p.ancla.vendedores} competidores${confianza}`)}
          ${metric('Margen neto', usd(p.margen_neto), `${p.margen_pct}% tras comisión · ${p.multiplo}× el costo`, p.margen_neto >= 0 ? 'text-emerald-700 dark:text-emerald-400' : ROJO)}
          ${metric('Pruebas de venta', pedidos, reviews, p.pedidos == null ? 'text-slate-400 dark:text-slate-500' : '')}
          ${metric('Tiempo de envío', `${p.dias_envio} días`, `Desde almacén ${esc(p.almacen)}`)}
          ${metric('Mínimo para 3x', usd(p.umbral_3x), p.criterios.c3.cumple ? 'El precio lo supera' : 'El precio no llega', p.criterios.c3.cumple ? '' : ROJO)}
        </dl>
        <ul class="flex flex-wrap gap-1.5" aria-label="Criterios">${chips}</ul>
        <details class="mt-auto rounded-xl border border-slate-200 dark:border-slate-800">
          <summary class="flex cursor-pointer items-center justify-between px-3 py-2 text-sm font-medium">Ver análisis <span class="chev text-slate-400 transition-transform" aria-hidden="true">›</span></summary>
          <div class="space-y-4 border-t border-slate-200 px-3 py-3 text-sm dark:border-slate-800">
            <ul class="space-y-1.5 text-slate-700 dark:text-slate-300">${motivos}</ul>
            <div>
              <p class="font-semibold">Competencia usada como ancla</p>
              <ul class="mt-1 space-y-1 text-slate-600 dark:text-slate-400">${competencia}</ul>
            </div>
            <div class="flex flex-wrap gap-4">${links}</div>
          </div>
        </details>
      </div>
    </article>`;
  }

  function conFallback(root) {
    root.querySelectorAll('img[data-full]').forEach((img) => {
      img.addEventListener('error', () => {
        if (!img.dataset.intento) {
          img.dataset.intento = '1';
          img.src = img.dataset.full;
          return;
        }
        const aviso = document.createElement('div');
        aviso.className = 'flex h-full w-full items-center justify-center text-sm text-slate-400';
        aviso.textContent = 'Imagen no disponible';
        img.replaceWith(aviso);
      });
    });
  }

  // Sección A
  const gridTop = document.getElementById('grid-top');
  gridTop.innerHTML = D.top_ganadores.length
    ? D.top_ganadores.map((p, i) => card(p, i + 1)).join('')
    : '<p class="rounded-xl border border-dashed border-slate-300 p-8 text-center text-slate-500 sm:col-span-2 lg:col-span-3 dark:border-slate-700">Ningún producto cumple los 4 criterios.</p>';
  conFallback(gridTop);

  // Sección B
  const obs = D.en_observacion;
  const estado = { filtro: 'todos', orden: 'recomendado', q: '' };
  const ORDEN = {
    recomendado: (a, b) => b.criterios_cumplidos - a.criterios_cumplidos || b.score - a.score,
    margen: (a, b) => b.margen_neto - a.margen_neto,
    pedidos: (a, b) => (b.pedidos ?? -1) - (a.pedidos ?? -1),
    costo: (a, b) => a.costo_total - b.costo_total,
  };
  const gridObs = document.getElementById('grid-obs');
  const filtros = document.getElementById('filtros');
  const opciones = [['todos', 'Todos', obs.length]]
    .concat(CRIT.map(([k, n]) => [k, `Falta ${n}`, obs.filter((p) => !p.criterios[k].cumple).length]))
    .filter(([, , c]) => c > 0);

  function pintarFiltros() {
    filtros.innerHTML = opciones.map(([k, label, c]) => {
      const activo = estado.filtro === k;
      const cls = activo
        ? 'border-slate-900 bg-slate-900 text-white dark:border-white dark:bg-white dark:text-slate-900'
        : 'border-slate-300 bg-white text-slate-700 hover:border-slate-400 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300';
      return `<button type="button" data-filtro="${k}" aria-pressed="${activo}" class="rounded-full border px-3 py-1.5 text-sm font-medium transition-colors ${cls}">${label} <span class="tabular-nums opacity-70">${c}</span></button>`;
    }).join('');
  }

  function pintarObs() {
    const q = estado.q.trim().toLowerCase();
    const lista = obs
      .filter((p) => estado.filtro === 'todos' || !p.criterios[estado.filtro].cumple)
      .filter((p) => !q || `${p.titulo} ${p.proveedor} ${tipo(p)}`.toLowerCase().includes(q))
      .sort(ORDEN[estado.orden]);
    gridObs.innerHTML = lista.map((p) => card(p)).join('');
    conFallback(gridObs);
    document.getElementById('contador').textContent = `Mostrando ${lista.length} de ${obs.length}`;
    document.getElementById('vacio').classList.toggle('hidden', lista.length > 0);
  }

  filtros.addEventListener('click', (e) => {
    const boton = e.target.closest('button[data-filtro]');
    if (!boton) return;
    estado.filtro = boton.dataset.filtro;
    pintarFiltros();
    pintarObs();
  });
  document.getElementById('buscar').addEventListener('input', (e) => { estado.q = e.target.value; pintarObs(); });
  document.getElementById('orden').addEventListener('change', (e) => { estado.orden = e.target.value; pintarObs(); });
  pintarFiltros();
  pintarObs();

  // Descartados y excluidos
  document.getElementById('t-resto').innerHTML =
    `Descartados (${D.descartados.length}) y excluidos (${D.excluidos.length}) <span class="chev text-slate-400 transition-transform" aria-hidden="true">›</span>`;
  document.getElementById('tabla-descartados').innerHTML = D.descartados.map((p) => `
    <tr class="border-t border-slate-200 align-top dark:border-slate-800">
      <td class="py-2 pr-4"><p class="font-medium">${esc(tipo(p))}</p><p class="line-clamp-1 text-xs text-slate-500 dark:text-slate-400" title="${esc(p.titulo)}">${esc(p.titulo)}</p></td>
      <td class="py-2 pr-4 tabular-nums">${p.criterios_cumplidos}/4</td>
      <td class="py-2 pr-4"><div class="flex flex-wrap gap-1">${faltan(p).map((k) => `<span class="rounded bg-red-600/10 px-1.5 py-0.5 text-xs font-medium text-red-700 dark:text-red-400">${NOMBRE[k]}</span>`).join('')}</div></td>
      <td class="py-2 pr-4 text-right tabular-nums">${usd(p.costo_total)}</td>
      <td class="py-2 text-right tabular-nums">${usd(p.precio_recomendado)}</td>
    </tr>`).join('');
  document.getElementById('excluidos').innerHTML = D.excluidos.map((e) =>
    `<li><span class="font-medium text-slate-800 dark:text-slate-200">${esc(e.titulo.slice(0, 70))}</span> — ${esc(e.motivo)}</li>`).join('');

  // Metodología
  const ETIQUETAS = {
    c1_solucion: 'Solución', c2_factor_wow: 'Factor Wow', c3_rentabilidad: 'Rentabilidad 3x',
    c4_validacion: 'Validación', margen_neto: 'Margen neto', orden: 'Orden de los ganadores',
  };
  document.getElementById('metodologia').innerHTML =
    Object.entries(D.metodologia).map(([k, v]) =>
      `<div><dt class="font-semibold">${ETIQUETAS[k] || k}</dt><dd class="mt-0.5 text-slate-600 dark:text-slate-400">${esc(v)}</dd></div>`).join('') +
    `<div><dt class="font-semibold">Parámetros</dt><dd class="mt-0.5 text-slate-600 dark:text-slate-400">` +
    `Multiplicador ${P.multiplicador_rentabilidad}× · mínimo ${P.min_pedidos} pedidos · máximo ${P.max_dias_sin_actualizar} días sin actualizar · ` +
    `comisión ${esc(P.comision_pago)} · confianza alta con ≥ ${P.min_vendedores_ancla_confianza_alta} vendedores en el ancla</dd></div>`;
})();
</script>
</body>
</html>
"""


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    datos = json.loads(ENTRADA.read_text(encoding="utf-8"))
    incrustado = json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")
    SALIDA.write_text(PLANTILLA.replace("__DATOS__", incrustado), encoding="utf-8")

    r = datos["resumen"]
    print(f"Informe creado: {SALIDA}")
    print(f"Ábrelo en el navegador: {SALIDA.as_uri()}\n")
    print(f"Top ganadores: {r['top_ganadores']} · En observación: {r['en_observacion']} · "
          f"Descartados: {r['descartados']} · Excluidos: {r['excluidos']}")
    for i, p in enumerate(datos["top_ganadores"], 1):
        print(f"  #{i} {p['titulo'][:60]} — costo ${p['costo_total']:.2f}, precio ${p['precio_recomendado']:.2f}, "
              f"margen neto ${p['margen_neto']:.2f}, {p['pedidos']} pedidos, {p['dias_envio']} días de envío")


if __name__ == "__main__":
    main()
