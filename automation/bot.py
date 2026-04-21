from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from datetime import datetime
from dateutil.relativedelta import relativedelta
from services.auto_etl_service import process_new_csvs
from threading import Lock
import time
import os


load_dotenv()

bot_lock = Lock()

bot_status = {
    "running": False,
    "last_run": None,
    "last_error": None
}


def descargar_archivo():
    
    if not bot_lock.acquire(blocking=False):
        print("El bot ya está en ejecución.")
        return False
    
    bot_status["running"] = True
    bot_status["last_error"] = None
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Login
            page.goto(os.getenv('URL_LOGIN'))

            print("[BOT] Iniciando sesión...")
            page.fill("input[name='vUser']", os.getenv('USER'))
            page.fill("input[name='vPassword']", os.getenv('PASSWORD'))
            page.click("input[type='submit']")
            time.sleep(5)

            if page.locator("text='80003 3 - Acceso negado. El usuario ya esta dentro de la aplicacion. Reintente.'").is_visible():  # <span id="lblError" class="stLblErrLog">80003 3 - Acceso negado. El usuario ya esta dentro de la aplicacion. Reintente.</span>
                page.reload()
                time.sleep(5)

            # Ejecutar la creacion de un reporte de desembolso (dia de hoy)
            print("[BOT] Navegando por la aplicación...")
            header_frame = page.frame(url=os.getenv('FRAME_MENU_SUPERIOR'))
            header_frame.locator("label.stTopText", has_text="Financiamiento").click()

            header_frame2 = page.frame(url=os.getenv('FRAME_MENU_LATERAL'))
            header_frame2.locator("label.stMenuText", has_text="Interfaces").click()

            header_frame2.locator("label.stMenuOptText", has_text="Procesos").click()

            urlProcesos = os.getenv('FRAME_MENU_CENTRAL')
            header_frame3 = page.frame(url=urlProcesos)
            header_frame3.locator("#iProcessId").select_option(value="54")
            header_frame3.locator("#iProcessId").dispatch_event("change")

            # Selccion de fechas varias
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

            # Use a context manager to wait for the download while performing the click
            with page.expect_download() as download_info:
                header_frame3.locator("label.stSubMenuOptText", has_text="Descargar Archivo").click()
            download = download_info.value

            base_path = os.getenv("DATA_ETL_PATH")
            os.makedirs(base_path, exist_ok=True)

            print("[BOT] Iniciando descarga...")
            filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
            full_path = os.path.join(base_path, filename)

            download.save_as(full_path)
            print("[BOT] Archivo guardado:", full_path)
            header_frame.click("text=Salir")
            page.context.close()

            base_path = os.getenv("DATA_ETL_PATH")
            print("[BOT] Ejecutando ETL...")
            process_new_csvs(base_path)
            
            bot_status["last_run"] = datetime.now()
            return True
    
    except Exception as e:
        bot_status["last_error"] = str(e)
        raise e
    
    finally:
        bot_status["running"] = False
        bot_lock.release()

    return 0
