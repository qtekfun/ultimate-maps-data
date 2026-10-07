# UltimateMaps-data

Datos de mapas para [UltimateMaps](https://github.com/qtekfun/UltimateMaps): mapas vectoriales fuera de línea y datos de búsqueda y rutas, por regiones. Se publican como *releases* de este repositorio; la app los baja desde el catálogo `catalog.json`.

Catálogo estable (siempre la última versión): `https://github.com/qtekfun/UltimateMaps-data/releases/latest/download/catalog.json`

## Qué hay en cada release

- `catalog.json`: jerarquía de regiones y, para las descargables, URL, tamaño y SHA-256 de cada fichero.
- `<región>.pmtiles`: mapa para dibujar (PMTiles de Protomaps, recortado con el polígono de la región; las regiones vecinas se solapan en el borde).
- `<región>.mwm`: datos de búsqueda y rutas (formato de CoMaps/Organic Maps). Se instalan con el nombre original de CoMaps.
- `World.mwm`, `WorldCoasts.mwm`: datos globales que necesita el motor de búsqueda.
- `SHA256SUMS`: huellas de todos los ficheros.

## Origen y licencias

- **Datos de OpenStreetMap:** © OpenStreetMap contributors, bajo la [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/). Estos ficheros son bases de datos derivadas y se comparten bajo la misma licencia; la app muestra la atribución.
- **PMTiles:** extraídos del build diario del planeta de [Protomaps](https://docs.protomaps.com/basemaps/downloads) (20261006) con [`pmtiles extract`](https://github.com/protomaps/go-pmtiles). Las teselas son un producto derivado de OSM (ODbL).
- **`.mwm`:** generados por el proyecto [CoMaps](https://codeberg.org/comaps/comaps) a partir de OSM (versión de datos 261004, serie 2026.06.28), copiados sin modificar. No hemos encontrado condiciones de uso específicas de su CDN; si eres del proyecto y prefieres que se retiren o se sirvan de otra forma, abre un *issue*.
- **Polígonos de las regiones:** `data/borders/*.poly` de CoMaps.
- Los scripts que generan el catálogo y los recortes están en `scripts/` del repositorio de la app (`gen-region-catalog.py`, `split-pmtiles.py`).

Sin garantía. Los datos de OSM pueden contener errores y no deben usarse para nada crítico.
