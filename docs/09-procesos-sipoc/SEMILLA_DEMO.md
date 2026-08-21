# Semilla demostrativa P09

La semilla crea únicamente contenido administrativo ficticio y requiere ejecutar primero P07.

```bash
docker compose exec web python src/manage.py seed_organizations_demo --actor admin_demo
docker compose exec web python src/manage.py seed_processes_demo --actor admin_demo --dataset-version 1
```

## Contrato de volumen

| Tipo | Procesos | Versiones borrador | Elementos SIPOC |
|---|---:|---:|---:|
| Estratégico | 10 | 10 | 50 |
| Operativo | 60 | 60 | 300 |
| Soporte | 30 | 30 | 150 |
| Total | 100 | 100 | 500 |

Los UUID se derivan con UUIDv5 a partir de claves estables. Repetir el comando no duplica registros. La semilla solo está habilitada en entornos `local`, `test` o `demo` y no importa archivos externos.
