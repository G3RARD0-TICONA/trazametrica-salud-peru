# Regresión lineal y logística

## Separación temporal

Las observaciones se ordenan cronológicamente y se dividen sin barajar. La fracción final, configurable entre 10 % y 40 %, se reserva como prueba; sus etiquetas no intervienen en el ajuste. Se exigen al menos cuatro observaciones de entrenamiento y dos de prueba; la logística exige además ambas clases en entrenamiento.

## Regresión lineal

Se utiliza mínimos cuadrados ordinarios sobre el índice temporal. La evaluación informa MAE, RMSE y R². La línea base predice siempre la media del entrenamiento; el modelo solo supera la puerta cuando su RMSE de prueba no es mayor.

## Regresión logística

La etiqueta representa cumplimiento de la meta KPI aprobada según su sentido. El índice temporal se estandariza exclusivamente con media y desviación del entrenamiento. El ajuste por descenso de gradiente es determinista y limita iteraciones y tasa de aprendizaje. La evaluación informa exactitud, precisión, sensibilidad, F1, Brier y matriz de confusión; la línea base usa la clase mayoritaria del entrenamiento.

## Rechazo de calidad

Una ejecución que no iguala la línea base permanece registrada como `rejected_quality`. No se oculta ni se presenta como modelo aceptado. Un R² alto aislado tampoco sustituye métricas de prueba, supuestos, estabilidad o validación externa.

