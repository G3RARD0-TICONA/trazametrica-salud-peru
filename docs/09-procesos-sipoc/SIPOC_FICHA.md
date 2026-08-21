# Ficha y SIPOC

## Ficha mínima aprobable

1. Código y nombre del proceso.
2. Organización y área propietaria activas.
3. Tipo: estratégico, operativo o soporte.
4. Objetivo no vacío.
5. Alcance no vacío.
6. Al menos un proveedor.
7. Al menos una entrada.
8. Al menos una actividad.
9. Al menos una salida.
10. Al menos un cliente.

Cada sección admite varios elementos con posición única. El hash se recalcula al cambiar la ficha o cualquier elemento de un borrador. Después del envío, la ficha completa queda inmutable; una corrección posterior exige rechazo a borrador o una nueva versión.

## Consulta

`/processes/` muestra el catálogo activo agrupado por tipo. `/processes/<uuid>/` presenta la ficha y sus versiones. Ambas rutas requieren `processes.view` y mantienen visible la advertencia de datos sintéticos.
