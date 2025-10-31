from sqlalchemy import func
from datetime import datetime
from models.models import Credit, db

def get_dashboard_data():
    # Créditos nuevos
    nuevos_creditos = db.session.query(Credit).filter(
        Credit.clasificacion_credito.in_(["Nuevo Cliente", "Nuevo Cliente Compra de deuda"])
    ).count()

    # Créditos desembolsados
    total_desembolsados = db.session.query(Credit).count()

    # Créditos por ciudad
    ciudades = db.session.query(Credit.nombre_sucursal, func.count(Credit.id)).group_by(Credit.nombre_sucursal).all()
    ciudades_labels = [c[0] for c in ciudades]
    ciudades_values = [c[1] for c in ciudades]

    # Créditos por promotor
    promotores = db.session.query(Credit.promotor, func.count(Credit.id)).group_by(Credit.promotor).all()
    promotores_labels = [p[0] for p in promotores]
    promotores_values = [p[1] for p in promotores]

    # Empresas más frecuentes
    empresas = db.session.query(Credit.empresa, func.count(Credit.id)).group_by(Credit.empresa).order_by(func.count(Credit.id).desc()).all()
    empresas_labels = [e[0] for e in empresas]
    empresas_values = [e[1] for e in empresas]

    # Créditos aprobados por usuario de mesa de control
    usuarios = db.session.query(Credit.usuario_mesa_control, func.count(Credit.id)).group_by(Credit.usuario_mesa_control).all()
    usuarios_labels = [u[0] for u in usuarios]
    usuarios_values = [u[1] for u in usuarios]

    # Flujo de desembolsos e ingresos por interés (gráfico senoidal)
    flujo = db.session.query(Credit.fecha_desembolso, Credit.monto_disponer, Credit.monto_disponer*(1+Credit.nInterestRateM/100)).all()
    
    flujo_filtered = [f for f in flujo if f[0] is not None]
    flujo_sorted = sorted(flujo_filtered, key=lambda x: x[0])

    flujo_labels = [x[0].strftime("%Y-%m-%d") for x in flujo_sorted]
    flujo_values = [-x[1] for x in flujo_sorted]  # desembolsos como negativos
    flujo_intereses = [x[2] for x in flujo_sorted]  # valor final con interés
    flujo_values_final = [neg+pos for neg, pos in zip(flujo_values, flujo_intereses)]  # combinamos

    # Horarios de autorización
    horarios = db.session.query(Credit.horario_autorizacion).all()
    horas_labels = [h[0].hour for h in horarios if h[0] is not None]
    
    # contamos por hora
    from collections import Counter
    horas_counter = Counter(horas_labels)
    horas_sorted = sorted(horas_counter.items())
    horas_labels_final = [h[0] for h in horas_sorted]
    horas_values_final = [h[1] for h in horas_sorted]

    # Estadística: monto promedio de créditos y usuarios con >2 créditos activos
    monto_promedio = db.session.query(func.avg(Credit.monto_disponer)).scalar()
    monto_mas_chico = db.session.query(func.min(Credit.monto_disponer)).scalar()
    monto_mas_grande = db.session.query(func.max(Credit.monto_disponer)).scalar()
    usuarios_creditos = db.session.query(Credit.usuario_mesa_control, func.count(Credit.id)).group_by(Credit.usuario_mesa_control).all()
    usuarios_mas2 = len([u for u in usuarios_creditos if u[1]>2])

    return {
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
        "monto_promedio": round(monto_promedio,2) if monto_promedio else 0,
        "monto_mas_chico": monto_mas_chico,
        "monto_mas_grande": monto_mas_grande,
        "usuarios_mas2": usuarios_mas2
    }
