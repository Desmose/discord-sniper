# discord-sniper

Bot qui surveille une liste de pseudos Discord et tente automatiquement de les recuperer des qu'ils se liberent, via l'API Discord (`PATCH /users/@me`). Inclut un dashboard web pour suivre l'etat en temps reel.

> **Attention** : automatiser des actions sur un compte utilisateur Discord (par opposition a un bot officiel) va a l'encontre des [conditions d'utilisation](https://discord.com/terms) de Discord et peut entrainer la suspension du compte. A utiliser a tes risques, sur un compte que tu es pret a perdre.

## Fonctionnement

- Le script lit `candidates.txt` (un pseudo par ligne) et tente de renommer le compte vers chaque pseudo, a intervalle aleatoire (`POLL_INTERVAL_MIN/MAX_SECONDS`).
- En cas de succes, une notification [ntfy](https://ntfy.sh) est envoyee et le pseudo est retire de la liste.
- Si Discord demande un captcha, le bot se met en pause (redemarrage manuel necessaire) : resoudre un captcha via l'API necessite un token hCaptcha valide, ce que ce projet ne fournit pas.
- Le dashboard (`/dashboard`) lit les fichiers de statut dans `status/` et les affiche sur `http://localhost:8080`.

## Installation

```bash
cp .env.example .env
cp candidates.example.txt candidates.txt
```

Remplis `.env` :
- `DISCORD_TOKEN` : recupere depuis l'onglet Reseau du navigateur (connecte-toi, ouvre les devtools, cherche une requete vers `/api/v9/users/@me` ou similaire, copie le header `Authorization`).
- `DISCORD_PASSWORD` : mot de passe du compte (l'API Discord l'exige pour valider un changement de pseudo).
- `NTFY_TOPIC` : un nom de topic unique/aleatoire sur ntfy.sh (n'importe qui connaissant le topic peut lire tes notifications).

Edite `candidates.txt` avec les pseudos a surveiller.

## Lancement

```bash
docker compose up -d --build
```

Dashboard disponible sur `http://localhost:8080`.

## Configuration

| Variable | Description | Defaut |
|---|---|---|
| `DISCORD_TOKEN` | Token du compte | - |
| `DISCORD_PASSWORD` | Mot de passe du compte | - |
| `CANDIDATES_FILE` | Chemin du fichier de candidats | `candidates.txt` |
| `POLL_INTERVAL_MIN_SECONDS` / `POLL_INTERVAL_MAX_SECONDS` | Intervalle entre tentatives | `60` / `90` |
| `CONTINUE_AFTER_SUCCESS` | Continue apres un succes | `false` |
| `NTFY_SERVER` / `NTFY_TOPIC` | Notifications | `https://ntfy.sh` / - |
| `ACCOUNT_LABEL` | Nom affiche dans les logs/dashboard | `default` |

## Limitations connues

- Discord peut exiger un captcha (hCaptcha) sur les tentatives repetees de changement de pseudo depuis l'API. Ce projet ne l'automatise pas ; le bot se contente de te notifier et de se mettre en pause.
- Un intervalle trop court (quelques secondes) augmente le risque de rate-limit et de captcha.
