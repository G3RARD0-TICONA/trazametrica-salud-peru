# Archivos y seguridad

## 1. Contrato admitido

| Control | Regla P08 |
|---|---|
| Origen | Exclusivamente sintético y confirmado por el actor |
| Tamaño | Mayor que cero y máximo 10 MiB |
| Extensión | `.pdf`, `.docx`, `.xlsx`, `.csv` o `.txt` |
| MIME | Lista explícita coherente con el tipo permitido |
| Nombre | Solo nombre base, sin directorios |
| Almacenamiento | Clave opaca bajo `documents/`, `imports/` o `reports/`, sin `..` |
| Integridad | SHA-256 hexadecimal de 64 caracteres |
| Escaneo | `pending`, `clean`, `rejected` o `error`; una versión solo acepta `clean` |

## 2. Frontera actual

`FileAsset` es el contrato de metadatos para cualquier adaptador posterior. P08 no sirve archivos desde rutas aportadas por el usuario y no interpreta su contenido. El binario deberá almacenarse fuera del árbol público del repositorio y fuera de `STATIC_ROOT`.

P15 reutiliza este contrato para salidas generadas por el sistema bajo `reports/`. CSV se admite solo como salida sintética controlada; la aplicación neutraliza texto interpretable como fórmula antes de escribir CSV o XLSX.

## 3. Controles pendientes de despliegue

P17/P18 deberán integrar almacenamiento privado, URLs temporales, análisis antimalware real, cuotas, limpieza de cargas huérfanas, cabeceras de descarga y pruebas de contenido. Hasta entonces, el estado `clean` solo puede provenir de un adaptador de demostración controlado; no constituye certificación de seguridad.

## 4. Repositorio público

Nunca se versionan archivos cargados, `.env`, credenciales, tokens, exportaciones reales ni capturas clínicas. Los ejemplos y pruebas generan únicamente nombres, dominios `.invalid`, hashes y contenidos ficticios.
