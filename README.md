# NOVA Voice AI

NOVA is a local Streamlit assistant with voice controls, Google sign-in, Gmail
read/send features, and optional Telegram messaging.

## Requirements

- Python 3.11 or newer
- Google Chrome or Microsoft Edge for browser speech recognition
- A Google OAuth client configuration for Google sign-in and Gmail
- A Telegram bot token and chat ID if you want to use Telegram

## Run locally

From the project directory, create and activate a virtual environment, then
install the dependencies and start Streamlit:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run nova_app.py
```

Open [http://localhost:5000](http://localhost:5000). Port 5000 is configured in
`.streamlit/config.toml` to match the local Google OAuth callback. If you change
the port, update the OAuth redirect URI as well.

## Google sign-in and Gmail

1. In Google Cloud Console, create or select a project and enable the Gmail API.
2. Configure the OAuth consent screen. If the app is in testing mode, add the
   Google account you will use as a test user.
3. Create an OAuth client and save its downloaded client configuration as
   `credentials.json` in the project directory. The current setup expects a
   client file with an authorized redirect URI of
   `http://localhost:5000/`.
4. Start NOVA and choose **Continue with Google**. Google handles the password
   and consent flow; NOVA does not ask for your Google password.
5. After authorization, Gmail features use the granted read, send, and modify
   scopes. To disconnect, use **Settings → Gmail → Disconnect**.

The OAuth token is stored locally in `token.pickle`. Treat it as a credential:
do not commit or share it. Revoke NOVA's access from your Google Account
security settings if the token may have been exposed.

## Optional Telegram configuration

Create a bot with Telegram's BotFather, then create a `nova.env` file in the
project directory (or set these environment variables in your shell):

```dotenv
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

Send `/start` to the bot before loading messages. NOVA checks the Telegram
connection in **Settings → Services**. Without both values, Telegram features
remain unavailable.

`OPENAI_API_KEY` (or the legacy `open_ai_key` variable) can be set in
`nova.env` to enable OpenAI email summaries. Without it, NOVA uses its built-in
summary fallback.

## Voice controls

After signing in, open the **Voice** page and select **Start NOVA**. Allow
microphone access when the browser asks. Speech recognition support varies by
browser; use current Chrome or Edge and check the browser's microphone
permission if voice input does not start. The app must be served from localhost
or another secure browser context for microphone access.

Example commands include:

- `load emails`, `read email`, `summarize email`
- `send email`
- `load telegram`, `read telegram`, `send telegram`
- `open settings`, `open contacts`, `go home`
- `set pin` followed by four digits

NOVA may require the configured PIN before protected send/read actions. Voice
sign-in is not supported; authenticate with Google or use the optional local
account form.

## Docker

Build the image:

```powershell
docker build -t nova-assistant .
```

Run it with the OAuth client file and environment file mounted at runtime:

```powershell
docker run --rm -p 5000:5000 `
  -v "${PWD}\credentials.json:/app/credentials.json:ro" `
  -v "${PWD}\nova.env:/app/nova.env:ro" `
  nova-assistant
```

Then open [http://localhost:5000](http://localhost:5000). Do not copy OAuth
client files, tokens, or environment files into the Docker image.

## Security notes

- Never commit `credentials.json`, `nova.env`, or `token.pickle`. The repository
  ignore rules cover these files for new, untracked files; if any are already
  tracked by Git, remove them from version control and rotate/revoke the
  exposed credentials.
- The local account form is a development convenience, not a production
  identity system. User accounts and PINs are held in Streamlit session state,
  not a persistent account database.
- Do not expose this local app to the public internet without adding
  production-grade authentication, session management, and secret handling.
