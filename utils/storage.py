import os
import json

# Carpeta base del proyecto (donde está la carpeta data_clientes)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data_clientes")

def save_reporte(identificacion: str, data: dict):
    """Guarda el reporte de un cliente en data_clientes/<identificacion>.json"""
    os.makedirs(DATA_DIR, exist_ok=True)
    ruta = os.path.join(DATA_DIR, f"{identificacion}.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"[DEBUG] Guardado en: {ruta}")  # 👈 esto aparece en consola
    return ruta

def load_reporte(identificacion: str) -> dict | None:
    """Carga el reporte desde data_clientes/<identificacion>.json si existe"""
    ruta = os.path.join(DATA_DIR, f"{identificacion}.json")
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

