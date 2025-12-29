import pandas as pd
import numpy as np

# 1. Cargar el dataset con todas las situaciones
df = pd.read_csv('recorrido_robot.csv')

# 2. Agrupar por "Celdas de Situación"
# Redondeamos a cada 5cm para crear grupos de situaciones similares
df['f_grid'] = (df['dist_frontal'] / 5).round() * 5
df['d_grid'] = (df['dist_derecho'] / 5).round() * 5

print(f"Muestras totales: {len(df)}")

# 3. Crear el Consenso
# Para cada "celda" de distancia, calculamos la respuesta PROMEDIO
df_mapa = df.groupby(['f_grid', 'd_grid']).agg({
    'pwm_izq': 'mean',
    'pwm_der': 'mean'
}).reset_index()

# 4. Limpieza de seguridad
df_mapa = df_mapa.dropna()

# 5. Guardar el mapa de navegación
df_mapa.to_csv('datos_mejorados.csv', index=False)
print(f"Situaciones únicas aprendidas: {len(df_mapa)}")