"""
Entrenamiento del modelo IA - Entrena XGBoost con los datos procesados.
"""
import os
import pandas as pd
from xgboost import XGBRegressor
from sklearn.preprocessing import StandardScaler
import joblib

# Directorio de datos
DIR_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

# Cargar el mapa purificado
df = pd.read_csv(os.path.join(DIR_DATA, 'datos_mejorados.csv'))

X = df[['f_grid', 'd_grid']]
y = df[['pwm_izq', 'pwm_der']]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# XGBoost configurado para GENERALIZAR (no memorizar)
modelo = XGBRegressor(
    n_estimators=500,
    learning_rate=0.05,
    max_depth=6,          # Profundidad moderada para que "entienda" y no solo "copie"
    reg_lambda=1,         # Penaliza respuestas extremas
    n_jobs=-1
)

print("Entrenando con el mapa de situaciones...")
modelo.fit(X_scaled, y)

# Guardar en carpeta data/
joblib.dump(modelo, os.path.join(DIR_DATA, 'cerebro_robot.pkl'))
joblib.dump(scaler, os.path.join(DIR_DATA, 'escalador.pkl'))

# Verificación rápida
score = modelo.score(X_scaled, y)
print(f"Precisión sobre el mapa: {score:.4f}")
print(f"Modelo guardado en: {DIR_DATA}")
