from sqlalchemy import func, and_
from models.models import Credit, db
from datetime import datetime, timedelta
import calendar

# Metas 
TIJUANA = 9235545.74
MEXICALI = 1879180.5
ENSENADA = 645935.41
META_MENSUAL = TIJUANA + MEXICALI + ENSENADA


def calcular_dias_habiles_restantes(fecha_actual): 
    """ Calcula los días hábiles del mes. Excluye fines de semana y días festivos. """ 
    festivos = [ 
        datetime(2026, 1, 1).date(), 
        datetime(2026, 2, 2).date(), 
        datetime(2026, 3, 16).date(), 
        datetime(2026, 5, 1).date(), 
        datetime(2026, 9, 16).date(), 
        datetime(2026, 11, 16).date(), 
        datetime(2026, 12, 25).date(), ] 
    
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
    hoy = datetime.now().date() - timedelta(days=0)

    # Inicio de mes (para la meta mensual)
    inicio_mes = hoy.replace(day=1)

    # ------------------------------
    # 1) Filtro base para el DÍA
    # ------------------------------
    filtro_base = and_(
        Credit.fecha_desembolso == hoy,
        ~Credit.estatus_credito.in_(["Cancelado", "Cerrado"])
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
        ~Credit.estatus_credito.in_(["Cancelado", "Cerrado"]),
        Credit.tipo_credito.in_(["NOMINA"])
    )

    creditos_mes = db.session.query(Credit).filter(filtro_mes)
    total_monto_mes = creditos_mes.with_entities(func.sum(Credit.monto_disponer)).scalar() or 0

    avance_mensual = (total_monto_mes / META_MENSUAL) * 100 if META_MENSUAL else 0
    
    # ------------------------------
    # 2.1) Meta diaria requerida
    # ------------------------------
    dias_habiles_restantes_mes = calcular_dias_habiles_restantes(hoy)
    meta_diaria_requerida = (META_MENSUAL - total_monto_mes) / dias_habiles_restantes_mes if dias_habiles_restantes_mes else 0


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
        .order_by(func.sum(Credit.monto_disponer).desc())
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
        .order_by(func.sum(Credit.monto_disponer).desc())
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
        .order_by(func.sum(Credit.monto_disponer).desc())
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
        "meta_diaria_requerida": meta_diaria_requerida,

        "sucursales": sucursales,
        "promotores": promotores,
        "empresas": empresas
    }
