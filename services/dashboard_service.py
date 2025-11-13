from sqlalchemy import func, and_
from datetime import datetime
from collections import Counter
from models.models import Credit, db
from dateutil import parser

def get_dashboard_data(
    fecha_inicio=None,
    fecha_fin=None,
    promotor=None,
    empresa=None,
    sucursal=None,
    tipo_credito=None,
    clasificacion_credito=None,
    estatus_excluir=("Cancelado", "Cerrado", "Por formalizar"),
):
    """
    Retorna datos de dashboard con filtros dinámicos por rango de fechas, promotor, empresa, sucursal, etc.

    Parámetros:
        fecha_inicio (date | str): Fecha inicial del rango.
        fecha_fin (date | str): Fecha final del rango.
        promotor (str): Nombre del promotor.
        empresa (str): Nombre de la empresa.
        sucursal (str): Nombre de la sucursal.
        estatus_excluir (tuple): Estatus a excluir del análisis.
    """

    def try_parse_date(val):
        if not val:
            return None
        try:
            # Primero intenta YYYY-MM-DD (formato HTML)
            return datetime.strptime(val, "%Y-%m-%d").date()
        except ValueError:
            # Si no, intenta detectar automáticamente el formato (incluye dd/mm/yyyy)
            return parser.parse(val, dayfirst=True).date()


    # Query base
    query = db.session.query(Credit).filter(~Credit.estatus_credito.in_(estatus_excluir))

    # Aplicar filtros dinámicos
    if fecha_inicio and fecha_fin:
        query = query.filter(Credit.fecha_desembolso.between(fecha_inicio, fecha_fin))
    elif fecha_inicio:
        query = query.filter(Credit.fecha_desembolso >= fecha_inicio)
    elif fecha_fin:
        query = query.filter(Credit.fecha_desembolso <= fecha_fin)

    if promotor:
        query = query.filter(Credit.promotor == promotor)
    if empresa:
        query = query.filter(Credit.empresa == empresa)
    if sucursal:
        query = query.filter(Credit.nombre_sucursal == sucursal)
        
    # Filtro por tipo de crédito
    if tipo_credito:
        if isinstance(tipo_credito, (list, tuple, set)):
            query = query.filter(Credit.tipo_credito.in_(tipo_credito))
        else:
            query = query.filter(Credit.tipo_credito == tipo_credito)

    # Filtro por clasificación de crédito
    if clasificacion_credito:
        if isinstance(clasificacion_credito, (list, tuple, set)):
            query = query.filter(Credit.clasificacion_credito.in_(clasificacion_credito))
        else:
            query = query.filter(Credit.clasificacion_credito == clasificacion_credito)

    # Créditos nuevos
    nuevos_creditos = query.filter(
        Credit.clasificacion_credito.in_(["Nuevo Cliente", "Nuevo Cliente Compra de deuda"])
    ).count()

    # Créditos desembolsados totales (en el rango)
    total_desembolsados = query.count()

    # Créditos por ciudad
    ciudades = (
        query.with_entities(Credit.nombre_sucursal, func.count(Credit.id))
        .group_by(Credit.nombre_sucursal)
        .all()
    )
    ciudades_labels = [c[0] for c in ciudades]
    ciudades_values = [c[1] for c in ciudades]

    # Créditos por promotor
    promotores = (
        query.with_entities(Credit.promotor, func.count(Credit.id))
        .group_by(Credit.promotor)
        .all()
    )
    promotores_labels = [p[0] for p in promotores]
    promotores_values = [p[1] for p in promotores]

    # Empresas más frecuentes
    empresas = (
        query.with_entities(Credit.empresa, func.count(Credit.id))
        .group_by(Credit.empresa)
        .order_by(func.count(Credit.id).desc())
        .all()
    )
    empresas_labels = [e[0] for e in empresas]
    empresas_values = [e[1] for e in empresas]

    # Créditos aprobados por usuario de mesa de control
    usuarios = (
        query.with_entities(Credit.usuario_mesa_control, func.count(Credit.id))
        .group_by(Credit.usuario_mesa_control)
        .all()
    )
    usuarios_labels = [u[0] for u in usuarios]
    usuarios_values = [u[1] for u in usuarios]

    # Flujo de desembolsos e intereses
    flujo = (
        query.with_entities(
            Credit.fecha_desembolso,
            Credit.monto_disponer,
            Credit.monto_disponer * (1 + Credit.nInterestRateM / 100),
        )
        .all()
    )
    flujo_sorted = sorted([f for f in flujo if f[0] is not None], key=lambda x: x[0])
    flujo_labels = [x[0].strftime("%Y-%m-%d") for x in flujo_sorted]
    flujo_values = [-x[1] for x in flujo_sorted]
    flujo_intereses = [x[2] for x in flujo_sorted]
    flujo_values_final = [neg + pos for neg, pos in zip(flujo_values, flujo_intereses)]

    # Horarios de autorización
    horarios = query.with_entities(Credit.horario_autorizacion).all()
    horas_labels = [h[0].hour for h in horarios if h[0] is not None]
    horas_counter = Counter(horas_labels)
    horas_sorted = sorted(horas_counter.items())
    horas_labels_final = [h[0] for h in horas_sorted]
    horas_values_final = [h[1] for h in horas_sorted]

    # Estadísticas de montos
    monto_promedio = query.with_entities(func.avg(Credit.monto_disponer)).scalar()
    monto_mas_chico = query.with_entities(func.min(Credit.monto_disponer)).scalar()
    monto_mas_grande = query.with_entities(func.max(Credit.monto_disponer)).scalar()

    # Usuarios con más de 2 créditos activos (según el rango)
    usuarios_creditos = (
        query.with_entities(Credit.usuario_mesa_control, func.count(Credit.id))
        .group_by(Credit.usuario_mesa_control)
        .all()
    )
    usuarios_mas2 = len([u for u in usuarios_creditos if u[1] > 2])

    return {
        "filtros": {
            "fecha_inicio": try_parse_date(fecha_inicio),
            "fecha_fin|": try_parse_date(fecha_fin),
            "promotor": promotor,
            "empresa": empresa,
            "sucursal": sucursal,
            "tipo_credito": tipo_credito,
            "clasificacion_credito": clasificacion_credito,
        },
        "fecha_default_inicio": datetime.now().replace(day=1).date(),
        "fecha_default_fin": datetime.now().date(),
        "nuevos_creditos": nuevos_creditos,
        "total_desembolsados": total_desembolsados,
        "ciudades_labels": ciudades_labels,
        "ciudades_values": ciudades_values,
        "promotores_labels": promotores_labels,
        "promotores_values": promotores_values,
        "empresas_labels": empresas_labels,
        "empresas_values": empresas_values,
        "usuarios_labels": usuarios_labels,
        "usuarios_values": usuarios_values,
        "flujo_labels": flujo_labels,
        "flujo_values": flujo_values_final,
        "horas_labels": horas_labels_final,
        "horas_values": horas_values_final,
        "monto_promedio": round(monto_promedio, 2) if monto_promedio else 0,
        "monto_mas_chico": monto_mas_chico,
        "monto_mas_grande": monto_mas_grande,
        "usuarios_mas2": usuarios_mas2,
    }
