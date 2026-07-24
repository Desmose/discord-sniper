import os
import time
import random
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
DISCORD_PASSWORD = os.environ["DISCORD_PASSWORD"]
CANDIDATES_FILE = os.environ.get("CANDIDATES_FILE", "candidates.txt")
POLL_INTERVAL_MIN = float(os.environ.get("POLL_INTERVAL_MIN_SECONDS", "75"))
POLL_INTERVAL_MAX = float(os.environ.get("POLL_INTERVAL_MAX_SECONDS", "105"))
CONTINUE_AFTER_SUCCESS = os.environ.get("CONTINUE_AFTER_SUCCESS", "false").lower() == "true"

NTFY_SERVER = os.environ.get("NTFY_SERVER", "https://ntfy.sh")
NTFY_TOPIC = os.environ["NTFY_TOPIC"]

ACCOUNT_LABEL = os.environ.get("ACCOUNT_LABEL", "") or "default"
PREFIX = f"[{ACCOUNT_LABEL}] "

STATUS_DIR = Path(os.environ.get("STATUS_DIR", "/app/status"))
STATUS_FILE = STATUS_DIR / f"{ACCOUNT_LABEL}.json"

API_BASE = "https://discord.com/api/v10"

logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s [%(levelname)s] {PREFIX}%(message)s",
)
log = logging.getLogger("sniper")


def notify(title: str, message: str, priority: str = "default"):
    title = PREFIX + title
    try:
        requests.post(
            f"{NTFY_SERVER}/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers={"Title": title, "Priority": priority},
            timeout=10,
        )
    except requests.RequestException as e:
        log.error(f"Echec envoi notif ntfy: {e}")


def write_status(**fields):
    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "account": ACCOUNT_LABEL,
        "last_update": datetime.now(timezone.utc).isoformat(),
        **fields,
    }
    tmp = STATUS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload))
    tmp.replace(STATUS_FILE)


def load_candidates() -> list[str]:
    path = Path(CANDIDATES_FILE)
    if not path.exists():
        raise FileNotFoundError(f"{CANDIDATES_FILE} introuvable")
    names = [line.strip() for line in path.read_text().splitlines()]
    return [n for n in names if n and not n.startswith("#")]


def save_candidates(names: list[str]):
    Path(CANDIDATES_FILE).write_text("\n".join(names) + "\n")


def try_claim(username: str) -> str:
    """Retourne 'success', 'taken', 'ratelimited', 'captcha', ou 'error'."""
    resp = requests.patch(
        f"{API_BASE}/users/@me",
        headers={
            "Authorization": DISCORD_TOKEN,
            "Content-Type": "application/json",
        },
        json={"username": username, "password": DISCORD_PASSWORD},
        timeout=15,
    )

    if resp.status_code == 200:
        return "success"

    if resp.status_code == 429:
        retry_after = resp.json().get("retry_after", 30)
        log.warning(f"Rate limited, pause {retry_after}s")
        time.sleep(float(retry_after) + 2)
        return "ratelimited"

    if resp.status_code == 401:
        log.error("Token invalide ou expire (401). Arret.")
        notify("Sniper: token invalide", f"Le token du compte semble expire.", priority="high")
        raise SystemExit(1)

    body = {}
    try:
        body = resp.json()
    except ValueError:
        pass

    if "captcha_key" in body or "captcha_sitekey" in body:
        log.warning(f"Captcha requis pour '{username}'. Intervention manuelle necessaire.")
        notify(
            "Sniper: captcha requis",
            f"Discord demande un captcha pour tenter '{username}'. Impossible d'automatiser, connecte-toi manuellement si besoin.",
            priority="high",
        )
        return "captcha"

    if resp.status_code == 400:
        return "taken"

    log.error(f"Reponse inattendue ({resp.status_code}): {body}")
    return "error"


def main():
    candidates = load_candidates()
    total = len(candidates)
    if not candidates:
        log.error("Aucun pseudo candidat dans le fichier.")
        return

    log.info(f"Demarrage, {total} candidats.")
    notify("Sniper demarre", f"Surveillance de {total} pseudo(s).")

    attempts = 0
    found = []
    write_status(state="starting", current=None, last_result=None,
                 attempts_total=0, remaining=total, total_candidates=total, found=found)

    captcha_paused = False

    while candidates and not captcha_paused:
        for name in list(candidates):
            write_status(state="running", current=name, last_result=None,
                         attempts_total=attempts, remaining=len(candidates),
                         total_candidates=total, found=found)

            result = try_claim(name)
            attempts += 1

            if result == "success":
                log.info(f"SUCCES: '{name}' recupere !")
                notify("Pseudo recupere !", f"'{name}' est maintenant ton pseudo Discord.", priority="urgent")
                candidates.remove(name)
                save_candidates(candidates)
                found.append(name)
                write_status(state="running", current=name, last_result=result,
                             attempts_total=attempts, remaining=len(candidates),
                             total_candidates=total, found=found)
                if not CONTINUE_AFTER_SUCCESS:
                    log.info("Arret (CONTINUE_AFTER_SUCCESS=false).")
                    write_status(state="stopped_success", current=name, last_result=result,
                                 attempts_total=attempts, remaining=len(candidates),
                                 total_candidates=total, found=found)
                    return

            elif result == "captcha":
                captcha_paused = True
                write_status(state="captcha_paused", current=name, last_result=result,
                             attempts_total=attempts, remaining=len(candidates),
                             total_candidates=total, found=found)
                break

            elif result == "taken":
                log.info(f"'{name}' toujours pris.")
                write_status(state="running", current=name, last_result=result,
                             attempts_total=attempts, remaining=len(candidates),
                             total_candidates=total, found=found)

            else:
                write_status(state="running", current=name, last_result=result,
                             attempts_total=attempts, remaining=len(candidates),
                             total_candidates=total, found=found)

            time.sleep(random.uniform(POLL_INTERVAL_MIN, POLL_INTERVAL_MAX))

    if not candidates:
        log.info("Liste epuisee, aucun candidat restant.")
        write_status(state="exhausted", current=None, last_result=None,
                     attempts_total=attempts, remaining=0, total_candidates=total, found=found)
    elif captcha_paused:
        log.info("En pause suite a un captcha. Relance le conteneur apres verification manuelle.")


if __name__ == "__main__":
    main()
