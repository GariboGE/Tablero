from sqlalchemy import func, and_
from models.models import Credit, db
from datetime import datetime, timedelta

META_MENSUAL = 15000000  # ajusta aquí la meta mensual que quieras

def get_daily_data():
    # Hoy lo tienes como "ayer"
    hoy = datetime.now().date()

    # Inicio de mes (para la meta mensual)
    inicio_mes = hoy.replace(day=1)

    # ------------------------------
    # 1) Filtro base para el DÍA
    # ------------------------------
    filtro_base = and_(
        Credit.fecha_desembolso == hoy,
        ~Credit.estatus_credito.in_(["Cancelado", "Cerrado", "Por formalizar"])
    )

    creditos = db.session.query(Credit).filter(filtro_base)

    # Totales del día
    total_creditos = creditos.count()
    total_monto = creditos.with_entities(func.sum(Credit.monto_disponer)).scalar() or 0

    # ------------------------------
    # 2) Acumulado MENSUAL
    # ------------------------------
    filtro_mes = and_(
        Credit.fecha_desembolso.between(inicio_mes, hoy),
        ~Credit.estatus_credito.in_(["Cancelado", "Cerrado", "Por formalizar"])
    )

    creditos_mes = db.session.query(Credit).filter(filtro_mes)
    total_monto_mes = creditos_mes.with_entities(func.sum(Credit.monto_disponer)).scalar() or 0

    avance_mensual = (total_monto_mes / META_MENSUAL) * 100 if META_MENSUAL else 0

    # ------------------------------
    # 3) Sucursales (del día)
    # ------------------------------
    sucursales = (
        creditos
        .with_entities(
            Credit.nombre_sucursal,
            func.sum(Credit.monto_disponer),
            func.count(Credit.id)
        )
        .group_by(Credit.nombre_sucursal)
        .all()
    )
    sucursales = [(s[0], float(s[1]), s[2]) for s in sucursales]

    # Promotores (del día)
    promotores = (
        creditos
        .with_entities(
            Credit.promotor,
            func.sum(Credit.monto_disponer),
            func.count(Credit.id)
        )
        .group_by(Credit.promotor)
        .all()
    )
    promotores = [(p[0], float(p[1]), p[2]) for p in promotores]

    # Empresas (del día)
    empresas = (
        creditos
        .with_entities(
            Credit.empresa,
            func.sum(Credit.monto_disponer),
            func.count(Credit.id)
        )
        .group_by(Credit.empresa)
        .all()
    )
    empresas = [(e[0], float(e[1]), e[2]) for e in empresas]

    return {
        "fecha_actual": hoy,
        "total_creditos": total_creditos,
        "total_monto": total_monto,            # monto SOLO del día
        "meta_mensual": META_MENSUAL,          # nueva meta
        "monto_acumulado_mes": total_monto_mes,
        "avance_mensual": avance_mensual,

        "sucursales": sucursales,
        "promotores": promotores,
        "empresas": empresas
    }
