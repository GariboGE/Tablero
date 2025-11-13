from sqlalchemy import func, and_
from models.models import Credit, db
from datetime import datetime, date
from collections import Counter


def get_daily_data():
    hoy = datetime.now().date()

    # Filtro base: solo créditos con desembolso hoy y sin estatus indeseados
    filtro_base = and_(
        Credit.fecha_desembolso == hoy,
        ~Credit.estatus_credito.in_(["Cancelado", "Cerrado", "Por formalizar"])
    )

    # Créditos filtrados base
    creditos_filtrados = db.session.query(Credit).filter(filtro_base)

    # Créditos nuevos (solo del día y válidos)
    nuevos_creditos = creditos_filtrados.filter(
        Credit.clasificacion_credito.in_(["Nuevo Cliente", "Nuevo Cliente Compra de deuda"])
    ).count()

    # Total desembolsados del día
    total_desembolsados = creditos_filtrados.count()

    # Créditos por ciudad
    ciudades = (
        creditos_filtrados
        .with_entities(Credit.nombre_sucursal, func.count(Credit.id))
        .group_by(Credit.nombre_sucursal)
        .all()
    )
    ciudades_labels = [c[0] for c in ciudades]
    ciudades_values = [c[1] for c in ciudades]

    # Créditos por promotor
    promotores = (
        creditos_filtrados
        .with_entities(Credit.promotor, func.count(Credit.id))
        .group_by(Credit.promotor)
        .all()
    )
    promotores_labels = [p[0] for p in promotores]
    promotores_values = [p[1] for p in promotores]

    # Empresas más frecuentes
    empresas = (
        creditos_filtrados
        .with_entities(Credit.empresa, func.count(Credit.id))
        .group_by(Credit.empresa)
        .order_by(func.count(Credit.id).desc())
        .all()
    )
    empresas_labels = [e[0] for e in empresas]
    empresas_values = [e[1] for e in empresas]

    # Créditos aprobados por usuario de mesa de control
    usuarios = (
        creditos_filtrados
        .with_entities(Credit.usuario_mesa_control, func.count(Credit.id))
        .group_by(Credit.usuario_mesa_control)
        .all()
    )
    usuarios_labels = [u[0] for u in usuarios]
    usuarios_values = [u[1] for u in usuarios]

    # Flujo de desembolsos e intereses
    flujo = (
        creditos_filtrados
        .with_entities(
            Credit.fecha_desembolso,
            Credit.monto_disponer,
            Credit.monto_disponer * (1 + Credit.nInterestRateM / 100)
        )
        .all()
    )
    flujo_sorted = sorted(flujo, key=lambda x: x[0])
    flujo_labels = [x[0].strftime("%Y-%m-%d") for x in flujo_sorted]
    flujo_values = [-x[1] for x in flujo_sorted]  # desembolsos negativos
    flujo_intereses = [x[2] for x in flujo_sorted]
    flujo_values_final = [neg + pos for neg, pos in zip(flujo_values, flujo_intereses)]

    # Horarios de autorización (del día)
    horarios = creditos_filtrados.with_entities(Credit.horario_autorizacion).all()
    horas_labels = [h[0].hour for h in horarios if h[0] is not None]
    horas_counter = Counter(horas_labels)
    horas_sorted = sorted(horas_counter.items())
    horas_labels_final = [h[0] for h in horas_sorted]
    horas_values_final = [h[1] for h in horas_sorted]

    # Estadísticas de montos
    monto_promedio = creditos_filtrados.with_entities(func.avg(Credit.monto_disponer)).scalar()
    monto_mas_chico = creditos_filtrados.with_entities(func.min(Credit.monto_disponer)).scalar()
    monto_mas_grande = creditos_filtrados.with_entities(func.max(Credit.monto_disponer)).scalar()

    # Usuarios con más de 2 créditos (del día)
    usuarios_creditos = (
        creditos_filtrados
        .with_entities(Credit.usuario_mesa_control, func.count(Credit.id))
        .group_by(Credit.usuario_mesa_control)
        .all()
    )
    usuarios_mas2 = len([u for u in usuarios_creditos if u[1] > 2])

    return {
        "fecha_actual": hoy,
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
