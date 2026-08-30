# Estadística descriptiva, Pareto y control

## Contratos reproducibles

| Familia | Entrada | Salida verificable |
|---|---|---|
| Descriptivos | valores KPI ordenados | cantidad, media, mediana, rango, desviación, Q1, Q3 e IQR |
| Atípicos | cuartiles interpolados | índices y valores fuera de `Q1 − 1.5·IQR` o `Q3 + 1.5·IQR` |
| Pareto | servicio y magnitud | peso, porcentaje y acumulado con desempate estable |
| Control | serie KPI | línea central, sigma poblacional, límites de tres sigmas y señales |
| Tendencia | serie y ventana | medias móviles y pronóstico ingenuo de un paso |

Los valores se procesan en orden cronológico y con desempate por periodo, dimensión e identificador. Números no finitos, ventanas inválidas, conjuntos vacíos o pesos negativos se rechazan con un diagnóstico accionable.

## Interpretación permitida

Los resultados ayudan a explorar variación administrativa sintética y priorizar revisión humana. Una señal estadística no demuestra causalidad, incumplimiento, riesgo clínico ni necesidad de tratamiento. El sistema conserva esa limitación junto a cada ejecución.

