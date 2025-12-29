import pandas as pd
import numpy as np

# Cargar el archivo original
df = pd.read_csv('recorrido_robot.csv')

# 1. Filtro de Sensores: Eliminar rebotes imposibles
df = df[(df['dist_derecho'] > 0) & (df['dist_derecho'] < 150)]
df = df[(df['dist_frontal'] > 0) & (df['dist_frontal'] < 150)]

# 2. Suavizado (Moving Average): Quitar el temblor
df['dist_frontal'] = df['dist_frontal'].rolling(window=5).mean()
df['dist_derecho'] = df['dist_derecho'].rolling(window=5).mean()
df = df.dropna()

# 3. Eliminar la "Zona Muerta" (Si no te mueves, no aprendes)
df = df[df[['pwm_izq', 'pwm_der']].abs().max(axis=1) > 20]

# 4. CREAR CARACTERÍSTICAS DE MEMORIA (Vital para el R2)
df['delta_der'] = df['dist_derecho'].diff().fillna(0)
df['lag1'] = df['dist_derecho'].shift(1).fillna(df['dist_derecho'])
df['lag2'] = df['dist_derecho'].shift(2).fillna(df['dist_derecho'])

# 5. BALANCEO AGRESIVO (El secreto del éxito)
# Definimos 'giro' como cualquier momento donde los motores no son iguales
es_giro = (df['pwm_izq'] - df['pwm_der']).abs() > 15
giros = df[es_giro]
rectas = df[~es_giro]

# Reducimos las rectas para que haya la misma cantidad que giros
rectas_balanceadas = rectas.sample(n=min(len(giros), len(rectas)), random_state=42)
df_final = pd.concat([giros, rectas_balanceadas]).sample(frac=1) # Mezclar todo

# 6. Guardar el archivo para entrenamiento
df_final.to_csv('datos_mejorados.csv', index=False)
print(f"Limpieza y Balanceo: Giros({len(giros)}) | Rectas({len(rectas_balanceadas)})")
print("Archivo 'datos_mejorados.csv' listo.")