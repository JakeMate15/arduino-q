import time
import sys
from arduino.app_utils import App, Bridge

print("--- Monitor de Distancia (Patrón Bridge.notify) ---")
sys.stdout.flush()

def al_recibir_distancias(izq, centro, der):
    """Esta función es llamada por el Arduino cada vez que tiene nuevas lecturas."""
    def fmt(val):
        return f"{val:5.2f} cm" if val >= 0 else "N/A"

    print(f">> IZQ: {fmt(izq)} | CENTRO: {fmt(centro)} | DER: {fmt(der)}")
    sys.stdout.flush()

# Registramos el 'provider' para que coincida con el Bridge.notify del sketch
Bridge.provide("distancias", al_recibir_distancias)

  # Ejecutamos la aplicación. El bucle se maneja internamente al recibir notificaciones.
App.run()