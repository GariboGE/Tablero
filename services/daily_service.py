from sqlalchemy import func, and_
from models.models import Credit, db
from datetime import datetime, timedelta
from collections import Counter

META_DIARIA = 500000

def get_daily_data():
    hoy = datetime.now().date() - timedelta(days=1)

    # Filtro base: créditos desembolsados hoy y válidos
    filtro_base = and_(
        Credit.fecha_desembolso == hoy,
        ~Credit.estatus_credito.in_(["Cancelado", "Cerrado", "Por formalizar"])
    )

    creditos = db.session.query(Credit).filter(filtro_base)

    # Totales diarios
    total_creditos = creditos.count()
    total_monto = creditos.with_entities(func.sum(Credit.monto_disponer)).scalar() or 0

    # Sucursales (monto + créditos)
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

    # Promotores
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

    # Empresas
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
        "total_monto": total_monto,
        "meta_diaria": META_DIARIA,
        "avance": (total_monto / META_DIARIA) * 100 if META_DIARIA else 0,

        "sucursales": sucursales,
        "promotores": promotores,
        "empresas": empresas
    }

