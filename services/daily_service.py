import logging
from sqlalchemy import func, and_
from models.models import Credit, MetaMensual, db
from datetime import datetime, timedelta, date
import calendar

logger = logging.getLogger(__name__)

# Valores por defecto si no hay metas en la BD (usados solo en seed inicial)
_DEFAULT_GOALS = {
    "Tijuana": 10110386.30,
    "Mexicali": 1866718.99,
    "Ensenada": 777694.89,
}


def get_meta_mensual(mes, anio):
    """Retorna la meta total del mes desde la BD, o la suma de defaults si no hay registros."""
    metas = MetaMensual.query.filter_by(mes=mes, anio=anio).all()
    if not metas:
        logger.warning("Sin metas en BD para %d/%d — usando valores por defecto.", mes, anio)
        return sum(_DEFAULT_GOALS.values())
    return sum(m.monto for m in metas)


def calcular_dias_habiles_restantes(fecha_actual):
    festivos = [
        date(2026, 1, 1),
        date(2026, 2, 2),
        date(2026, 3, 16),
        date(2026, 5, 1),
        date(2026, 9, 16),
        date(2026, 11, 16),
        date(2026, 12, 25),
    ]
    ultimo_dia = calendar.monthrange(fecha_actual.year, fecha_actual.month)[1]
    fecha_fin_mes = fecha_actual.replace(day=ultimo_dia)
    dias_habiles = 0
    fecha_temp = fecha_actual
    while fecha_temp <= fecha_fin_mes:
        if fecha_temp.weekday() < 5 and fecha_temp not in festivos:
            dias_habiles += 1
        fecha_temp += timedelta(days=1)
    return dias_habiles


def get_daily_data():
    hoy = datetime.now().date()
    inicio_mes = hoy.replace(day=1)
    meta_mensual = get_meta_mensual(hoy.month, hoy.year)

    filtro_dia = and_(
        Credit.fecha_desembolso == hoy,
        ~Credit.estatus_credito.in_(["Cancelado", "Cerrado"]),
        Credit.tipo_credito.in_(["NOMINA"]),
    )
    creditos = db.session.query(Credit).filter(filtro_dia)

    total_creditos = creditos.count()
    total_monto = creditos.with_entities(func.sum(Credit.monto_disponer)).scalar() or 0

    filtro_mes = and_(
        Credit.fecha_desembolso.between(inicio_mes, hoy),
        ~Credit.estatus_credito.in_(["Cancelado", "Cerrado"]),
        Credit.tipo_credito.in_(["NOMINA"]),
    )
    creditos_mes = db.session.query(Credit).filter(filtro_mes)
    total_monto_mes = creditos_mes.with_entities(func.sum(Credit.monto_disponer)).scalar() or 0

    avance_mensual = (total_monto_mes / meta_mensual * 100) if meta_mensual else 0

    dias_habiles_restantes = calcular_dias_habiles_restantes(hoy)
    meta_diaria_requerida = (
        (meta_mensual - total_monto_mes) / dias_habiles_restantes
        if dias_habiles_restantes else 0
    )

    sucursales = (
        creditos
        .with_entities(Credit.nombre_sucursal, func.sum(Credit.monto_disponer), func.count(Credit.id))
        .group_by(Credit.nombre_sucursal)
        .order_by(func.sum(Credit.monto_disponer).desc())
        .all()
    )
    sucursales = [(s[0], float(s[1]), s[2]) for s in sucursales]

    promotores = (
        creditos
        .with_entities(Credit.promotor, func.sum(Credit.monto_disponer), func.count(Credit.id))
        .group_by(Credit.promotor)
        .order_by(func.sum(Credit.monto_disponer).desc())
        .all()
    )
    promotores = [(p[0], float(p[1]), p[2]) for p in promotores]

    empresas = (
        creditos
        .with_entities(Credit.empresa, func.sum(Credit.monto_disponer), func.count(Credit.id))
        .group_by(Credit.empresa)
        .order_by(func.sum(Credit.monto_disponer).desc())
        .all()
    )
    empresas = [(e[0], float(e[1]), e[2]) for e in empresas]

    # Tendencia: últimos 30 días de colocación diaria (NOMINA)
    trend_inicio = hoy - timedelta(days=29)
    trend_rows = (
        db.session.query(Credit.fecha_desembolso, func.sum(Credit.monto_disponer))
        .filter(
            Credit.fecha_desembolso.between(trend_inicio, hoy),
            ~Credit.estatus_credito.in_(["Cancelado", "Cerrado"]),
            Credit.tipo_credito.in_(["NOMINA"]),
        )
        .group_by(Credit.fecha_desembolso)
        .order_by(Credit.fecha_desembolso)
        .all()
    )
    trend_por_fecha = {str(d): float(m or 0) for d, m in trend_rows if d}
    trend_labels, trend_values = [], []
    for i in range(30):
        f = trend_inicio + timedelta(days=i)
        trend_labels.append(f.strftime("%d/%m"))
        trend_values.append(trend_por_fecha.get(str(f), 0))

    return {
        "fecha_actual": hoy,
        "total_creditos": total_creditos,
        "total_monto": total_monto,
        "meta_mensual": meta_mensual,
        "monto_acumulado_mes": total_monto_mes,
        "avance_mensual": avance_mensual,
        "meta_diaria_requerida": meta_diaria_requerida,
        "sucursales": sucursales,
        "promotores": promotores,
        "empresas": empresas,
        "trend_labels": trend_labels,
        "trend_values": trend_values,
    }
