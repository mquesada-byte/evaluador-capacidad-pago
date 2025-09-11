# utils/storage.py
import os, json

BASE_DIR = "data_clientes"   # 👈 nombre corregido

def ensure_base_dir():
    os.makedirs(BASE_DIR, exist_ok=True)

def save_reporte(cedula: str, data: dict):
    ensure_base_dir()
    file_path = os.path.join(BASE_DIR, f"{cedula}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_reporte(cedula: str) -> dict | None:
    file_path = os.path.join(BASE_DIR, f"{cedula}.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None
