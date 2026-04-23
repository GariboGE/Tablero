import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def registrar_log(tipo, estado, mensaje=None, insertados=0, actualizados=0, omitidos=0):
    """Persiste un evento de bot/ETL en la tabla bot_logs."""
    try:
        from models.models import BotLog, db
        log = BotLog(
            timestamp=datetime.now(),
            tipo=tipo,
            estado=estado,
            mensaje=(mensaje[:500] if mensaje else None),
            insertados=insertados or 0,
            actualizados=actualizados or 0,
            omitidos=omitidos or 0,
        )
        db.session.add(log)
        db.session.commit()
    except Exception as exc:
        logger.error("Error al registrar log de actividad: %s", exc)
