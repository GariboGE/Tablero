from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime


db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=True)


class Credit(db.Model):
    __tablename__ = "credits"

    id = db.Column(db.Integer, primary_key=True)
    tipo_credito = db.Column(db.String(100))
    fecha_desembolso = db.Column(db.Date)
    numero_credito = db.Column(db.Integer, unique=True, nullable=False)
    empresa = db.Column(db.String(200))
    promotor = db.Column(db.String(200))
    nombre_cliente = db.Column(db.String(200))
    monto_autorizado = db.Column(db.Float)
    monto_refinanciar = db.Column(db.Float)
    monto_disponer = db.Column(db.Float)
    clasificacion_credito = db.Column(db.String(200))
    nombre_sucursal = db.Column(db.String(200))
    nombre_aval = db.Column(db.String(200))
    mes_desembolso = db.Column(db.String(50))
    estatus_credito = db.Column(db.String(100))
    suma_ref = db.Column(db.Float)
    suma_proveedores = db.Column(db.Float)
    monto_crecimiento = db.Column(db.Float)
    monto_refinanciado = db.Column(db.Float)
    tipo_comite = db.Column(db.String(100))
    horario_autorizacion = db.Column(db.Time)
    usuario_mesa_control = db.Column(db.String(100))
    tipo_disposicion = db.Column(db.String(100))
    total_dispersiones = db.Column(db.Float)
    vFirstDueDate = db.Column(db.Date)
    nInterestRateM = db.Column(db.Float)

    related_credits = db.relationship("RelatedCredit", backref="credit", cascade="all, delete-orphan")
    providers = db.relationship("Provider", backref="credit", cascade="all, delete-orphan")
    dispositions = db.relationship("Disposition", backref="credit", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Credit #{self.numero_credito} - {self.nombre_cliente}>"


class RelatedCredit(db.Model):
    __tablename__ = "related_credits"

    id = db.Column(db.Integer, primary_key=True)
    credit_id = db.Column(db.Integer, db.ForeignKey("credits.id"))
    referencia_credito = db.Column(db.Integer)
    monto_liquidar = db.Column(db.Float)


class Provider(db.Model):
    __tablename__ = "providers"

    id = db.Column(db.Integer, primary_key=True)
    credit_id = db.Column(db.Integer, db.ForeignKey("credits.id"))
    nombre_proveedor = db.Column(db.String(200))
    monto = db.Column(db.Float)


class Disposition(db.Model):
    __tablename__ = "dispositions"

    id = db.Column(db.Integer, primary_key=True)
    credit_id = db.Column(db.Integer, db.ForeignKey("credits.id"))
    referencia_disposicion = db.Column(db.Integer)
    monto = db.Column(db.Float)


class MetaMensual(db.Model):
    """Meta de colocación por sucursal, mes y año."""
    __tablename__ = "metas_mensuales"

    id = db.Column(db.Integer, primary_key=True)
    sucursal = db.Column(db.String(100), nullable=False)
    mes = db.Column(db.Integer, nullable=False)
    anio = db.Column(db.Integer, nullable=False)
    monto = db.Column(db.Float, nullable=False, default=0.0)

    __table_args__ = (
        db.UniqueConstraint("sucursal", "mes", "anio", name="uq_meta_sucursal_mes_anio"),
    )

    def __repr__(self):
        return f"<MetaMensual {self.sucursal} {self.mes}/{self.anio} ${self.monto:,.0f}>"


class BotLog(db.Model):
    """Registro de ejecuciones del bot y carga de CSVs."""
    __tablename__ = "bot_logs"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    tipo = db.Column(db.String(50))    # 'scheduler', 'manual', 'csv_manual'
    estado = db.Column(db.String(20))  # 'exito', 'error'
    mensaje = db.Column(db.Text)
    insertados = db.Column(db.Integer, default=0)
    actualizados = db.Column(db.Integer, default=0)
    omitidos = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<BotLog {self.tipo} {self.estado} @ {self.timestamp}>"


class EmailDestinatario(db.Model):
    """Lista persistente de destinatarios para reportes por email."""
    __tablename__ = "email_destinatarios"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    nombre = db.Column(db.String(200))
    activo = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<EmailDestinatario {self.email}>"
