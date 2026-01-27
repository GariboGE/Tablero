from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin


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

    # Relaciones
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
