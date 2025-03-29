import time as tm
from datetime import datetime, time, timedelta
from configuration import data_configuration_session
from support.logger import Logger


def wait_for_precise_time(log:Logger,  target_time=data_configuration_session.START_SESSION):
    """Attende fino all'orario specificato."""
    now = datetime.now()

    # Assicurati che `target_time` sia un oggetto datetime.time
    if isinstance(target_time, datetime):
        target_time = tm.time()  # Converti in datetm.time

    target_datetime = now.replace(hour=target_time.hour, minute=target_time.minute, second=1, microsecond=0)

    if now > target_datetime:
        target_datetime += timedelta(days=1)  # Se l'orario è già passato oggi, impostalo per domani

    wait_seconds = (target_datetime - now).total_seconds()

    log.log(f"Wait {wait_seconds:.2f} seconds to start at {target_time}.", level="info")

    if wait_seconds > 0:
        tm.sleep(wait_seconds)  # ✅ Ora è un numero corretto

    log.log("Target time reached. Starting execution.", level="info")