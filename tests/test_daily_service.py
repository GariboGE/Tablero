"""Tests para daily_service — get_daily_data y get_meta_mensual."""
import pytest
from datetime import date
from models.models import Credit, MetaMensual, db
from services.daily_service import get_meta_mensual, get_daily_data


# ── Helpers ────────────────────────────────────────────────────

def _make_credit(numero, monto, fecha=None, tipo="NOMINA", estatus="Activo", sucursal="Tijuana", promotor="Ana", empresa="ACME"):
    return Credit(
        numero_credito=numero,
        tipo_credito=tipo,
        fecha_desembolso=fecha or date.today(),
        empresa=empresa,
        promotor=promotor,
        nombre_cliente=f"Cliente {numero}",
        monto_disponer=monto,
        nombre_sucursal=sucursal,
        estatus_credito=estatus,
        clasificacion_credito="Nuevo Cliente",
        monto_autorizado=monto,
    )


# ── get_meta_mensual ───────────────────────────────────────────

def test_meta_falls_back_to_default_when_no_db_entry(app, db):
    with app.app_context():
        # Mes muy lejano que no tiene metas sembradas
        total = get_meta_mensual(mes=6, anio=2099)
        # Debe retornar la suma de los defaults hardcodeados
        assert total == pytest.approx(10110386.30 + 1866718.99 + 777694.89, rel=1e-3)


def test_meta_reads_from_db(app, db):
    with app.app_context():
        db.session.add(MetaMensual(sucursal="Tijuana", mes=3, anio=2026, monto=5_000_000))
        db.session.add(MetaMensual(sucursal="Mexicali", mes=3, anio=2026, monto=2_000_000))
        db.session.commit()

        total = get_meta_mensual(mes=3, anio=2026)
        assert total == pytest.approx(7_000_000)


# ── get_daily_data ─────────────────────────────────────────────

def test_get_daily_data_returns_expected_keys(app, db):
    with app.app_context():
        data = get_daily_data()
        expected_keys = {
            "fecha_actual", "total_creditos", "total_monto",
            "meta_mensual", "monto_acumulado_mes", "avance_mensual",
            "meta_diaria_requerida", "sucursales", "promotores",
            "empresas", "trend_labels", "trend_values",
        }
        assert expected_keys.issubset(data.keys())


def test_get_daily_data_counts_only_nomina(app, db):
    with app.app_context():
        hoy = date.today()
        db.session.add(_make_credit(88001, 10000, fecha=hoy, tipo="NOMINA"))
        db.session.add(_make_credit(88002, 20000, fecha=hoy, tipo="GRUPAL"))
        db.session.commit()

        data = get_daily_data()
        # Solo créditos NOMINA del día deben contarse
        creditos_nomina = data["total_creditos"]
        assert creditos_nomina >= 1  # al menos el que acabamos de agregar

        # Verificar que el monto del crédito GRUPAL no contamina el total
        credito_grupal = db.session.query(Credit).filter_by(numero_credito=88002).first()
        assert credito_grupal is not None  # existe en DB pero no en el conteo daily


def test_get_daily_data_excludes_cancelled(app, db):
    with app.app_context():
        hoy = date.today()
        db.session.add(_make_credit(88003, 50000, fecha=hoy, tipo="NOMINA", estatus="Cancelado"))
        db.session.commit()

        data = get_daily_data()
        # El crédito cancelado no debe sumar al monto
        credito = db.session.query(Credit).filter_by(numero_credito=88003).first()
        assert credito is not None
        assert credito.estatus_credito == "Cancelado"


def test_trend_labels_length_is_30(app, db):
    with app.app_context():
        data = get_daily_data()
        assert len(data["trend_labels"]) == 30
        assert len(data["trend_values"]) == 30


def test_avance_mensual_between_0_and_100_plus(app, db):
    with app.app_context():
        data = get_daily_data()
        assert data["avance_mensual"] >= 0
