import logging
import os
import time
from datetime import datetime
from threading import Lock

from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from services.auto_etl_service import process_new_csvs
from services.log_service import registrar_log

load_dotenv()

logger = logging.getLogger(__name__)

bot_lock = Lock()

bot_status = {
    "running": False,
    "last_run": None,
    "last_error": None,
}


def descargar_archivo():
    if not bot_lock.acquire(blocking=False):
        logger.warning("El bot ya está en ejecución — omitiendo invocación duplicada.")
        return False

    bot_status["running"] = True
    bot_status["last_error"] = None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(os.getenv("URL_LOGIN"))
            logger.info("[BOT] Iniciando sesión en el LOS...")
            page.fill("input[name='vUser']", os.getenv("USER"))
            page.fill("input[name='vPassword']", os.getenv("PASSWORD"))
            page.click("input[type='submit']")
            time.sleep(5)

            if page.locator(
                "text='80003 3 - Acceso negado. El usuario ya esta dentro de la aplicacion. Reintente.'"
            ).is_visible():
                page.reload()
                time.sleep(5)

            logger.info("[BOT] Navegando al módulo de interfaces...")
            header_frame = page.frame(url=os.getenv("FRAME_MENU_SUPERIOR"))
            header_frame.locator("label.stTopText", has_text="Financiamiento").click()

            header_frame2 = page.frame(url=os.getenv("FRAME_MENU_LATERAL"))
            header_frame2.locator("label.stMenuText", has_text="Interfaces").click()
            header_frame2.locator("label.stMenuOptText", has_text="Procesos").click()

            header_frame3 = page.frame(url=os.getenv("FRAME_MENU_CENTRAL"))
            header_frame3.locator("#iProcessId").select_option(value="54")
            header_frame3.locator("#iProcessId").dispatch_event("change")

            today = datetime.today()
            mes_anterior = today - relativedelta(month=1)
            header_frame3.locator("input[name='vDateMinD']").fill(mes_anterior.strftime("%d"))
            header_frame3.locator("input[name='vDateMinM']").fill(mes_anterior.strftime("%m"))
            header_frame3.locator("input[name='vDateMinA']").fill(mes_anterior.strftime("%Y"))

            header_frame3.click("input[name='btExecute']")
            time.sleep(15)
            header_frame3.click("input[name='btRefresh']")
            time.sleep(5)

            radio_buttons = header_frame3.locator("input[name='rdSel']")
            radio_buttons.first.click()

            with page.expect_download() as download_info:
                header_frame3.locator("label.stSubMenuOptText", has_text="Descargar Archivo").click()
            download = download_info.value

            base_path = os.getenv("DATA_ETL_PATH")
            os.makedirs(base_path, exist_ok=True)
            filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
            full_path = os.path.join(base_path, filename)
            download.save_as(full_path)
            logger.info("[BOT] Archivo guardado: %s", full_path)

            header_frame.click("text=Salir")
            page.context.close()

            logger.info("[BOT] Ejecutando ETL...")
            process_new_csvs(base_path)

            bot_status["last_run"] = datetime.now()
            registrar_log(tipo="manual", estado="exito", mensaje="Descarga y ETL completados")
            return True

    except Exception as exc:
        bot_status["last_error"] = str(exc)
        logger.error("[BOT] Error durante la ejecución: %s", exc)
        registrar_log(tipo="manual", estado="error", mensaje=str(exc))
        raise

    finally:
        bot_status["running"] = False
        bot_lock.release()
