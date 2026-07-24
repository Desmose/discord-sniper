# discord-sniper

Script that watches a list of Discord usernames and tries to grab them as soon as they free up (via `PATCH /users/@me`). Comes with a web dashboard to follow the progress.

Automating a Discord user account goes against their TOS and can get the account banned. Do it on a throwaway account, at your own risk.

## How it works

The script reads `candidates.txt` (one username per line) and tries to rename the account to each of them, with a random delay between attempts. If it goes through, you get an [ntfy](https://ntfy.sh) notification and the username is removed from the list.

If Discord asks for a captcha, the bot pauses (you have to restart it manually). Solving the captcha through the API would need a valid hCaptcha token, which I don't provide here.

The dashboard runs on `http://localhost:8080` and reads the status files in `status/`.

## Setup

```bash
cp .env.example .env
cp candidates.example.txt candidates.txt
```

Then fill in `.env`:
- `DISCORD_TOKEN`: in the browser, devtools -> Network tab -> a request to `users/@me` -> copy the `Authorization` header
- `DISCORD_PASSWORD`: the account password (Discord requires it to validate the username change)
- `NTFY_TOPIC`: a random topic name on ntfy.sh (careful, anyone who knows the topic can read your notifications)

Put your usernames in `candidates.txt`, one per line.

## Run

```bash
docker compose up -d --build
```

The rest of the settings (delay between attempts, behavior after a success, etc.) are in `.env.example`, they're commented.

## Good to know

Discord often ends up requiring a captcha if you spam attempts through the API. Keep the delay not too short (like 60-90s) to limit that, but there's no guarantee.
