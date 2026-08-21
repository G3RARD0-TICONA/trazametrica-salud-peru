# Modelo de maestros organizacionales

## 1. Entidades implementadas

| P05 | Modelo Django | Tabla PostgreSQL | Ámbito del código |
|---|---|---|---|
| ENT-004 | `Organization` | `organizations_organization` | Instalación |
| ENT-005 | `Site` | `organizations_site` | Organización |
| ENT-006 | `Service` | `organizations_service` | Sede |
| ENT-007 | `Area` | `organizations_area` | Organización |
| ENT-008 | `ResponsibilityAssignment` | `organizations_responsibility_assignment` | Área, usuario y tipo |

## 2. Relaciones

```text
Organization 1 ── N Site 1 ── N Service
      │
      └── N Area ── N Area hija
                └── N ResponsibilityAssignment N ── 1 User
```

Todas las claves foráneas utilizan `PROTECT`. Las entidades conservan UUID, actor creador/modificador y fecha. Los cuatro maestros codificados agregan estado activo y evidencia obligatoria de desactivación.

## 3. Integridad

- `Organization.code` es único sin distinguir mayúsculas.
- Un índice único parcial sobre una expresión constante permite una sola organización activa.
- `Site`, `Service` y `Area` combinan su ámbito con `Lower(code)`.
- Un área no puede referenciarse como padre y el servicio bloquea ciclos indirectos.
- La zona horaria debe existir en IANA; la semilla utiliza `America/Lima`.
- La etiqueta de organización debe declarar `DATOS SINTÉTICOS`.
- `ResponsibilityAssignment.valid_to` debe ser nula o mayor/igual a `valid_from`.

## 4. Ciclo de vida

`activo → desactivado con fecha, actor y motivo`

No se implementa reactivación automática. Un maestro inactivo no se edita ni admite nuevos hijos. Una organización, sede o área con dependencias activas no puede desactivarse hasta cerrar la estructura descendiente o las responsabilidades vigentes.

## 5. Protección de historial

Los métodos `delete()` de instancia y queryset lanzan `ValidationError`. Esta defensa complementa `on_delete=PROTECT`: incluso un registro todavía no referenciado debe desactivarse, porque RN-001 prohíbe reutilizar su código y RF-005 exige conservar el historial.
