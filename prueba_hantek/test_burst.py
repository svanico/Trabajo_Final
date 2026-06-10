import os
import time
import numpy as np
import traceback
import matplotlib.pyplot as plt
from hantek_driver import Hantek1008

os.add_dll_directory(os.getcwd())

def ejecutar_captura_burst():
    print("=== CONFIGURACIÓN DE PARÁMETROS BURST MODE ===")
    canales_activos = [0] 
    escalas_verticales = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    base_tiempo_ns = 200_000 
    
    print(f"Canales activos: {canales_activos}")
    print(f"Base de tiempo:  {base_tiempo_ns} ns/div\n")

    # Variable para guardar los datos de forma segura
    datos_completos = None
    
    # ==========================================
    # BLOQUE 1: ADQUISICIÓN ESTRICTA DE HARDWARE
    # ==========================================
    osc = Hantek1008(
        active_channels=canales_activos,
        vertical_scale_factor=escalas_verticales,
        ns_per_div=base_tiempo_ns
    )

    try:
        print("1. Configurando hardware e iniciando conexión...")
        osc.connect()
        osc.init()
        
        print("2. Disparando captura en Modo Burst...")
        tiempo_inicio = time.perf_counter()
        
        # Obtenemos los datos a máxima velocidad
        datos_completos = osc.request_samples_burst_mode(mode="volt")
        
        duracion = time.perf_counter() - tiempo_inicio
        print(f"-> Captura completada en {duracion:.4f} s.\n")

    except Exception as e:
        print(f"\n[ERROR FATAL] Falló la cadena de hardware/software:")
        traceback.print_exc()

    finally:
        # ¡El hardware se libera INMEDIATAMENTE después de capturar!
        print("3. Ejecutando protocolo de cierre USB...")
        osc.close()
        print("-> Hardware liberado correctamente.\n")

    # ==========================================
    # BLOQUE 2: PROCESAMIENTO Y VISUALIZACIÓN
    # ==========================================
    if datos_completos:
        print("4. Procesando y graficando los datos en memoria...")
        
        # 1. Calculamos la Frecuencia Teórica (Base)
        fs_base = 25 / (base_tiempo_ns * 1e-9)
        
        # 2. Aplicamos la corrección por Multiplexación del ADC
        # Extraemos el factor directamente del driver según cuántos canales encendiste
        factor_aceleracion = osc.actual_sampling_rate_factor(len(canales_activos))
        fs_real = fs_base * factor_aceleracion
        
        print(f"-> Fs Base: {fs_base/1000:.1f} kHz | Factor Multiplicador: {factor_aceleracion}x")
        print(f"-> Frecuencia de Muestreo REAL: {fs_real/1000:.2f} kHz\n")
        
        plt.figure(figsize=(10, 5))
        plt.title(f'Captura Modo Burst - Hantek 1008C\nBase: {base_tiempo_ns/1000} µs/div | Fs Real: {fs_real/1000:.1f} kHz', fontsize=12)
        
        muestras_validas = False

        for canal in canales_activos:
            if canal in datos_completos and len(datos_completos[canal]) > 0:
                muestras_validas = True
                voltajes = np.array(datos_completos[canal])
                
                # 3. Creamos el vector de tiempo usando la Fs REAL corregida
                tiempo_ms = (np.arange(len(voltajes)) / fs_real) * 1000.0
                
                plt.plot(tiempo_ms, voltajes, '*-', label=f'CH{canal} Físico', linewidth=1.5)
                
                v_pp = np.max(voltajes) - np.min(voltajes)
                print(f"-> CH{canal}: {len(voltajes)} muestras | Vpp: {v_pp:.4f} V")

        if muestras_validas:
            plt.xlabel('Tiempo (ms)', fontsize=11, fontweight='bold')
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
    ejecutar_captura_burst()