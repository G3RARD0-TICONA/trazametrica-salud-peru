# Rendimiento de referencia

## Entorno oficial

- GitHub Actions Ubuntu;
- Python 3.13.15;
- Django 5.2 LTS;
- PostgreSQL 17.11;
- una aplicación web y una base de datos sin red externa.

## Conjunto sintético v1

| Elemento | Volumen mínimo |
|---|---:|
| Sedes | 3 |
| Servicios | 20 |
| Procesos | 100 |
| Indicadores | 200 |
| Observaciones | 100 000 |
| Filas XLSX de referencia | 10 000 |

## Umbrales

- p95 de inicio, organización, procesos, indicadores y tablero: ≤2 s;
- cada solicitud primaria medida: ≤20 consultas SQL;
- validación atómica de XLSX de 10 000 filas: ≤60 s;
- ninguna prueba de rendimiento puede desactivar validaciones, permisos o bitácora para alcanzar la meta.

Los tiempos son una línea base del entorno CI, no una promesa de capacidad productiva. P18 deberá repetirlos sobre la infraestructura publicada y documentar CPU, memoria, latencia, concurrencia y costo.
