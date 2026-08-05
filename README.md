# 👻 Phantom Picks Discord Bot

A Discord bot for the Phantom Picks sports picks community (MLB, NFL, NBA,
College Football, College Basketball). It builds and maintains the entire
server structure — categories, channels, roles, and permissions — and gives
you commands to post picks, post results, and keep a running model record.

Built with Python 3.11 and [discord.py](https://discordpy.readthedocs.io/).

---

## 1. What the bot does automatically

On every startup, the bot connects to your server and (idempotently — safe
to run repeatedly) creates/updates:

- **4 categories, in order:** 📋 INFORMATION, 📊 MODEL RECORD, 🆓 FREE PICKS, 💎 VIP MEMBERS ONLY
- **10 channels** inside them, with the exact read/post permissions described below
- **2 roles:** `Free Member` (auto-assigned to everyone who joins) and `Phantom Pro` (VIP — membership managed externally by Winible; the bot only grants channel access to whoever already has the role)
- **Pinned messages:** welcome message in #welcome, responsible-betting guide in #unit-sizing-and-responsible-betting, and the live model record in #model-record-and-pnl

You can also re-run this any time with `!setup` (admin only) — for example
after manually renaming something back, or on a brand-new server.

---

## 2. Repo structure

```
bot.py                 entry point — loads cogs, connects, runs setup on_ready
config.py              channel/category/role names, sport emoji map — edit here to rename things
sports.py               turns user-typed sport names into canonical codes
data_store.py            JSON persistence for the model record (data/record.json)
formatting.py            every outgoing message template (welcome, picks, results, record block)
checks.py                admin/owner-only command check
cogs/
  server_setup.py         builds categories/channels/roles/permissions, pinned messages, !setup
  picks.py                 !freepick, !vippick
  results.py                !result, !updaterecord, !setrecord, !setunits, !record
  moderation.py             #member-wins auto-react, #free-chat spam automod
  welcome.py                 on_member_join: role + welcome DM
  help.py                     !help
data/record.json          created automatically — do not hand-edit while the bot is running
```

---

## 3. Create your Discord bot & get a token

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and click **New Application**. Name it "Phantom Picks" (or whatever you like — this name is only shown in the portal).
2. In the left sidebar, click **Bot**. Click **Reset Token** (or **Add Bot** if this is a new app) and copy the token somewhere safe — you'll paste it into `.env` in a moment. Treat this token like a password; never commit it to git or share it publicly.
3. On that same Bot page, scroll to **Privileged Gateway Intents** and turn **ON**:
   - **SERVER MEMBERS INTENT** (needed to auto-assign the Free Member role and fire the welcome DM on join)
   - **MESSAGE CONTENT INTENT** (needed so the bot can read your `!` commands)
4. Under **Bot** settings, you can also set a display name/avatar for the bot ("Phantom Picks").

### Invite the bot to your server

1. In the left sidebar, click **OAuth2 -> URL Generator**.
2. Under **Scopes**, check `bot`.
3. Under **Bot Permissions**, the simplest reliable option is to check **Administrator** — this guarantees the bot can create categories/channels/roles and post everywhere, and it's also what makes "only I can post" channels work correctly (see note below). If you'd rather grant only what's needed, check: Manage Roles, Manage Channels, View Channels, Send Messages, Manage Messages, Embed Links, Add Reactions, Read Message History.
4. Copy the generated URL at the bottom, open it in your browser, pick your server, and authorize it.

> **Why Administrator matters for "only I can post" channels:** the bot locks
> those channels by denying `@everyone` (and both roles) permission to send
> messages. Discord's permission system lets anyone with the **Administrator**
> permission bypass those overwrites automatically — so as long as *you* (the
> server owner) have Administrator, you can still post there even though the
> channel itself denies everyone else. You don't need a special role for
> yourself; server owners have this by default.

### Fix the role hierarchy (important)

After inviting the bot, go to **Server Settings -> Roles** and drag the
bot's own role **above** `Free Member` and `Phantom Pro`. Discord only lets
a bot manage/assign roles that sit below its own highest role — if you skip
this, role assignment (including the automatic Free Member role on join)
will silently fail.

---

## 4. Local setup

```bash
git clone <this-repo-url>
cd DiscordBot
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# now edit .env and paste in your DISCORD_TOKEN (and your real WINIBLE_LINK)

python bot.py
```

On first run, watch the console — you should see log lines like
`Created category: 📋 INFORMATION`, `Created role: Free Member`, etc. Check
your Discord server: the full structure should now exist, and #welcome /
#unit-sizing-and-responsible-betting / #model-record-and-pnl should each
have one pinned message.

---

## 5. Command reference

| Command | Who | What it does |
|---|---|---|
| `!freepick [sport] [away] [home] [picked] [kalshi price] [probability]` | admin | Posts a formatted pick to #free-daily-picks |
| `!vippick [sport] [away] [home] [picked] [kalshi price] [probability] [edge] [HIGH\|MEDIUM] [bet size] [reason]` | admin | Posts a formatted pick to #vip-picks |
| `!result [W\|L] [sport] [away] [home] [picked] [amount] [notes]` | admin | Posts to #free-results + #vip-results, updates the pinned record |
| `!updaterecord [W\|L] [sport]` | admin | Manually adjusts overall + sport record only |
| `!setrecord [W-L]` | admin | Manually overwrites the overall record, e.g. `!setrecord 45-30` |
| `!setunits [+/-X]` | admin | Sets the units total shown in the pinned record |
| `!record` | anyone | Replies with the current model record block |
| `!setup` | admin | Re-runs full server provisioning |
| `!help` | anyone | Lists all commands with syntax/examples |

**"admin"** = the server owner, or anyone with the Administrator permission
(optionally also `BOT_OWNER_ID` in `.env`, if you want to grant command
access to an account that isn't a full server admin).

**Quoting:** wrap any argument containing spaces in double quotes — team
names, `"College Football"` / `"College Basketball"`, and the VIP pick
reason / result notes. Example:

```
!freepick MLB "New York Yankees" "Boston Red Sox" "Boston Red Sox" 62 68

!vippick NFL "Buffalo Bills" "Miami Dolphins" "Buffalo Bills" 58 65 7 HIGH 75 "Dolphins missing 2 starting OL, model sees pressure rate spiking"

!result W MLB "New York Yankees" "Boston Red Sox" "Boston Red Sox" 46 "Bullpen shut the door in the 8th, exactly as modeled"
```

Sport aliases accepted: `MLB`, `NFL`, `NBA`, `CFB`/`"College Football"`, `CBB`/`"College Basketball"` (edit `SPORT_ALIASES` in `config.py` to add more).

**Confidence-tier tracking:** the model record's HIGH/MEDIUM confidence
buckets only update when `!result` can match the game to a pick that was
posted via `!vippick` (which is the only command that takes a confidence
tier). If you run `!result` for a game with no matching pending `!vippick`
pick (e.g. a free-only pick, or the bot restarted and lost the in-memory
match), the overall/sport/today records still update — only the confidence
buckets are skipped.

---

## 6. Data persistence

All record data lives in `data/record.json`, written atomically on every
update. It's gitignored on purpose — it's live data, not code. **On a
normal VPS or your own machine, this just works.** On Railway/Render, see
the persistence notes in the deployment steps below — without a persistent
volume/disk, a redeploy will reset your record back to 0-0.

---

## 7. Hosting for free — Railway (recommended)

Railway runs the bot as a background worker with no HTTP port required,
which fits this project well.

1. Push this repo to your own GitHub repository (if you haven't already).
2. Go to [railway.app](https://railway.app), sign in, click **New Project -> Deploy from GitHub repo**, and pick your repo.
3. In the new service's **Variables** tab, add:
   - `DISCORD_TOKEN` = your bot token
   - `WINIBLE_LINK` = your real upgrade link
   - (optional) `BOT_OWNER_ID`
4. In **Settings -> Deploy**, set the **Start Command** to `python bot.py` (Railway will also honor the included `Procfile`).
5. **Persistence:** by default Railway's filesystem is ephemeral across redeploys. Add a **Volume** (Settings -> Volumes) mounted at `/app/data` so `data/record.json` survives redeploys and restarts.
6. Deploy. Check the **Deployments -> Logs** tab for the same startup log lines you saw locally.

Railway's free trial credit is enough to run a small bot like this 24/7 for
a good while; once it runs out you'll need a paid plan to keep it always-on.

---

## 8. Hosting for free — Render

Render's **free tier only supports Web Services** (something that binds to
a port), not standalone background workers — so we use the included
`keep_alive.py` to satisfy that requirement.

1. Push this repo to GitHub.
2. On [render.com](https://render.com), click **New -> Web Service**, connect your repo.
3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `python bot.py`
5. **Environment variables:**
   - `DISCORD_TOKEN` = your bot token
   - `WINIBLE_LINK` = your real upgrade link
   - `RENDER_KEEP_ALIVE` = `1` (tells `bot.py` to start the tiny Flask server in `keep_alive.py` so Render has a port to bind to)
   - (optional) `BOT_OWNER_ID`
6. Deploy. Render's free web services spin down after ~15 minutes of no HTTP traffic and spin back up on the next request — that will disconnect your bot. Use a free uptime pinger (e.g. UptimeRobot) to hit your Render URL every few minutes and keep it awake.
7. **Persistence:** Render's free tier has an ephemeral filesystem — `data/record.json` will reset to 0-0 on every redeploy/restart. To keep permanent record history on Render you need a paid plan with a persistent disk attached at `/app/data`. If you want true free 24/7 uptime **with** persistence, Railway (above) is the better fit.

---

## 9. Post-launch verification checklist

Run through this after first deploy:

- [ ] `!help` responds with the full command list
- [ ] `!record` responds with the record block (all zeros on a fresh install)
- [ ] `!freepick MLB "Away Team" "Home Team" "Home Team" 55 60` posts correctly formatted to #free-daily-picks with the ⚾ emoji
- [ ] `!vippick MLB "Away Team" "Home Team" "Home Team" 55 60 5 HIGH 50 "test"` posts correctly to #vip-picks
- [ ] `!result W MLB "Away Team" "Home Team" "Home Team" 50 "test"` posts to both #free-results and #vip-results, and the pinned message in #model-record-and-pnl updates (record, MLB record, and HIGH confidence record all increment)
- [ ] As a **non-admin** test account: can post in #free-chat and #member-wins; **cannot** post in #welcome, #unit-sizing-and-responsible-betting, #model-record-and-pnl, #free-daily-picks, #free-results
- [ ] As that same non-admin account: the **💎 VIP MEMBERS ONLY** category (and its 3 channels) is completely invisible in the channel list
- [ ] Give that test account the `Phantom Pro` role manually (simulating what Winible will do) — the VIP category should now appear, with read-only access to #vip-picks/#vip-results and full post access to #vip-chat
- [ ] Post a message in #member-wins — the bot reacts with 👻
- [ ] Join the server with a fresh test account — you receive the welcome DM and are auto-assigned `Free Member`
- [ ] Restart the bot — no duplicate categories/channels/roles are created, and the pinned messages are not re-posted (only edited/refreshed)

**On the VIP role:** `Phantom Pro` is created by the bot if it doesn't
already exist, ready for Winible's Discord integration to assign/remove it.
The bot does not (and should not) contain any commands for granting or
revoking VIP — that's entirely Winible's job. The bot only reacts to the
role already being present on a member.

---

## 10. Troubleshooting

- **Bot can't create channels/roles / role assignment silently fails:** the bot's role isn't above `Free Member`/`Phantom Pro` in Server Settings -> Roles — see step 3 above.
- **"Missing Access" errors in logs:** double check the bot was invited with the Administrator permission (or the full granular list in step 3) and that Privileged Gateway Intents are enabled in the Developer Portal.
- **`!freepick`/`!vippick`/`!result` say "Missing or invalid argument":** you likely forgot to quote a multi-word argument (team name, sport, or notes/reason) — see the quoting examples in section 5.
- **Record resets after every deploy:** you're on a host without a persistent volume/disk attached to `data/` — see the persistence notes in sections 7/8.
- **Welcome DM never arrives:** the member has "Allow direct messages from server members" turned off in their Discord privacy settings — the bot logs this and continues without erroring; there's nothing to fix on the bot side.

⚠️ Not financial advice. Bet responsibly.
