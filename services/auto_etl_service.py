import os
import shutil
import logging
import pandas as pd
from datetime import datetime
from services.etl_service import import_csv_to_db
from services.log_service import registrar_log

logger = logging.getLogger(__name__)

ENCODINGS = ["utf-8", "latin-1", "cp1252"]


def _leer_csv(file_path):
    """Intenta leer el CSV con UTF-8, luego latin-1, luego cp1252."""
    for enc in ENCODINGS:
        try:
            return pd.read_csv(file_path, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"No se pudo leer {file_path} con ninguna codificación soportada.")


def _archivar_archivo(file_path, folder_path):
    """Mueve el archivo a la carpeta archive/ con timestamp."""
    archive_dir = os.path.join(folder_path, "archive")
    os.makedirs(archive_dir, exist_ok=True)
    nombre = os.path.basename(file_path)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(archive_dir, f"{ts}_{nombre}")
    shutil.move(file_path, dest)
    logger.info("Archivo archivado en: %s", dest)


def process_new_csvs(folder_path):
    if not os.path.exists(folder_path):
        logger.warning("[AUTO ETL] Carpeta no existe: %s", folder_path)
        return

    files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]

    if not files:
        logger.info("[AUTO ETL] No hay archivos nuevos en %s", folder_path)
        return

    for file in files:
        file_path = os.path.join(folder_path, file)
        logger.info("[AUTO ETL] Procesando: %s", file)

        try:
            df = _leer_csv(file_path)
            inserted, skipped, updated = import_csv_to_db(df)
            logger.info(
                "[AUTO ETL] OK — %d insertados, %d actualizados, %d omitidos",
                inserted, updated, skipped
            )
            registrar_log(
                tipo="scheduler",
                estado="exito",
                mensaje=f"Archivo: {file}",
                insertados=inserted,
                actualizados=updated,
                omitidos=skipped,
            )
            _archivar_archivo(file_path, folder_path)

        except Exception as exc:
            logger.error("[AUTO ETL] ERROR procesando %s: %s", file, exc)
            registrar_log(
                tipo="scheduler",
                estado="error",
                mensaje=f"Archivo: {file} — {exc}",
            )
