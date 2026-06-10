import os
import time
import numpy as np
import traceback
import matplotlib.pyplot as plt
from hantek_driver import Hantek1008

os.add_dll_directory(os.getcwd())

def ejecutar_captura_continua():
    print("=== CONFIGURACIÓN DE PARÁMETROS ROLL MODE ===")
    canales_activos = [0, 1]  # Modifica esto para agregar o quitar hidrófonos
    escalas_verticales = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    
    # Valores válidos estrictos del driver: 440, 220, 88, 44, 22, 11, 5, 2, 1...
    freq_solicitada = 440 
    
    # Tiempo total que la PC estará grabando (en segundos)
    tiempo_grabacion_segundos = 1

    print(f"Canales activos: {canales_activos}")
    print(f"Frec. Solicitada: {freq_solicitada} Hz/canal")
    print(f"Tiempo de captura: {tiempo_grabacion_segundos} s\n")

    # Preparamos el "balde" dinámico para guardar los datos
    datos_completos = {canal: [] for canal in canales_activos}
    duracion_real = 0.0

    # ==========================================
    # BLOQUE 1: ADQUISICIÓN ESTRICTA DE HARDWARE
    # ==========================================
    osc = Hantek1008(
        active_channels=canales_activos,
        vertical_scale_factor=escalas_verticales
    )

    try:
        print("1. Configurando hardware e iniciando conexión...")
        osc.connect()
        osc.init()
        
        print("2. Iniciando grabación en Modo Continuo (Roll)...")
        # Pedimos el generador (la "manguera" de datos)
        generador = osc.request_samples_roll_mode(sampling_rate=freq_solicitada, mode="volt")
        
        tiempo_inicio = time.perf_counter() #inicia un contador
        
        # Bucle de recolección en tiempo real
        for bloque_datos in generador:
            # bloque_datos es un diccionario que trae los canales activos en ese milisegundo
            for canal in canales_activos:
                if canal in bloque_datos:
                    datos_completos[canal].extend(bloque_datos[canal])
            
            # Cortamos por software al alcanzar el tiempo deseado
            if time.perf_counter() - tiempo_inicio >= tiempo_grabacion_segundos:
                break
                
        duracion_real = time.perf_counter() - tiempo_inicio
        print(f"-> Adquisición detenida físicamente en {duracion_real:.4f} s.\n")

    except Exception as e:
        print(f"\n[ERROR FATAL] Falló la cadena de hardware/software:")
        traceback.print_exc()

    finally:
        print("3. Ejecutando protocolo de cierre USB...")
        osc.close()
        print("-> Hardware liberado correctamente.\n")

    # ==========================================
    # BLOQUE 2: PROCESAMIENTO Y VISUALIZACIÓN
    # ==========================================
    # Verificamos si capturamos datos en el primer canal activo para usarlo como referencia
    canal_ref = canales_activos[0]
    if len(datos_completos[canal_ref]) > 0:
        print("4. Procesando y graficando los datos en memoria...")
        
        # En modo Roll, la frecuencia se calcula empíricamente
        muestras_totales = len(datos_completos[canal_ref])
        fs_real = muestras_totales / duracion_real
        
        plt.figure(figsize=(10, 5))
        plt.title(f'Captura Modo Continuo - Hantek 1008C\nTiempo: {duracion_real:.2f} s | Fs Efectiva: {fs_real:.1f} Hz', fontsize=12)

        # Iteramos sobre los canales para agregarlos a la misma grilla
        for canal in canales_activos:
            voltajes = np.array(datos_completos[canal])
            
            # Creamos el eje temporal (esta vez en Segundos, ya que el roll mode es más lento)
            tiempo_seg = np.arange(len(voltajes)) / fs_real
            
            plt.plot(tiempo_seg, voltajes,'*-' ,label=f'CH{canal} Físico', linewidth=1.5, alpha=0.8)
            
            v_pp = np.max(voltajes) - np.min(voltajes)
            print(f"-> CH{canal}: {len(voltajes)} muestras | Vpp: {v_pp:.4f} V | Vprom: {np.mean(voltajes):.4f} V")

        plt.xlabel('Tiempo (Segundos)', fontsize=11, fontweight='bold')
        plt.ylabel('Amplitud (V)', fontsize=11, fontweight='bold')
        plt.grid(True, which='major', linestyle='-', alpha=0.6)
        plt.grid(True, which='minor', linestyle=':', alpha=0.3)
        plt.minorticks_on()
        plt.legend(loc='upper right')
        plt.tight_layout()
        
        print("-> Desplegando ventana gráfica interactiva.")
        plt.show() 
    else:
        print("[ADVERTENCIA] El búfer llegó vacío. No hay datos para graficar.")

if __name__ == "__main__":
    ejecutar_captura_continua()