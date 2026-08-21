# Reglas y servicios de aplicación

## 1. Frontera de escritura

Toda mutación funcional se inicia en `apps.organizations.services` y se ejecuta dentro de `transaction.atomic`. Antes de cambiar datos, el servicio verifica que el actor esté activo y tenga `organizations.manage`.

| Servicio | Regla principal |
|---|---|
| `create_organization` | Rechaza una segunda organización activa |
| `create_site` | Exige organización activa y código único |
| `create_service` | Exige sede y organización activas |
| `create_area` | Exige organización activa y padre del mismo ámbito |
| `update_master_identity` | Conserva actor de modificación y rechaza inactivos |
| `move_area` | Rechaza padre propio, otro ámbito y ciclos indirectos |
| `assign_responsibility` | Exige usuario/área activos y vigencia sin superposición |
| `end_responsibility` | Finaliza sin invadir otra vigencia |
| `deactivate_master` | Exige motivo y cierre previo de dependencias activas |

## 2. Denegación por defecto

- `ADMIN_SYSTEM` y el superusuario técnico poseen `organizations.manage`.
- Los ocho roles vigentes de P06 pueden consultar mediante `organizations.view` según su matriz.
- Un usuario autenticado sin capacidad recibe HTTP 403.
- La vista no habilita escritura; la interfaz de mantenimiento se añadirá sobre estos servicios, no directamente sobre el ORM.

## 3. Jerarquía de áreas

Al mover un área, el servicio recorre la cadena de ancestros desde el padre propuesto. Rechaza la operación si encuentra el área movida o un identificador ya visitado. La base también bloquea la autorreferencia directa.

## 4. Vigencias

Los intervalos son inclusivos. Por ello, una responsabilidad que termina el 31 y otra que empieza el 31 se superponen. La validación bloquea filas existentes durante la transacción y la base conserva unicidad del inicio y coherencia de fechas.

## 5. Desactivación

- Organización: requiere no tener sedes ni áreas activas.
- Sede: requiere no tener servicios activos.
- Área: requiere no tener áreas hijas activas ni responsabilidades vigentes.
- Servicio: puede desactivarse directamente con motivo.

El resultado conserva `deactivated_at`, `deactivated_by`, `deactivation_reason` y `updated_by`.
