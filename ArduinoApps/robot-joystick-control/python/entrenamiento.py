import pandas as pd
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib

# Cargar el archivo procesado
df = pd.read_csv('datos_mejorados.csv')

# ENTRADAS: Incluimos los Lags para que la IA sepa de dónde viene el robot
X = df[['dist_frontal', 'dist_derecho', 'delta_der', 'lag1', 'lag2']]
y = df[['pwm_izq', 'pwm_der']]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.15, random_state=42)

# Red más robusta con activación TANH (mejor para motores)
red = MLPRegressor(
    hidden_layer_sizes=(128, 64, 32), 
    activation='tanh', 
    solver='adam', 
    max_iter=3000, 
    early_stopping=True,
    verbose=True
)

print("Entrenando con Memoria y Balanceo...")
red.fit(X_train, y_train)

score = red.score(X_test, y_test)
print(f"\nPrecisión final (R^2): {score:.4f}")

if score > 0.45:
    joblib.dump(red, 'cerebro_robot.pkl')
    joblib.dump(scaler, 'escalador.pkl')
    print("¡Modelo guardado con éxito!")
else:
    print("El R2 sigue bajo. Considera grabar datos más lentos y precisos.")