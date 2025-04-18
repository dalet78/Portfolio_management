import time as tm
from datetime import datetime, timedelta
from configuration import data_configuration_session
from support.logger import LoggerSingleton


def wait_for_precise_time(
        interval_minutes = data_configuration_session.INTERVAL_MINUTES,
        start_hour = data_configuration_session.START_SESSION_HOUR,
        start_minute = data_configuration_session.START_SESSION_MINUTE,
        end_hour = data_configuration_session.END_SESSION_HOUR,
        end_minute = data_configuration_session.END_SESSION_MINUTE,
        tolerance_seconds = data_configuration_session.TOLLERANCE_SECOND,
        max_wait_minutes = 15

    ):
    """
    Attende fino all'inizio della prossima candela valida (multiplo di `interval_minutes`)
    all'interno della finestra oraria `start_hour:start_minute` - `end_hour:end_minute`.

    ⚙️ Parametri:
    - interval_minutes: intervallo delle candele (es. 5 per candela a 5 minuti)
    - start_hour/minute, end_hour/minute: fascia oraria di validità (es. 15:30–22:00)
    - tolerance_seconds: se mancano pochi secondi, inizia subito
    - max_wait_minutes: se il prossimo orario è troppo lontano, inizia subito

    🚫 Se siamo fuori orario, aspetta fino al primo orario utile (anche il giorno dopo).
    """
    log = LoggerSingleton.get_logger()
    now = datetime.now()
    current_time = now.time()

    # ⏰ Costruisci oggetti datetime.time per la fascia oraria
    start_time = datetime(now.year, now.month, now.day, start_hour, start_minute).time()
    end_time = datetime(now.year, now.month, now.day, end_hour, end_minute).time()

    # 🎯 Siamo nella fascia oraria valida?
    if current_time < start_time:
        # 💤 Troppo presto → aspetta fino a start_time di oggi
        wait_until = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        log.log(f"🌅 Troppo presto, attendo l'inizio della sessione alle {start_time}", level="info")

    elif current_time >= end_time:
        # 🌙 Troppo tardi → aspetta fino a start_time di domani
        wait_until = (now + timedelta(days=1)).replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        log.log(f"🌙 Sessione chiusa. Aspetto domani alle {start_time}", level="info")

    else:
        # ✅ Siamo nella finestra giusta: calcola prossimo multiplo di `interval_minutes`
        next_minute = ((now.minute // interval_minutes) + 1) * interval_minutes
        next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=next_minute)
        wait_seconds = (next_time - now).total_seconds()

        # ⚠️ Se troppo vicino, esegui subito
        if wait_seconds < tolerance_seconds:
            log.log(f"⏱️ Meno di {tolerance_seconds}s alla prossima candela, parto subito.", level="info")
            return

        # ⚠️ Se troppo lontano (es. crash appena dopo), esegui subito
        if wait_seconds > max_wait_minutes * 60:
            log.log(f"⚠️ Prossima candela troppo lontana (> {max_wait_minutes} min), eseguo subito.", level="warning")
            return

        wait_until = next_time
        log.log(f"🕰️ Aspetto {wait_seconds:.1f}s per la prossima candela ({next_time.strftime('%H:%M:%S')})", level="info")

    # ⏳ Attesa vera e propria
    wait_seconds = (wait_until - datetime.now()).total_seconds()
    if wait_seconds > 0:
        tm.sleep(wait_seconds)

    log.log("🎯 Orario valido raggiunto. Avvio operazioni.", level="info")