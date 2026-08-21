# Modelo de identidad y acceso

## 1. Principios

1. **Denegación por defecto:** una cuenta autenticada sin rol vigente no puede abrir el panel.
2. **Mínimo privilegio:** cada rol recibe únicamente capacidades necesarias para su función demostrativa.
3. **Separación de funciones:** `ADMIN_SYSTEM` no aprueba procesos, documentos, cargas, KPI, auditorías, mejoras o riesgos.
4. **Trazabilidad del actor:** toda cuenta ordinaria, rol y asignación conserva quién creó o modificó el registro.
5. **Sin borrado de evidencia:** los usuarios y roles se desactivan con fecha, actor y motivo.
6. **Vigencia explícita:** una asignación solo concede capacidades dentro de su intervalo cerrado de fechas.
7. **Control en servidor:** los endpoints protegidos validan capacidades aunque una interfaz sea manipulada.

## 2. Componentes implementados

| Componente | Responsabilidad | Evidencia de código |
|---|---|---|
| `User` | Identidad, credenciales, estado y actores de auditoría | `src/apps/accounts/models.py` |
| `Role` | Agrupación estable y normalizada de capacidades | `src/apps/accounts/models.py` |
| `UserRole` | Asignación temporal de un rol a un usuario | `src/apps/accounts/models.py` |
| Política | Relación declarativa rol → capacidades | `src/apps/accounts/policies.py` |
| Servicios | Asignar/finalizar roles y desactivar cuentas | `src/apps/accounts/services.py` |
| Decorador | Rechazar solicitudes sin capacidad | `src/apps/accounts/decorators.py` |
| Bootstrap | Crear cuenta técnica y catálogo de roles sintéticos | `bootstrap_access` |

## 3. Ciclo de una cuenta

`creación por actor autorizado → asignación de rol → acceso durante vigencia → finalización o desactivación`

- Una cuenta ordinaria no puede crearse sin `created_by`.
- La única excepción es la cuenta técnica inicial, que debe ser superusuario y registrar `bootstrap_reason`.
- Una cuenta inactiva debe conservar `deactivated_at`, `deactivated_by` y `deactivation_reason`.
- La aplicación no elimina cuentas ni reutiliza sus identificadores UUID.

## 4. Reglas de asignación

- `valid_to` no puede ser anterior a `valid_from`.
- Dos asignaciones del mismo rol al mismo usuario no pueden superponerse.
- Los límites son inclusivos: una asignación que termina el 31 y otra que empieza el 31 se superponen.
- La asignación requiere actor, usuario y rol activos.
- El servicio bloquea las filas existentes durante la validación para reducir condiciones de carrera.
- La restricción de fechas también reside en PostgreSQL.

## 5. Autenticación y sesión

- Backend: `ModelBackend` de Django.
- Hash de contraseñas: mecanismo predeterminado de Django; en pruebas se acelera sin cambiar la lógica.
- Longitud mínima configurada: 12 caracteres, más validadores de similitud, contraseña común y valor numérico.
- Sesión: cookie `HttpOnly`, `SameSite=Lax`, cierre al cerrar navegador y duración máxima de ocho horas.
- Demo: cookies seguras, redirección HTTPS configurable, HSTS y cabecera de proxy explícita.
- La contraseña de bootstrap se recibe solo mediante `BOOTSTRAP_ADMIN_PASSWORD` y nunca se imprime.

## 6. Frontera con P05 y P07

P05 definió 46 entidades funcionales. P06 implementa únicamente las tres entidades de identidad necesarias para iniciar Django correctamente; las tablas técnicas de sesiones, permisos, migraciones y administración pertenecen al framework y no se contabilizan como nuevas entidades del dominio. P07 implementa organización, sedes, servicios, áreas y responsabilidades, con comprobaciones de capacidad y ámbito organizacional.
