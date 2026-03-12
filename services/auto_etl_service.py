import os
import pandas as pd
from services.etl_service import import_csv_to_db

def process_new_csvs(folder_path):
    if not os.path.exists(folder_path):
        print("[AUTO ETL] Carpeta no existe")
        return

    files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]

    if not files:
        print("[AUTO ETL] No hay archivos nuevos")
        return

    for file in files:
        file_path = os.path.join(folder_path, file)
        print(f"[AUTO ETL] Procesando {file}")

        try:
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except:
                try:
                    df = pd.read_csv(file_path, encoding='latin-1')
                except:
                    df = pd.read_csv(file_path, encoding='cp1252')

            inserted, skipped, updated = import_csv_to_db(df)
            print(f"[AUTO ETL] OK -> {inserted} insertados, {updated} actualizados, {skipped} omitidos")

            os.remove(file_path)

        except Exception as e:
            print(f"[AUTO ETL] ERROR: {e}")
