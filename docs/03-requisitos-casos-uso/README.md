# P03 — Requisitos, actores y casos de uso

**Estado:** aprobada internamente  
**Puerta:** G03 cerrada, 12/12 controles conformes  
**Versión:** 1.0  
**Fecha de corte:** 20 de agosto de 2026

## 1. Objetivo

Definir qué debe hacer el MVP de Trazamétrica Salud Perú, quién puede ejecutar cada acción y qué evidencia permitirá aceptar el comportamiento. P03 transforma las decisiones de P00–P02 en requisitos verificables sin adelantar la arquitectura, el modelo físico de datos o la selección de dependencias.

## 2. Entradas aprobadas

- P00: propósito, límites, gobierno, datos sintéticos y reglas de cambio.
- P01: prioridad laboral de procesos, KPI, Excel, calidad, SQL y Power BI Desktop.
- P02: restricciones normativas, exclusión de información clínica y controles preventivos.

## 3. Alcance funcional del MVP

El MVP administrará una organización demostrativa con varias sedes y servicios. Permitirá versionar procesos, documentos e indicadores; importar datos sintéticos desde Excel; calcular y publicar KPI reproducibles; registrar auditorías, hallazgos, no conformidades y acciones correctivas; adjuntar evidencias; aplicar aprobaciones; mantener una bitácora; y exportar información limpia.

## 4. Supuestos controlados

- Una sola organización demostrativa por instalación; multitenencia fuera del MVP.
- Interfaz y documentación en español, con zona horaria `America/Lima`.
- Datos exclusivamente sintéticos y regenerables.
- Sin integración con historias clínicas, RENHICE, aseguradoras o sistemas institucionales.
- Power BI Desktop consume exportaciones; no existe publicación automática al servicio Power BI.
- Las alertas del MVP se muestran dentro de la aplicación; correo, SMS y mensajería quedan diferidos.
- Los archivos de evidencia son demostrativos y no contienen información real.

## 5. Expediente

- [Actores y permisos](ACTORES.md)
- [Requisitos funcionales y no funcionales](REQUISITOS.md)
- [Reglas de negocio](REGLAS_NEGOCIO.md)
- [Casos de uso](CASOS_DE_USO.md)
- [Trazabilidad, pruebas y puerta G03](TRAZABILIDAD_G03.md)

## 6. Decisiones diferidas

P04 deberá decidir la arquitectura, módulos, autenticación concreta, trabajos asíncronos, almacenamiento de evidencias, despliegue y observabilidad. P05 deberá resolver entidades, relaciones, claves, historización, catálogos y diccionario físico. Ninguna decisión diferida invalida los comportamientos exigidos en P03.

## 7. Resultado actual

El expediente contiene actores, segregación de funciones, 35 requisitos funcionales, 14 requisitos no funcionales, 26 reglas de negocio, 20 casos de uso y 18 pruebas de aceptación de alto nivel. El titular aprobó expresamente P03 y autorizó el cierre de G03 el 20 de agosto de 2026.
