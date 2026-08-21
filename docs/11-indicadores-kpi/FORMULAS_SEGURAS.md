# Fórmulas declarativas y reproducibles

## Contrato

La fórmula se almacena como árbol JSON normalizado. Admite hasta 64 nodos y 8 niveles.

| Familia | Operadores | Contrato |
|---|---|---|
| Agregados | `sum`, `average`, `minimum`, `maximum`, `count` | un rol de observaciones no vacío |
| Aritmética | `add`, `subtract`, `multiply`, `divide` | exactamente dos argumentos |
| Constante | `constant` | decimal finito como texto canónico |

Ejemplo de porcentaje:

```json
{
  "op": "multiply",
  "args": [
    {
      "op": "divide",
      "args": [
        {"op": "sum", "role": "numerator"},
        {"op": "sum", "role": "denominator"}
      ]
    },
    {"op": "constant", "value": "100"}
  ]
}
```

## Controles

- Lista positiva de operadores y claves exactas por nodo.
- Roles normalizados y explícitos; no se infieren desde texto libre.
- Prohibición de `eval`, `exec`, imports, atributos, funciones dinámicas y SQL.
- División entre cero, entradas vacías, no finitos y exceso de `numeric(20,6)` bloquean el cálculo.
- SHA-256 de la fórmula canónica antes de aprobación y al calcular.
- Contexto decimal con precisión 38 y resultado cuantizado a seis decimales.

El mismo árbol, versión y conjunto ordenado de observaciones produce el mismo valor y hash.
