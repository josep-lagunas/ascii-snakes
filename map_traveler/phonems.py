import wave
import numpy as np

frequency = 440  # frecuencia para el sonido de "a"
fs = 44100  # muestras por segundo
seconds = 0.1  # duración del sonido

# Generar un arreglo con seconds*sample_rate pasos, con valores entre 0 y seconds
t = np.linspace(0, seconds, int(seconds * fs), endpoint=False)

# Generar una onda senoidal de 440 Hz
note = np.sin(frequency * t * 2 * np.pi)

# Asegurar que el valor más alto esté en el rango de 16 bits
scaling = (2 ** 15) - 1
note *= scaling

# Convertir a datos de 16 bits
samples = note.astype(np.int16)

# Abrir un archivo de audio para escritura
with wave.open("a.wav", "w") as f:
    # Establecer el ancho de muestra y el número de canales
    f.setsampwidth(2)
    f.setnchannels(1)
    # Establecer la tasa de muestreo
    f.setframerate(fs)
    # Escribir las muestras en el archivo
    f.writeframes(samples.tostring())
