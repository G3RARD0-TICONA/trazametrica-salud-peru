# Semilla organizacional sintética

## 1. Propósito

`seed_organizations_demo` materializa el subconjunto de P07 del dataset previsto en P05. No importa archivos y no deriva información de clínicas reales.

## 2. Contenido versión 1

| Objeto | Cantidad | Convención |
|---|---:|---|
| Organización | 1 | `ORG-DEMO` y advertencia sintética |
| Sedes | 3 | Norte, Centro y Sur sintéticas |
| Servicios | 20 | `SER-01` a `SER-20` |
| Áreas | 12 | Jerarquía administrativa ficticia |

## 3. Determinismo

- Namespace UUID fijo: `f59a753c-0896-5c9d-a490-c9ac0c1e0907`.
- Cada UUID se deriva mediante UUIDv5 de una clave lógica estable.
- La semilla usa nombres ficticios y la fecha no interviene en identificadores.
- Ejecutarla nuevamente actualiza el catálogo administrado y conserva conteos/UUID.

## 4. Ejecución

```bash
docker compose exec web python src/manage.py seed_organizations_demo \
  --actor admin_demo --version 1
```

Debe ejecutarse después de `bootstrap_access`. Solo funciona en `local`, `test` o `demo`; no ofrece `--reset` destructivo. El comando integral `seed_demo` y el reinicio completo se implementarán cuando todos los módulos de datos existan.

## 5. Criterios de aceptación

1. Primera ejecución produce exactamente 1/3/20/12 registros.
2. Segunda ejecución conserva los mismos conteos.
3. UUID de organización y primera sede coinciden con sus claves deterministas.
4. Todos los nombres y etiquetas declaran su carácter sintético.
5. Una organización activa diferente bloquea la semilla para no mezclar ámbitos.
