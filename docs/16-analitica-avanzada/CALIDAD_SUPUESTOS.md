# Calidad, supuestos, sesgo y monitoreo

Cada ejecución conserva:

- origen sintético y procesado de las observaciones;
- definición y versión exactas;
- parámetros y hash SHA-256;
- periodo, orden e identificadores de entrada;
- hash de entradas y hash del resultado;
- cantidad total, entrenamiento y prueba;
- métricas del modelo y línea base;
- control de fuga de datos;
- limitaciones de validez y exclusión clínica.

## Riesgos controlados

| Riesgo | Control P16 |
|---|---|
| Fuga temporal | partición cronológica, sin barajar |
| Sobreajuste | conjunto de prueba y comparación contra línea base |
| Parámetros silenciosamente modificados | versión inmutable y hash canónico |
| Resultado irreproducible | orden estable, entradas y hashes conservados |
| Sesgo por cobertura | límites explícitos; no generalizar fuera de la semilla |
| Interpretación clínica | marca sintética y exclusión visible en web, modelo y documentos |

P17 medirá rendimiento y seguridad transversal. P18 definirá monitoreo operativo del entorno demostrativo; P16 solo conserva la evidencia necesaria para comparar futuras ejecuciones.

