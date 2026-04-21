from flask_mail import Message
from flask import current_app, render_template 
from .screenshot_service import capture_page
from datetime import datetime
import os


def send_email(subject, recipients, body, html=None):
    from app import mail
    
    today = datetime.today()
    fecha_inicio = today.replace(day=1).strftime('%Y-%m-%d')
    fecha_fin = today.strftime('%Y-%m-%d')
    
    context = {
        "fecha": datetime.now().strftime('%d/%m/%Y'),
        "titulo": "desembolsos de nómina"
    }
    
    msg = Message(
        subject=subject,
        recipients=recipients,
        body=body,
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    
    msg.html = render_template('email_report.html', **context)
    
    # Firma embebida
    firma_path = os.path.join(current_app.root_path, 'static/email/firma.png')
    with open(firma_path, 'rb') as f:
        msg.attach(
            filename='firma.png',
            content_type='image/png',
            data=f.read(),
            disposition='inline',
            headers={'Content-ID': '<firma>'}
        )
        
    if html:
        msg.html = html.replace('{{FIRMA}}', '<img src="cid:firma">')
    
    dashboard_url = (
        f"http://localhost:5000/dashboard/dashboard"
        f"?fecha_inicio={fecha_inicio}"
        f"&fecha_fin={fecha_fin}"
        f"&promotor="
        f"&empresa="
        f"&sucursal="
        f"&tipo_credito=NOMINA"
        f"&clasificacion_credito="
    )
    
    capture_page(dashboard_url, "dashboard_nomina.png", 1920, 1500)
    capture_page("http://localhost:5000/daily/daily", "daily.png", 1920, 1080)
        
    for img in ['static/screenshots/daily.png', 'static/screenshots/dashboard_nomina.png']:
        with open(img, 'rb') as f:
            msg.attach(
                filename=os.path.basename(img),
                content_type='image/png',
                data=f.read()
            )
            
    mail.send(msg)
    
    os.remove('static/screenshots/daily.png')
    os.remove('static/screenshots/dashboard_nomina.png')
