from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import current_user
from services.dashboard_service import get_dashboard_data
from flask import Blueprint, render_template, request
from models.models import Credit, db
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
        
    
    today = datetime.now().date()
    fecha_default_inicio = today.replace(day=1)
    fecha_default_fin = today
    
    fecha_inicio = request.args.get('fecha_inicio') or fecha_default_inicio.strftime('%Y-%m-%d')
    fecha_fin = request.args.get('fecha_fin') or fecha_default_fin.strftime('%Y-%m-%d')
    
    filtros = {
    'fecha_inicio': fecha_inicio,
    'fecha_fin': fecha_fin,
    'promotor': request.args.get('promotor'),
    'empresa': request.args.get('empresa'),
    'sucursal': request.args.get('sucursal'),
    'tipo_credito': request.args.get('tipo_credito'),
    'clasificacion_credito': request.args.get('clasificacion_credito')
    }
    
    # Llenar selects dinámicamente (sin duplicados)
    promotores = [p[0] for p in db.session.query(Credit.promotor).distinct() if p[0]]
    empresas = [e[0] for e in db.session.query(Credit.empresa).distinct() if e[0]]
    sucursales = [s[0] for s in db.session.query(Credit.nombre_sucursal).distinct() if s[0]]
    tipo_credito = [t[0] for t in db.session.query(Credit.tipo_credito).distinct() if t[0]]
    clasificacion_credito = [c[0] for c in db.session.query(Credit.clasificacion_credito).distinct() if c[0]]
    
    data = get_dashboard_data(**filtros)
    
    return render_template(
        'dashboard.html',
        data=data,
        promotores=promotores,
        empresas=empresas,
        sucursales=sucursales,
        tipo_credito=tipo_credito,
        clasificacion_credito=clasificacion_credito,
        fecha_default_inicio=fecha_default_inicio,
        fecha_default_fin=fecha_default_fin
    )