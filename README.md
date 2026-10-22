# Productos ganadores · Salud y Fitness (AutoDS)

Investigación de productos para dropshipping: se extrae el catálogo de Salud y Fitness de AutoDS, se filtra con los cuatro criterios de [`requi.txt`](requi.txt) y se genera un informe HTML interactivo con los ganadores y los productos en observación.

> **Mantén este repositorio privado.** Contiene proveedores, costos, precios recomendados y márgenes: información útil para la competencia.

## Contenido

| Ruta | Qué es |
|---|---|
| `requi.txt` | Encargo original con los cuatro criterios. |
| `data/raw_batch*.json` | Lotes extraídos con el conector de AutoDS (solo lectura). Se aplican en orden: un lote posterior sobrescribe los campos de uno anterior. |
| `data/evaluacion_cualitativa.json` | Criterios 1 y 2: evaluación de analista sobre título y descripción, con el motivo de cada decisión. |
| `filtrar_catalogo.py` | Consolida los lotes, calcula los criterios 3 y 4 y clasifica los productos. |
| `generar_informe.py` | Genera `informe_productos_ganadores.html` a partir del resultado del filtrado. |
| `data/catalogo_salud_fitness.json` | Salida: catálogo consolidado (productos, métricas y precios de la competencia). |
| `data/productos_filtrados.json` | Salida: top ganadores, en observación, descartados y excluidos. |
| `informe_productos_ganadores.html` | Salida: informe para abrir en el navegador. |

Lotes incluidos:

- `raw_batch1` a `raw_batch7`: extracción inicial (2026-10-19).
- `raw_batch8_refresco`: refresco de métricas de los 22 productos evaluados (2026-10-21).
- `raw_batch9_anclas`: refresco de los precios de la competencia (2026-10-21).

## Regenerar el informe

Requiere Python 3.11 o superior; no hay dependencias externas.

```bash
python filtrar_catalogo.py
python generar_informe.py
```

El HTML se abre con doble clic, pero necesita internet para cargar Tailwind, la fuente y las fotos de AliExpress.

## Criterios

| Criterio | Cómo se evalúa |
|---|---|
| 1. Solución | Juicio sobre título y descripción: ¿resuelve un dolor o problema físico concreto? |
| 2. Factor Wow | Juicio sobre título y descripción: ¿tiene un mecanismo demostrable en video y no es un commodity? |
| 3. Rentabilidad 3x | `precio recomendado >= (costo de la variante más barata en stock + envío) × 3`. El precio recomendado es la mediana de precios de la competencia del mismo tipo (Amazon / Shopify), contando una vez a cada vendedor. |
| 4. Validación | Al menos 50 pedidos, con stock y listado actualizado en los últimos 14 días. AutoDS no da pedidos por fecha, así que la recencia se aproxima con la última actualización del listado. |

Los umbrales están al principio de `filtrar_catalogo.py`. El margen neto descuenta solo la comisión de pago (2.9 % + $0.30), no publicidad ni devoluciones.

El criterio 3 decide si un producto es viable; no es la regla para fijar el precio de venta en la tienda.

## Refrescar los datos

La extracción se hace con el conector de AutoDS desde Claude: no hay script de descarga ni clave de API en este repositorio. Para refrescar:

1. Reconsulta los productos o los listados de la competencia en AutoDS.
2. Guarda un lote nuevo `data/raw_batchN_<descripcion>.json` con `"extraido": "AAAA-MM-DD"` y una lista `metricas` (productos) o `referencias_competencia_amazon` (competencia).
3. Si un producto desaparece de AutoDS, márcalo con `"is_deleted": true`. Si desaparece un listado de la competencia, márcalo con `"disponible": false`.
4. Vuelve a ejecutar los dos scripts.

Los costos y precios son una foto fechada: revisa el panel de AutoDS antes de aplicar cualquier precio en la tienda.
