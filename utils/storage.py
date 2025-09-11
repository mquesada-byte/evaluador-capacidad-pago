import os, json

# Carpeta donde se guardarán los archivos por cliente
DATA_DIR = "data/clientes"

def _file_path(cedula: str) -> str:
    """Devuelve la ruta completa del archivo JSON para una cédula dada."""
    return os.path.join(DATA_DIR, f"{cedula}.json")

def save_reporte(cedula: str, reporte: dict):
    """Guarda el reporte completo (todos los pasos) en un archivo JSON por cédula."""
    os.makedirs(DATA_DIR, exist_ok=True)  # crea la carpeta si no existe
    with open(_file_path(cedula), "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=2)

def load_reporte(cedula: str) -> dict | None:
    """Carga un reporte desde disco si existe, o devuelve None si no está."""
    try:
        with open(_file_path(cedula), "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
