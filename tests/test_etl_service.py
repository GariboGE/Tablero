"""Tests para el pipeline ETL — import_csv_to_db."""
import pandas as pd
import pytest
from services.etl_service import import_csv_to_db, parse_date, parse_time
from models.models import Credit, db


# ── Helpers ────────────────────────────────────────────────────

def _make_df(rows):
    """Crea un DataFrame con las columnas mínimas que espera el ETL."""
    base = {
        "No. Crédito": None,
        "Tipo de Crédito": "NOMINA",
        "Fecha Desembolso": "01/01/2026",
        "Empresa": "ACME",
        "Promotor": "Juan",
        "Nombre del cliente": "Cliente Test",
        "Monto Autorizado": 10000.0,
        "Monto a Refinanciar": 0.0,
        "Monto a Disponer": 9500.0,
        "Clasificación del crédito": "Nuevo Cliente",
        "Nombre de la Sucursal": "Tijuana",
        "Nombre Aval": "",
        "Mes Desembolso": "Enero",
        "Estatus del crédito": "Activo",
        "Suma REF": 0.0,
        "Suma Proveedores": 0.0,
        "Monto crecimiento": 0.0,
        "Monto refinanciado": 0.0,
        "Tipo de Comité": "Normal",
        "Horario Autorización": None,
        "Usuario Mesa de Control": "admin",
        "Tipo de Disposición": "Efectivo",
        "Total Dispersiones": 1.0,
        "vFirstDueDate": "15/01/2026",
        "nInterestRateM": 4.5,
    }
    data = []
    for numero, overrides in rows:
        row = dict(base)
        row["No. Crédito"] = numero
        row.update(overrides)
        data.append(row)
    return pd.DataFrame(data)


# ── parse_date ─────────────────────────────────────────────────

def test_parse_date_valid():
    result = parse_date("15/03/2025")
    assert result is not None
    assert result.day == 15
    assert result.month == 3


def test_parse_date_none():
    assert parse_date(None) is None


def test_parse_date_nan():
    assert parse_date(float("nan")) is None


# ── parse_time ─────────────────────────────────────────────────

def test_parse_time_valid():
    result = parse_time("2025-01-15 09:30:00")
    assert result is not None
    assert result.hour == 9


def test_parse_time_none():
    assert parse_time(None) is None


# ── import_csv_to_db ───────────────────────────────────────────

def test_insert_new_credit(app, db):
    with app.app_context():
        df = _make_df([(99001, {})])
        inserted, skipped, updated = import_csv_to_db(df)

        assert inserted == 1
        assert skipped == 0
        credit = db.session.query(Credit).filter_by(numero_credito=99001).first()
        assert credit is not None
        assert credit.promotor == "Juan"
        assert credit.monto_disponer == 9500.0


def test_skip_duplicate_credit(app, db):
    with app.app_context():
        df = _make_df([(99002, {})])
        import_csv_to_db(df)

        inserted, skipped, updated = import_csv_to_db(df)
        assert skipped == 1
        assert inserted == 0


def test_update_status_on_existing_credit(app, db):
    with app.app_context():
        df_original = _make_df([(99003, {"Estatus del crédito": "Activo"})])
        import_csv_to_db(df_original)

        df_updated = _make_df([(99003, {"Estatus del crédito": "Cancelado"})])
        inserted, skipped, updated = import_csv_to_db(df_updated)

        assert updated == 1
        credit = db.session.query(Credit).filter_by(numero_credito=99003).first()
        assert credit.estatus_credito == "Cancelado"


def test_strips_totales_row(app, db):
    with app.app_context():
        df = _make_df([(99004, {}), (99005, {})])
        # Agregar fila TOTALES al final
        totales_row = {col: "TOTALES" for col in df.columns}
        df = pd.concat([df, pd.DataFrame([totales_row])], ignore_index=True)

        inserted, skipped, _ = import_csv_to_db(df)
        assert inserted == 2  # La fila TOTALES fue ignorada


def test_returns_correct_tuple_shape(app, db):
    with app.app_context():
        df = _make_df([(99010, {}), (99011, {})])
        result = import_csv_to_db(df)
        assert len(result) == 3  # (insertados, omitidos, actualizados)
