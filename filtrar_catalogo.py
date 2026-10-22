"""Consolida la extraccion de AutoDS y aplica los 4 criterios de requi.txt.

Entradas (data/):
  raw_batch*.json              lotes extraidos con el conector AutoDS (MCP, solo lectura)
  evaluacion_cualitativa.json  criterios 1 y 2, evaluados sobre titulo y descripcion

Salidas (data/):
  catalogo_salud_fitness.json  productos consolidados + anclas de competencia
  productos_filtrados.json     top_ganadores / en_observacion / descartados / excluidos
"""

import json
import math
import statistics
import sys
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"

MULTIPLICADOR = 3              # criterio 3: precio >= (costo + envio) * 3
MIN_PEDIDOS = 50               # criterio 4: volumen de ventas activo
MAX_DIAS_SIN_ACTUALIZAR = 14   # criterio 4: listado vivo, pedidos al dia
COMISION_PCT = 0.029           # pasarela de pago, solo para el margen neto
COMISION_FIJA = 0.30
MIN_VENDEDORES_CONFIANZA = 3

CRITERIOS = {
    "c1": "Solución",
    "c2": "Factor Wow",
    "c3": "Rentabilidad 3x",
    "c4": "Validación",
}


def r2(valor):
    return float(Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def cargar_lotes():
    """Lee los lotes en orden: un lote posterior (p. ej. un refresco) sobrescribe los campos de uno anterior."""
    productos, anclas, vendedores = {}, {}, {}
    fechas_metricas, fechas_anclas = [], []
    for ruta in sorted(DATA.glob("raw_batch*.json")):
        lote = json.loads(ruta.read_text(encoding="utf-8"))
        registros = lote.get("productos", []) + lote.get("metricas", [])
        if registros:
            fechas_metricas.append(lote["extraido"])
        for registro in registros:
            producto = productos.setdefault(registro["id"], {"lotes": []})
            producto.update(registro)
            producto["lotes"].append(ruta.name)
        if lote.get("referencias_competencia_amazon"):
            fechas_anclas.append(lote["extraido"])
        for ancla in lote.get("referencias_competencia_amazon", []):
            anclas[ancla["id"]] = ancla
        vendedores.update(lote.get("vendedor_por_ancla", {}))
    return productos, anclas, vendedores, max(fechas_metricas), max(fechas_anclas)


def anclas_por_tipo(anclas, vendedores):
    por_tipo = {}
    for ancla in anclas.values():
        if ancla.get("disponible") is False:
            continue
        seller = ancla.get("seller") or vendedores.get(ancla["id"]) or ancla["id"]
        por_tipo.setdefault(ancla["tipo"], []).append(
            {"id": ancla["id"], "seller": seller, "title": ancla["title"], "price": ancla["price"]}
        )
    return por_tipo


def precio_ancla(anclas):
    """Mediana entre vendedores: cada vendedor cuenta una vez, con la mediana de sus listados."""
    por_vendedor = {}
    for ancla in anclas:
        por_vendedor.setdefault(ancla["seller"], []).append(ancla["price"])
    medianas = [statistics.median(precios) for precios in por_vendedor.values()]
    return r2(statistics.median(medianas)), len(medianas)


def url_proveedor(producto):
    if producto.get("site") == "aliexpress":
        return f"https://www.aliexpress.us/item/{producto['id_on_site']}.html"
    return None


def evaluar(producto, cualitativa, anclas, corte):
    costo = producto.get("best_variant_cost", producto.get("min_price"))
    envio = producto.get("best_variant_ship", producto.get("ship_cost", 0))
    costo_total = r2(costo + envio)
    precio, vendedores = precio_ancla(anclas)
    umbral = r2(costo_total * MULTIPLICADOR)
    comision = r2(precio * COMISION_PCT + COMISION_FIJA)
    margen_neto = r2(precio - costo_total - comision)

    pedidos = producto.get("orders_count") or 0
    reviews = producto.get("rating_count") or 0
    stock = producto.get("stock") or 0
    dias = max(0, (corte - datetime.fromisoformat(producto["updated_at"])).days)

    c3 = precio >= umbral
    c4 = pedidos >= MIN_PEDIDOS and stock > 0 and dias <= MAX_DIAS_SIN_ACTUALIZAR
    criterios = {
        "c1": {"cumple": cualitativa["c1"], "motivo": cualitativa["c1_motivo"]},
        "c2": {"cumple": cualitativa["c2"], "motivo": cualitativa["c2_motivo"]},
        "c3": {
            "cumple": c3,
            "motivo": f"Precio ${precio:.2f} {'>=' if c3 else '<'} 3 x (${costo:.2f} + ${envio:.2f}) = ${umbral:.2f}",
        },
        "c4": {
            "cumple": c4,
            "motivo": f"{pedidos} pedidos (mínimo {MIN_PEDIDOS}), {reviews} reviews, stock {stock}, "
                      f"listado actualizado hace {dias} días (máximo {MAX_DIAS_SIN_ACTUALIZAR})",
        },
    }
    return {
        "id": producto["id"],
        "titulo": producto["title"],
        "tipo": cualitativa["tipo"],
        "proveedor": producto.get("supplier"),
        "sitio": producto.get("site"),
        "url_proveedor": url_proveedor(producto),
        "url_autods": f"https://platform.autods.com/marketplace/all-products/{producto['id']}",
        "imagen": producto.get("img"),
        "costo_variante": costo,
        "envio": envio,
        "costo_total": costo_total,
        "dias_envio": producto.get("ship_days", producto.get("ship_max")),
        "almacen": producto.get("warehouse"),
        "precio_recomendado": precio,
        "ancla": {
            "metodo": "mediana por vendedor de la competencia (Amazon / Shopify)",
            "vendedores": vendedores,
            "confianza": "alta" if vendedores >= MIN_VENDEDORES_CONFIANZA else "baja",
            "listados": anclas,
        },
        "umbral_3x": umbral,
        "multiplo": r2(precio / costo_total),
        "comision_pago": comision,
        "margen_neto": margen_neto,
        "margen_pct": r2(margen_neto / precio * 100),
        "pedidos": producto.get("orders_count"),
        "reviews": producto.get("rating_count"),
        "rating": producto.get("rating"),
        "stock": stock,
        "dias_desde_actualizacion": dias,
        "criterios": criterios,
        "criterios_cumplidos": sum(c["cumple"] for c in criterios.values()),
        "faltantes": [CRITERIOS[k] for k, c in criterios.items() if not c["cumple"]],
        # Ranking: margen por venta ponderado por demanda en escala logaritmica.
        "score": r2(margen_neto * math.log10(pedidos + 10)),
    }


def guardar(nombre, contenido):
    (DATA / nombre).write_text(json.dumps(contenido, ensure_ascii=False, indent=2), encoding="utf-8")


def imprimir_resumen(top, observacion, descartados, excluidos):
    print(f"\nProductos evaluados: {len(top) + len(observacion) + len(descartados)} "
          f"(+{len(excluidos)} excluidos por datos insuficientes)\n")
    print(f"TOP GANADORES (4/4): {len(top)}")
    for r in top:
        print(f"  {r['titulo'][:58]:<58} costo ${r['costo_total']:>6.2f}  precio ${r['precio_recomendado']:>6.2f}  "
              f"margen neto ${r['margen_neto']:>6.2f}  pedidos {r['pedidos']}")
    print(f"\nEN OBSERVACIÓN (2-3/4): {len(observacion)}")
    for r in observacion:
        print(f"  [{r['criterios_cumplidos']}/4] {r['titulo'][:52]:<52} falta: {', '.join(r['faltantes'])}")
    print(f"\nDESCARTADOS (0-1/4): {len(descartados)}")
    for r in descartados:
        print(f"  [{r['criterios_cumplidos']}/4] {r['titulo'][:52]:<52} falta: {', '.join(r['faltantes'])}")
    print(f"\nEXCLUIDOS: {len(excluidos)}")
    for e in excluidos:
        print(f"  {e['titulo'][:52]:<52} {e['motivo']}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    productos, anclas, vendedores, fecha_metricas, fecha_anclas = cargar_lotes()
    # Criterio 4: los días sin actualizar se cuentan hasta el final del día de la extracción más reciente.
    corte = datetime.fromisoformat(fecha_metricas).replace(hour=23, minute=59, tzinfo=timezone.utc)
    cualitativa = json.loads((DATA / "evaluacion_cualitativa.json").read_text(encoding="utf-8"))["productos"]
    anclas_tipo = anclas_por_tipo(anclas, vendedores)

    guardar("catalogo_salud_fitness.json", {
        "meta": {
            "fuente": "Conector AutoDS (MCP): search_products, get_product_by_id, get_similar_products, get_winning_products",
            "modo": "solo lectura",
            "extraido": fecha_metricas,
            "anclas_extraidas": fecha_anclas,
            "region": "US",
            "moneda": "USD",
            "categorias": [
                {"id": "6169735694f2b1708dccde8b", "ruta": "Sports & Fitness > Exercise & Fitness"},
                {"id": "6751af15611cd6c8f1be0bf5", "ruta": "Beauty & Personal Care > Health & Wellness"},
            ],
            "nota": "Además de las dos categorías se buscaron por palabra clave productos de dolor físico "
                    "(cervical, lumbar, pies, sueño, ronquidos, postura); AutoDS los cataloga en 'Other Category'.",
            "total_productos": len(productos),
            "total_anclas": len(anclas),
        },
        "productos": sorted(productos.values(), key=lambda p: p["id"]),
        "anclas_competencia": anclas_tipo,
    })

    top, observacion, descartados, excluidos = [], [], [], []
    for producto in productos.values():
        ev = cualitativa.get(producto["id"])
        motivo = None
        if producto.get("is_deleted"):
            motivo = f"Eliminado del catálogo de AutoDS el {str(producto.get('deleted_at', ''))[:10]}."
        elif ev is None:
            motivo = "Sin evaluación de los criterios 1 y 2."
        elif "excluir" in ev:
            motivo = ev["excluir"]
        elif ev["tipo"] not in anclas_tipo:
            motivo = f"Sin ancla de competencia para el tipo '{ev['tipo']}'."
        if motivo:
            excluidos.append({"id": producto["id"], "titulo": producto["title"], "motivo": motivo})
            continue
        resultado = evaluar(producto, ev, anclas_tipo[ev["tipo"]], corte)
        n = resultado["criterios_cumplidos"]
        (top if n == 4 else observacion if n >= 2 else descartados).append(resultado)

    top.sort(key=lambda r: r["score"], reverse=True)
    observacion.sort(key=lambda r: (r["criterios_cumplidos"], r["score"]), reverse=True)
    descartados.sort(key=lambda r: r["score"], reverse=True)

    guardar("productos_filtrados.json", {
        "parametros": {
            "fecha_extraccion": fecha_metricas,
            "fecha_anclas": fecha_anclas,
            "multiplicador_rentabilidad": MULTIPLICADOR,
            "min_pedidos": MIN_PEDIDOS,
            "max_dias_sin_actualizar": MAX_DIAS_SIN_ACTUALIZAR,
            "comision_pago": f"{COMISION_PCT * 100:.1f}% + ${COMISION_FIJA:.2f}",
            "min_vendedores_ancla_confianza_alta": MIN_VENDEDORES_CONFIANZA,
        },
        "metodologia": {
            "c1_solucion": "Evaluación del título y la descripción (data/evaluacion_cualitativa.json).",
            "c2_factor_wow": "Evaluación del título y la descripción (data/evaluacion_cualitativa.json).",
            "c3_rentabilidad": "precio_recomendado >= (costo de la variante mas barata en stock + envio) * 3. "
                               "precio_recomendado = mediana por vendedor de los listados de la competencia del mismo tipo.",
            "c4_validacion": f"pedidos >= {MIN_PEDIDOS}, stock > 0 y listado actualizado en los últimos "
                             f"{MAX_DIAS_SIN_ACTUALIZAR} días. AutoDS no da pedidos por fecha: la recencia se "
                             "aproxima con la última actualización del listado.",
            "margen_neto": "precio_recomendado - costo - envio - comision de pago (sin publicidad ni devoluciones).",
            "orden": "score = margen_neto * log10(pedidos + 10).",
        },
        "resumen": {
            "top_ganadores": len(top),
            "en_observacion": len(observacion),
            "descartados": len(descartados),
            "excluidos": len(excluidos),
        },
        "top_ganadores": top,
        "en_observacion": observacion,
        "descartados": descartados,
        "excluidos": excluidos,
    })

    imprimir_resumen(top, observacion, descartados, excluidos)
    print(f"\nGuardado: {DATA / 'catalogo_salud_fitness.json'}")
    print(f"Guardado: {DATA / 'productos_filtrados.json'}")


if __name__ == "__main__":
    main()
