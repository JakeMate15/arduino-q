import pandas as pd
from xgboost import XGBRegressor
from sklearn.preprocessing import StandardScaler
import joblib

# Cargar el mapa purificado
df = pd.read_csv('datos_mejorados.csv')

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

# Guardar
joblib.dump(modelo, 'cerebro_robot.pkl')
joblib.dump(scaler, 'escalador.pkl')

# Verificación rápida
score = modelo.score(X_scaled, y)
print(f"Precisión sobre el mapa: {score:.4f}")