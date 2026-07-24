# discord-sniper

Petit bot qui surveille une liste de pseudos Discord et essaie de les prendre des qu'ils se liberent (via `PATCH /users/@me`). Avec un mini dashboard web pour voir ce qui se passe.

Automatiser un compte user Discord c'est contre leurs TOS et ca peut faire ban le compte. Fais-le sur un compte jetable, a tes risques.

## Comment ca marche

Le script lit `candidates.txt` (un pseudo par ligne) et tente de renommer le compte vers chacun, avec un delai aleatoire entre les essais. Si ca passe, tu recois une notif [ntfy](https://ntfy.sh) et le pseudo est retire de la liste.

Si Discord demande un captcha, le bot se met en pause (faut le relancer a la main). Resoudre le captcha via l'API demanderait un token hCaptcha valide, que je ne fournis pas ici.

Le dashboard tourne sur `http://localhost:8080` et lit les fichiers de statut dans `status/`.

## Setup

```bash
cp .env.example .env
cp candidates.example.txt candidates.txt
```

Puis remplis `.env` :
- `DISCORD_TOKEN` : dans le navigateur, devtools -> onglet Reseau -> une requete vers `users/@me` -> copie le header `Authorization`
- `DISCORD_PASSWORD` : le mot de passe du compte (Discord le demande pour valider le changement de pseudo)
- `NTFY_TOPIC` : un nom de topic random sur ntfy.sh (attention, qui connait le topic peut lire tes notifs)

Mets tes pseudos dans `candidates.txt`, un par ligne.

## Lancer

```bash
docker compose up -d --build
```

Le reste des reglages (intervalle entre essais, comportement apres un succes, etc.) est dans `.env.example`, c'est commente.

## A savoir

Discord finit souvent par exiger un captcha si tu spam les tentatives depuis l'API. Garde un intervalle pas trop court (genre 60-90s) pour limiter ca, mais y'a pas de garantie.
