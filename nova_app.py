"""
NOVA - 100% Voice Controlled AI Assistant
Run: streamlit run nova_app.py
Install: pip install -r requirements.txt
Google OAuth callback: http://localhost:5000/

EVERYTHING by voice:
  - Voice login (say your name)
  - Voice PIN entry
  - Voice compose & send email
  - Voice send Telegram
  - Voice read emails aloud
  - Voice navigation to any page
  - Voice contacts, settings, admin
"""
import streamlit as st
st.set_page_config(
    page_title="NOVA Voice AI", page_icon="🎙️",
    layout="wide", initial_sidebar_state="expanded"
)

import os, re, json, base64, pickle, datetime, hashlib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / "nova.env")

try:    import requests as _req;  REQUESTS_OK = True
except: REQUESTS_OK = False

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GOOGLE_OK = True
except: GOOGLE_OK = False

try:    import openai as _oai;  OPENAI_OK = True
except: OPENAI_OK = False

# ── Config ────────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")
OPENAI_API_KEY     = os.environ.get("OPENAI_API_KEY") or os.environ.get("open_ai_key", "")
CREDENTIALS_FILE   = BASE_DIR / "credentials.json"
TOKEN_FILE         = BASE_DIR / "token.pickle"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]

LANG_NAMES = {
    "en":"English","hi":"Hindi","te":"Telugu","ta":"Tamil","kn":"Kannada","bn":"Bengali",
    "es":"Spanish","fr":"French","de":"German","pt":"Portuguese","ar":"Arabic",
    "zh":"Chinese","ja":"Japanese","ru":"Russian","ko":"Korean","it":"Italian",
}
LOCALES = {
    "en":"en-US","hi":"hi-IN","te":"te-IN","ta":"ta-IN","kn":"kn-IN","bn":"bn-IN",
    "es":"es-ES","fr":"fr-FR","de":"de-DE","pt":"pt-PT","ar":"ar-SA","zh":"zh-CN",
    "ja":"ja-JP","ru":"ru-RU","ko":"ko-KR","it":"it-IT",
}

# ── Session state ─────────────────────────────────────────────────────────────
_DEF = {
    "page": "Voice", "lang": "en",
    "logged_in": False, "auth_provider": "", "user_name": "", "user_email": "",
    "user_pin": "", "pin_set": False,
    "local_users": {},
    "contacts": [
        {"name":"Rahul","email":"rahul@example.com","phone":""},
        {"name":"Priya","email":"priya@example.com","phone":""},
    ],
    "activity_log": [],
    "stats": {"emails_sent":0,"telegrams_sent":0,"logins":0,"voice_cmds":0},
    "emails": [], "tg_messages": [],
    "email_summaries": {}, "reply_suggestions": {},
    "compose_to":"","compose_sub":"","compose_body":"",
    # bridge
    "_bridge_in":  "",
    "_bridge_last":"",
    "_bridge_out": "",   # Python → JS response (NOVA speaks this)
    "_bridge_nav": "",   # Python → JS navigation signal
    "pin_verified_for": set(),
}
for k,v in _DEF.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
html,body,.stApp{background:#07071a!important;color:#e8e8ff!important;}
section[data-testid="stSidebar"]{background:#0c0c24!important;border-right:1px solid rgba(108,99,255,.2)!important;}
.stButton>button{background:linear-gradient(135deg,#6c63ff,#8b5cf6)!important;color:#fff!important;
  border:none!important;border-radius:10px!important;font-weight:700!important;}
.stButton>button[kind="secondary"]{background:rgba(255,255,255,.06)!important;
  color:#e8e8ff!important;border:1px solid rgba(255,255,255,.1)!important;}
.stTextInput>div>div>input,.stTextArea>div>div>textarea,.stSelectbox>div>div{
  background:rgba(255,255,255,.06)!important;border:1px solid rgba(255,255,255,.12)!important;
  color:#e8e8ff!important;border-radius:8px!important;}
.stTabs [data-baseweb="tab-list"]{background:#11112e!important;border-radius:10px!important;padding:4px!important;}
.stTabs [data-baseweb="tab"]{color:#7a7a9a!important;border-radius:8px!important;font-weight:600!important;}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,#6c63ff,#8b5cf6)!important;color:#fff!important;}
[data-testid="metric-container"]{background:rgba(255,255,255,.04)!important;
  border:1px solid rgba(255,255,255,.09)!important;border-radius:14px!important;padding:14px!important;}
[data-testid="stExpander"]{background:rgba(255,255,255,.03)!important;
  border:1px solid rgba(255,255,255,.09)!important;border-radius:10px!important;}
hr{border-color:rgba(255,255,255,.07)!important;}
h1,h2,h3,h4,p,li,label{color:#e8e8ff!important;}
.stMarkdown p{color:#e8e8ff!important;}
section[data-testid="stSidebar"] *{color:#e8e8ff!important;}
.hscroll{display:flex;gap:12px;overflow-x:auto;padding:8px 2px 12px;
  scrollbar-width:thin;scrollbar-color:#6c63ff33 transparent;}
.hscroll::-webkit-scrollbar{height:4px;}
.hscroll::-webkit-scrollbar-thumb{background:#6c63ff55;border-radius:4px;}
.ecard{min-width:220px;max-width:220px;background:rgba(108,99,255,.08);
  border:1px solid rgba(108,99,255,.2);border-radius:12px;padding:12px;flex-shrink:0;}
.ecard .ef{font-size:11px;color:#a78bfa;font-weight:700;margin-bottom:4px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.ecard .es{font-size:12px;color:#e8e8ff;font-weight:600;margin-bottom:4px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.ecard .eb{font-size:11px;color:#7a7a9a;overflow:hidden;}
.tcard{min-width:200px;max-width:200px;background:rgba(0,136,204,.08);
  border:1px solid rgba(0,136,204,.2);border-radius:12px;padding:12px;flex-shrink:0;}
.tcard .tf{font-size:11px;color:#00aaff;font-weight:700;margin-bottom:4px;}
.tcard .tm{font-size:12px;color:#e8e8ff;}
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def _log(a):
    st.session_state.activity_log.insert(0,{
        "time":datetime.datetime.now().strftime("%H:%M:%S"),"action":a})
    if len(st.session_state.activity_log)>100: st.session_state.activity_log.pop()

def _locale(l=None): return LOCALES.get(l or st.session_state.get("lang","en"),"en-US")
def _hash(p): return hashlib.sha256(p.strip().encode()).hexdigest()
def _chkpw(p,h): return hashlib.sha256(p.strip().encode()).hexdigest()==h

def _save_token(c):
    with open(TOKEN_FILE,"wb") as f: pickle.dump(c,f)


def _google_redirect_uri():
    configured = os.environ.get("GOOGLE_REDIRECT_URI")
    if configured:
        return configured
    return f"http://localhost:{st.get_option('server.port')}/"


def _start_google_oauth():
    if not GOOGLE_OK:
        st.error("Google sign-in is unavailable. Install the Google API packages from requirements.txt.")
        return
    if not CREDENTIALS_FILE.exists():
        st.error(f"Google OAuth client file not found: {CREDENTIALS_FILE.name}")
        return
    try:
        flow = Flow.from_client_secrets_file(
            str(CREDENTIALS_FILE), scopes=SCOPES, redirect_uri=_google_redirect_uri()
        )
        url, state = flow.authorization_url(
            access_type="offline", include_granted_scopes="true", prompt="select_account"
        )
        st.session_state["_google_auth_flow"] = flow
        st.session_state["_google_auth_state"] = state
        st.session_state["_google_auth_url"] = url
    except Exception:
        st.error("Could not start Google sign-in. Check the OAuth client configuration.")


def _complete_google_oauth():
    code = st.query_params.get("code")
    error = st.query_params.get("error")
    if not code and not error:
        return

    flow = st.session_state.get("_google_auth_flow")
    expected_state = st.session_state.get("_google_auth_state")
    returned_state = st.query_params.get("state")
    if error:
        st.error("Google sign-in was cancelled or denied.")
    elif not flow or not expected_state or returned_state != expected_state:
        st.error("Google sign-in expired or could not be verified. Please try again.")
    else:
        try:
            flow.fetch_token(code=code)
            _save_token(flow.credentials)
            info = google_info()
            if not info.get("email"):
                raise RuntimeError("Google did not return an email address.")
            st.session_state.user_name = info.get("name", "")
            st.session_state.user_email = info["email"]
            st.session_state.auth_provider = "google"
            st.session_state.logged_in = True
            st.session_state.stats["logins"] += 1
            _log("Google login")
            st.session_state.page = "Voice"
        except Exception:
            st.error("Google sign-in failed. Check the OAuth client, redirect URI, and Gmail API access.")

    for key in ("_google_auth_flow", "_google_auth_state", "_google_auth_url"):
        st.session_state.pop(key, None)
    st.query_params.clear()
    if st.session_state.logged_in:
        st.rerun()


def get_creds():
    if not GOOGLE_OK or not Path(TOKEN_FILE).exists(): return None
    try:
        with open(TOKEN_FILE,"rb") as f: c=pickle.load(f)
        if c and c.valid: return c
        if c and c.expired and c.refresh_token: c.refresh(Request()); _save_token(c); return c
    except: pass
    return None

def gmail_svc():
    c=get_creds(); return build("gmail","v1",credentials=c) if c else None

def google_connected(): return get_creds() is not None

def google_info():
    c=get_creds()
    if not c: return {}
    try: return build("oauth2","v2",credentials=c).userinfo().get().execute()
    except: return {}

def _extract_body(payload):
    body=""
    if "parts" in payload:
        for p in payload["parts"]:
            if p.get("mimeType")=="text/plain":
                d=p.get("body",{}).get("data","")
                if d: body+=base64.urlsafe_b64decode(d+"==").decode("utf-8",errors="replace")
            elif "parts" in p: body+=_extract_body(p)
    else:
        d=payload.get("body",{}).get("data","")
        if d: body=base64.urlsafe_b64decode(d+"==").decode("utf-8",errors="replace")
    return body.strip()

def _clean(t):
    t=re.sub(r'http\S+','',t)
    t=re.sub(r'On .{5,80} wrote:','',t)
    t=re.sub(r'<[^>]+>','',t)
    return re.sub(r'\s+',' ',t).strip()

def load_emails(limit=15):
    g=gmail_svc()
    if not g: return []
    try:
        res=g.users().messages().list(userId="me",maxResults=limit,labelIds=["INBOX"]).execute()
        out=[]
        for m in res.get("messages",[]):
            msg=g.users().messages().get(userId="me",id=m["id"],format="full",
                metadataHeaders=["From","Subject","Date"]).execute()
            hdrs={h["name"]:h["value"] for h in msg["payload"]["headers"]}
            body=_extract_body(msg["payload"])
            out.append({"id":m["id"],"from":hdrs.get("From","Unknown"),
                "subject":hdrs.get("Subject","(No Subject)"),
                "date":hdrs.get("Date",""),"snippet":msg.get("snippet",""),
                "body":body,"unread":"UNREAD" in msg.get("labelIds",[])})
        return out
    except Exception as e: st.error(f"Gmail: {e}"); return []

def do_send_email(to,subject,body):
    g=gmail_svc()
    if not g: return False,"Not connected to Google"
    try:
        fa=google_info().get("email","me")
        msg=MIMEMultipart("alternative")
        msg["To"]=to; msg["From"]=fa; msg["Subject"]=subject or "(No Subject)"
        msg.attach(MIMEText(body,"plain"))
        raw=base64.urlsafe_b64encode(msg.as_bytes()).decode()
        g.users().messages().send(userId="me",body={"raw":raw}).execute()
        st.session_state.stats["emails_sent"]+=1; _log(f"Email→{to}")
        return True,"Email sent!"
    except Exception as e: return False,str(e)

def tg_ok():
    return (REQUESTS_OK and bool(TELEGRAM_BOT_TOKEN)
            and bool(TELEGRAM_CHAT_ID) and len(TELEGRAM_BOT_TOKEN)>20
            and "YOUR" not in TELEGRAM_BOT_TOKEN)


def telegram_status():
    if not tg_ok():
        return False, "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in nova.env."
    try:
        response = _req.get(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe", timeout=10
        )
        if response.status_code == 401:
            return False, "Telegram rejected the bot token. Check it in nova.env."
        response.raise_for_status()
        result = response.json()
        if not result.get("ok"):
            return False, "Telegram could not validate this bot token."
        return True, f"Bot @{result.get('result', {}).get('username', 'unknown')} is reachable."
    except _req.RequestException:
        return False, "Could not reach the Telegram API."
    except ValueError:
        return False, "Telegram returned an unreadable response."


def load_tg(limit=20):
    if not tg_ok(): return []
    try:
        response=_req.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
                          params={"limit":limit},timeout=10)
        response.raise_for_status()
        r=response.json()
        if not r.get("ok"): return []
        msgs=[]
        for u in r.get("result",[]):
            m=u.get("message",{})
            if not m: continue
            ts=m.get("date",0)
            msgs.append({"text":m.get("text",""),
                "from":m.get("from",{}).get("first_name","?"),
                "date":datetime.datetime.fromtimestamp(ts).strftime("%I:%M %p") if ts else ""})
        return msgs
    except _req.RequestException:
        st.error("Could not reach the Telegram API. Check your network and bot token.")
        return []
    except ValueError:
        st.error("Telegram returned an unreadable response.")
        return []

def send_tg(text):
    if not tg_ok(): return False,"Telegram not configured"
    try:
        response=_req.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                           json={"chat_id":TELEGRAM_CHAT_ID,"text":text},timeout=10)
        response.raise_for_status()
        r=response.json()
        if r.get("ok"): st.session_state.stats["telegrams_sent"]+=1; _log("TG sent"); return True,"Sent!"
        return False,r.get("description","Failed")
    except _req.RequestException: return False,"Could not reach the Telegram API."
    except ValueError: return False,"Telegram returned an unreadable response."

def summarize_email(body,subject=""):
    body=_clean(body)
    if not body: return "No content."
    if OPENAI_OK and OPENAI_API_KEY:
        try:
            c=_oai.OpenAI(api_key=OPENAI_API_KEY)
            r=c.chat.completions.create(model="gpt-3.5-turbo",max_tokens=120,
                messages=[{"role":"system","content":"Summarize in 2 sentences."},
                          {"role":"user","content":f"Subject:{subject}\n{body[:2000]}"}])
            return r.choices[0].message.content.strip()
        except: pass
    sents=[s.strip() for s in re.split(r'(?<=[.!?])\s+',body) if len(s.strip())>20]
    return " ".join(sents[:2]) if sents else body[:200]

# ── VOICE RESPONSE BUILDER ────────────────────────────────────────────────────
def _voice_reply(text, nav=None):
    """Store a voice response for NOVA to speak + optional navigation"""
    st.session_state._bridge_out = text
    if nav:
        st.session_state._bridge_nav = nav

# ── COMMAND PROCESSOR ─────────────────────────────────────────────────────────
def process_cmd(cmd: str):
    """Called when JS sends a command via the bridge. Returns nothing — sets session state."""
    lang = st.session_state.lang
    p    = cmd.strip()
    pl   = p.lower()
    st.session_state.stats["voice_cmds"] += 1

    # ── VOICE LOGIN ──
    if p.startswith("LOGIN|||"):
        _voice_reply("Please sign in with Google first. Saying a name cannot authenticate an account.")
        return

    # ── PIN VERIFY ──
    if p.startswith("PIN|||"):
        parts  = p.split("|||")
        pin_in = parts[1] if len(parts)>1 else ""
        action = parts[2] if len(parts)>2 else ""
        if not st.session_state.pin_set:
            _voice_reply("No PIN is set. Please go to Admin and create a PIN first.")
            return
        if pin_in == st.session_state.user_pin:
            st.session_state.pin_verified_for.add(action)
            _log(f"PIN OK: {action}")
            nav_page = {"send_email":"Email","read_email":"Email",
                        "send_tg":"Telegram","read_tg":"Telegram"}.get(action,"")
            if nav_page:
                st.session_state.page = nav_page
                _voice_reply(f"PIN correct! {action.replace('_',' ')} unlocked.", nav=nav_page)
            else:
                _voice_reply("PIN correct! Access granted.")
        else:
            _log(f"PIN FAIL: {action}")
            _voice_reply("Wrong PIN. Access denied. Please try again.")
        return

    # ── SEND EMAIL ──
    if p.startswith("SEND_EMAIL|||"):
        parts = p.split("|||")
        if len(parts)==4:
            to,sub,body = parts[1],parts[2],parts[3]
            ok,msg = do_send_email(to,sub,body)
            _voice_reply(f"Email sent to {to}!" if ok else f"Failed to send email. {msg}")
        return

    # ── SEND TELEGRAM ──
    if p.startswith("SEND_TG|||"):
        parts = p.split("|||")
        if len(parts)==2:
            ok,msg = send_tg(parts[1])
            _voice_reply("Telegram message sent!" if ok else f"Failed. {msg}")
        return

    # ── LOAD EMAILS (voice triggered) ──
    if p == "LOAD_EMAILS":
        with st.spinner("Loading emails…"):
            st.session_state.emails = load_emails()
        n = len(st.session_state.emails)
        unread = sum(1 for e in st.session_state.emails if e.get("unread"))
        if n == 0:
            _voice_reply("No emails found. Make sure Gmail is connected in Settings.")
        else:
            first = st.session_state.emails[0]
            frm   = re.sub(r'<[^>]+>','',first["from"]).strip().split()[0]
            _voice_reply(f"Loaded {n} emails. {unread} unread. Latest is from {frm}, subject: {first['subject']}.")
        return

    # ── READ EMAIL ──
    if p.startswith("READ_EMAIL|||"):
        idx = int(p.split("|||")[1]) if len(p.split("|||"))>1 else 0
        emails = st.session_state.emails
        if not emails:
            _voice_reply("No emails loaded. Say load emails first.")
            return
        idx = min(idx, len(emails)-1)
        e   = emails[idx]
        frm = re.sub(r'<[^>]+>','',e["from"]).strip()
        body= _clean(e.get("body","") or e.get("snippet",""))[:400]
        _voice_reply(f"Email from {frm}. Subject: {e['subject']}. {body}")
        return

    # ── SUMMARIZE EMAIL ──
    if p.startswith("SUMMARIZE_EMAIL|||"):
        idx = int(p.split("|||")[1]) if len(p.split("|||"))>1 else 0
        emails = st.session_state.emails
        if not emails:
            _voice_reply("No emails loaded. Say load emails first.")
            return
        idx = min(idx, len(emails)-1)
        e   = emails[idx]
        with st.spinner("Summarizing…"):
            s = summarize_email(e.get("body",""), e["subject"])
        _voice_reply(f"Summary: {s}")
        return

    # ── LOAD TELEGRAM ──
    if p == "LOAD_TG":
        with st.spinner("Loading messages…"):
            st.session_state.tg_messages = load_tg()
        n = len(st.session_state.tg_messages)
        if n == 0:
            _voice_reply("No Telegram messages found.")
        else:
            last = st.session_state.tg_messages[-1]
            _voice_reply(f"Loaded {n} messages. Latest from {last['from']}: {last['text'][:100]}")
        return

    # ── READ TELEGRAM ──
    if p == "READ_TG":
        msgs = st.session_state.tg_messages
        if not msgs:
            _voice_reply("No Telegram messages loaded. Say load telegram first.")
            return
        last = msgs[-1]
        _voice_reply(f"Latest message from {last['from']}: {last['text']}")
        return

    # ── SET PIN ──
    if p.startswith("SET_PIN|||"):
        parts = p.split("|||")
        pin = parts[1] if len(parts)>1 else ""
        if len(pin)==4 and pin.isdigit():
            st.session_state.user_pin = pin
            st.session_state.pin_set  = True
            st.session_state.pin_verified_for = set()
            _log("PIN set by voice")
            _voice_reply(f"PIN set to {' '.join(pin)}. All send and read actions are now protected.")
        else:
            _voice_reply("Invalid PIN. Please say exactly 4 digits.")
        return

    # ── NAVIGATION ──
    nav_map = {
        ("email","inbox","open email","check email","go to email"):               "Email",
        ("telegram","open telegram","check telegram","go to telegram"):           "Telegram",
        ("contacts","open contacts","my contacts"):                               "Contacts",
        ("settings","open settings"):                                             "Settings",
        ("admin","open admin"):                                                   "Admin",
        ("profile","open profile","my profile"):                                  "Profile",
        ("whatsapp","open whatsapp"):                                             "WhatsApp",
        ("dashboard","home","go home"):                                           "Dashboard",
        ("voice","voice assistant","open assistant","assistant","home screen"):   "Voice",
        ("speech to text","stt"):                                                 "STT",
        ("text to speech","tts"):                                                 "TTS",
    }
    for triggers, page in nav_map.items():
        if any(t in pl for t in triggers):
            st.session_state.page = page
            _voice_reply(f"Opening {page}.", nav=page)
            return

    # ── INFO ──
    if "time" in pl:
        t = datetime.datetime.now().strftime("%I:%M %p")
        _voice_reply(f"The current time is {t}.")
        return
    if "date" in pl or "today" in pl:
        d = datetime.datetime.now().strftime("%A, %B %d %Y")
        _voice_reply(f"Today is {d}.")
        return
    if "help" in pl or "commands" in pl or "what can you do" in pl:
        _voice_reply(
            "Here is what I can do. Say: open email, load emails, read email, send email, "
            "open telegram, load telegram, read telegram, send telegram, "
            "open contacts, open settings, open admin, set pin, what time, what date. "
            "For sending you need a PIN. Say set pin followed by 4 digits to create one."
        )
        return
    if any(g in pl for g in ["hello","hi nova","hey nova","good morning","good evening","namaste"]):
        h = datetime.datetime.now().hour
        greet = "Good morning" if h<12 else "Good afternoon" if h<17 else "Good evening"
        name  = st.session_state.user_name or "friend"
        _voice_reply(f"{greet} {name}! I am NOVA your voice AI assistant. How can I help you?")
        return

    _voice_reply(f"I heard: {p}. I did not understand that command. Say help to hear what I can do.")

# ── MEGA VOICE HTML ───────────────────────────────────────────────────────────
def _nova_html(lang="en", logged_in=False, pin_set=False,
               nova_reply="", nav_signal="",
               emails=None, tg_msgs=None,
               user_name="") -> str:
    loc      = _locale(lang)
    emails   = emails   or []
    tg_msgs  = tg_msgs  or []

    # Build email list for JS
    email_js = json.dumps([{
        "from":  re.sub(r'<[^>]+>','',e["from"]).strip()[:30],
        "sub":   e["subject"][:50],
        "snip":  (e.get("snippet","") or "")[:80],
        "unread":e.get("unread",False),
    } for e in emails[:10]]).replace("<", "\\u003c")

    tg_js = json.dumps([{
        "from": m["from"][:20],
        "text": m["text"][:80],
        "date": m["date"],
    } for m in tg_msgs[-8:]]).replace("<", "\\u003c")

    reply_js     = json.dumps(nova_reply).replace("<", "\\u003c")
    nav_js       = json.dumps(nav_signal).replace("<", "\\u003c")
    name_js      = json.dumps(user_name).replace("<", "\\u003c")
    pin_set_js   = "true" if pin_set else "false"
    logged_in_js = "true" if logged_in else "false"

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:transparent;
  color:#e8e8ff;overflow-x:hidden;min-height:100vh;}}

/* ── ORB ── */
@keyframes float{{0%,100%{{transform:translateY(0)scale(1)}}50%{{transform:translateY(-8px)scale(1.05)}}}}
@keyframes pulse{{0%,100%{{box-shadow:0 0 30px #6c63ffaa,0 0 60px #6c63ff44}}
  50%{{box-shadow:0 0 80px #ff6b9dcc,0 0 120px #ff6b9d44}}}}
@keyframes orbActive{{0%,100%{{transform:scale(1.05);box-shadow:0 0 60px #ff6b9daa}}
  50%{{transform:scale(1.12);box-shadow:0 0 100px #ff6b9dff}}}}
@keyframes wv{{0%,100%{{transform:scaleY(1);opacity:.4}}50%{{transform:scaleY(4);opacity:1}}}}
@keyframes fadeIn{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}

#wrap{{display:flex;flex-direction:column;align-items:center;padding:10px 8px 20px;gap:8px;}}

/* orb */
#orb{{width:120px;height:120px;border-radius:50%;cursor:pointer;
  background:radial-gradient(circle at 35% 35%,#c084fc,#6c63ff 50%,#00d4ff);
  display:flex;align-items:center;justify-content:center;font-size:46px;
  animation:float 3.5s ease-in-out infinite;user-select:none;
  transition:all .3s;}}
#orb.listening{{animation:orbActive .7s ease-in-out infinite alternate;}}
#orb.speaking{{animation:pulse .9s ease-in-out infinite;}}

/* title */
#title{{font-size:22px;font-weight:900;letter-spacing:6px;
  background:linear-gradient(135deg,#6c63ff,#00d4ff);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
#badge{{padding:3px 16px;border-radius:20px;font-size:10px;font-weight:700;
  background:rgba(108,99,255,.2);border:1px solid rgba(108,99,255,.4);
  color:#a78bfa;letter-spacing:1px;}}

/* wave bars */
#bars{{display:flex;gap:4px;height:28px;align-items:center;}}
.b{{width:4px;border-radius:3px;background:#2a2a3a;height:4px;}}
.b.on:nth-child(1){{animation:wv 1s 0s ease-in-out infinite;background:#6c63ff;}}
.b.on:nth-child(2){{animation:wv 1s .1s ease-in-out infinite;background:#8b5cf6;}}
.b.on:nth-child(3){{animation:wv 1s .2s ease-in-out infinite;background:#ff6b9d;}}
.b.on:nth-child(4){{animation:wv 1s .1s ease-in-out infinite;background:#8b5cf6;}}
.b.on:nth-child(5){{animation:wv 1s 0s ease-in-out infinite;background:#6c63ff;}}

/* speech bubble */
#bubble{{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);
  border-radius:16px;padding:12px 16px;width:100%;max-width:500px;
  font-size:13px;line-height:1.9;min-height:54px;animation:fadeIn .3s ease;}}

/* heard text */
#heard{{background:rgba(0,255,136,.04);border:1px solid rgba(0,255,136,.18);
  border-radius:8px;padding:6px 14px;width:100%;max-width:500px;
  font-size:11px;color:#00ff88;min-height:20px;font-style:italic;}}

/* flow panel */
#flow{{background:rgba(108,99,255,.07);border:1px solid rgba(108,99,255,.3);
  border-radius:10px;padding:10px 14px;width:100%;max-width:500px;
  font-size:12px;color:#a78bfa;display:none;line-height:2.2;}}

/* status */
#status{{font-size:11px;color:#7a7a9a;letter-spacing:1px;min-height:16px;}}

/* buttons */
#btns{{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;}}
.btn-main{{padding:10px 24px;border:none;border-radius:10px;cursor:pointer;
  background:linear-gradient(135deg,#6c63ff,#8b5cf6);color:#fff;
  font-size:12px;font-weight:700;transition:.2s;}}
.btn-main:hover{{transform:scale(1.03);}}
.btn-stop{{padding:10px 16px;border:1px solid rgba(255,68,102,.5);border-radius:10px;
  cursor:pointer;background:rgba(255,68,102,.1);color:#ff4466;font-size:12px;font-weight:700;}}
.btn-sec{{padding:8px 14px;border:1px solid rgba(255,255,255,.15);border-radius:9px;
  cursor:pointer;background:rgba(255,255,255,.06);color:#e8e8ff;font-size:11px;font-weight:600;}}

/* command hints */
#hints{{width:100%;max-width:500px;background:rgba(255,255,255,.03);
  border:1px solid rgba(255,255,255,.07);border-radius:10px;padding:10px 14px;}}
#hints summary{{font-size:11px;color:#7a7a9a;cursor:pointer;user-select:none;}}
#hints div{{font-size:10px;color:#555;line-height:2.4;margin-top:8px;}}
#hints span.cmd{{color:#a78bfa;}}
#hints span.g{{color:#00d4ff;}}

/* email/tg cards */
#cards{{width:100%;max-width:500px;}}
.card-row{{display:flex;gap:10px;overflow-x:auto;padding:4px 0 8px;
  scrollbar-width:thin;scrollbar-color:#6c63ff33 transparent;}}
.card-row::-webkit-scrollbar{{height:3px;}}
.card-row::-webkit-scrollbar-thumb{{background:#6c63ff44;border-radius:3px;}}
.ecard{{min-width:190px;background:rgba(108,99,255,.08);
  border:1px solid rgba(108,99,255,.2);border-radius:10px;padding:10px;
  flex-shrink:0;font-size:11px;cursor:pointer;transition:.2s;}}
.ecard:hover{{background:rgba(108,99,255,.16);transform:translateY(-2px);}}
.ecard .ef{{color:#a78bfa;font-weight:700;margin-bottom:3px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.ecard .es{{color:#e8e8ff;font-weight:600;margin-bottom:3px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.ecard .eb{{color:#7a7a9a;display:-webkit-box;-webkit-line-clamp:2;
  -webkit-box-orient:vertical;overflow:hidden;}}
.tcard{{min-width:170px;background:rgba(0,136,204,.08);
  border:1px solid rgba(0,136,204,.2);border-radius:10px;padding:10px;
  flex-shrink:0;font-size:11px;}}
.tcard .tf{{color:#00aaff;font-weight:700;margin-bottom:3px;}}
.tcard .tm{{color:#e8e8ff;}}
.card-lbl{{font-size:10px;color:#7a7a9a;letter-spacing:1px;
  text-transform:uppercase;margin-bottom:5px;margin-top:8px;}}
</style>
</head><body>
<div id="wrap">
  <!-- ORB -->
  <div id="orb">🎙️</div>
  <div id="title">NOVA</div>
  <div id="badge" id="badge">TAP ORB TO START</div>

  <!-- Wave bars -->
  <div id="bars">
    <span class="b" id="b1"></span><span class="b" id="b2"></span>
    <span class="b" id="b3"></span><span class="b" id="b4"></span>
    <span class="b" id="b5"></span>
  </div>

  <!-- NOVA speech bubble -->
  <div id="bubble">👋 Tap the orb or press <b>Start</b> — I'll listen, understand, and act!</div>

  <!-- User heard text -->
  <div id="heard">Your voice appears here…</div>

  <!-- Flow panel (multi-step) -->
  <div id="flow"></div>

  <!-- Status -->
  <div id="status">Ready</div>

  <!-- Buttons -->
  <div id="btns">
    <button class="btn-main" id="btnMain">🎤 Start NOVA</button>
    <button class="btn-stop" id="btnStop">⏹ Stop</button>
    <button class="btn-sec" id="btnRepeat">🔁 Repeat</button>
  </div>

  <!-- Cards (emails + tg) -->
  <div id="cards"></div>

  <!-- Command hints -->
  <details id="hints">
    <summary>💡 What can I say?</summary>
    <div>
      <span class="g">Navigation:</span>
      <span class="cmd">open email · open telegram · open contacts · open settings · open admin · go home</span><br>
      <span class="g">Email:</span>
      <span class="cmd">load emails · read email · read second email · send email · summarize email</span><br>
      <span class="g">Telegram:</span>
      <span class="cmd">load telegram · read telegram · send telegram</span><br>
      <span class="g">PIN:</span>
      <span class="cmd">set pin 1 2 3 4 · (PIN required before sending/reading)</span><br>
      <span class="g">Info:</span>
      <span class="cmd">what time · what date · help · hello · stop</span><br>
      <span class="g">Login:</span>
      <span class="cmd">say your name on login screen</span>
    </div>
  </details>
</div>

<script>
(function(){{
  /* ── State ── */
  var ON=false, SP=false, BUSY=false, rc=null;
  var SRC=window.SpeechRecognition||window.webkitSpeechRecognition;
  var LOC="{loc}";
  var FLOW=null, STEP=0, D={{}};
  var PIN_ACTION=null;
  var LAST_SPOKEN="";

  var LOGGED_IN={logged_in_js};
  var PIN_SET={pin_set_js};
  var USER={name_js};

  /* ── Elements ── */
  var orb    =document.getElementById("orb");
  var badge  =document.getElementById("badge");
  var bubble =document.getElementById("bubble");
  var heard  =document.getElementById("heard");
  var flow   =document.getElementById("flow");
  var status =document.getElementById("status");
  var btnMain=document.getElementById("btnMain");
  var bars   =[1,2,3,4,5].map(function(i){{return document.getElementById("b"+i);}});

  /* ── On load: init cards + handle python reply ── */
  window.addEventListener("load",function(){{
    renderCards();
    var reply={reply_js};
    var nav={nav_js};
    if(reply){{
      setTimeout(function(){{
        bubble.innerHTML="🔊 "+reply;
        speakText(reply,function(){{if(ON)listen();}});
      }},400);
    }}
    if(nav&&nav!==window._lastNav){{
      window._lastNav=nav;
    }}
  }});

  /* ── Cards ── */
  var EMAILS={email_js};
  var TGS={tg_js};
  function renderCards(){{
    var c=document.getElementById("cards");
    var html="";
    if(EMAILS.length){{
      html+="<div class='card-lbl'>📧 Emails</div><div class='card-row'>";
      EMAILS.forEach(function(e,i){{
        html+="<div class='ecard' onclick='readEmailCard("+i+")'>"
          +"<div class='ef'>"+(e.unread?"🔴 ":"⚪ ")+e.from+"</div>"
          +"<div class='es'>"+e.sub+"</div>"
          +"<div class='eb'>"+e.snip+"</div></div>";
      }});
      html+="</div>";
    }}
    if(TGS.length){{
      html+="<div class='card-lbl'>✈️ Telegram</div><div class='card-row'>";
      TGS.forEach(function(m){{
        html+="<div class='tcard'><div class='tf'>"+m.from+" · "+m.date+"</div>"
          +"<div class='tm'>"+m.text+"</div></div>";
      }});
      html+="</div>";
    }}
    c.innerHTML=html;
  }}
  function readEmailCard(i){{
    if(!ON){{ bubble.innerHTML="🔊 Tap Start first, then tap a card."; return; }}
    sendCmd("READ_EMAIL|||"+i);
  }}

  /* ── UI helpers ── */
  function setBadge(t){{ badge.textContent=t; }}
  function setBubble(t){{ bubble.innerHTML=t; }}
  function setHeard(t){{ heard.textContent=t; }}
  function setStatus(t){{ status.textContent=t; }}
  function setFlow(h){{ if(h){{flow.style.display="block";flow.innerHTML=h;}}else{{flow.style.display="none";flow.innerHTML="";}} }}
  function waveOn(on){{
    bars.forEach(function(b,i){{
      if(!b)return;
      if(on){{ b.classList.add("on"); b.style.height=["8px","18px","30px","18px","8px"][i]; }}
      else{{ b.classList.remove("on"); b.style.height="4px"; }}
    }});
  }}
  function orbState(s){{
    orb.classList.remove("listening","speaking");
    if(s) orb.classList.add(s);
    orb.style.animation="";
  }}
  function btnLabel(on){{ btnMain.textContent=on?"⏹ Stop NOVA":"🎤 Start NOVA"; }}

  /* ── Bridge: send command to Python ── */
  function sendCmd(cmd){{
    BUSY=true;
    var doc=window.parent.document;
    var inputWindow=doc.defaultView;
    var found=false;
    var inputs=doc.querySelectorAll("input[data-bridge='nova']");
    if(!inputs.length) inputs=doc.querySelectorAll("input");
    for(var i=0;i<inputs.length;i++){{
      var ph=inputs[i].placeholder||"";
      if(ph.indexOf("NOVA-BRIDGE")!==-1||ph.indexOf("nova-bridge")!==-1){{
        var setter=Object.getOwnPropertyDescriptor(inputWindow.HTMLInputElement.prototype,"value").set;
        setter.call(inputs[i],cmd);
        inputs[i].dispatchEvent(new inputWindow.Event("input",{{bubbles:true}}));
        found=true;
        setTimeout(function(){{
          var btns=doc.querySelectorAll("button");
          for(var j=0;j<btns.length;j++){{
            var t=(btns[j].innerText||btns[j].textContent||"").trim();
            if(t==="▶"){{btns[j].click();break;}}
          }}
        }},200);
        break;
      }}
    }}
    if(!found){{
      BUSY=false;
      setBubble("⚠️ Bridge not found. Make sure you're on the Voice page.");
    }}
    /* Python will re-render with _bridge_out set — page reloads and we speak it */
  }}

  /* ── TTS ── */
  function speakText(text,cb){{
    if(!text){{if(cb)cb();return;}}
    SP=true; LAST_SPOKEN=text;
    window.speechSynthesis&&window.speechSynthesis.cancel();
    waveOn(false); orbState("speaking"); setBadge("🔊 SPEAKING");
    setBubble("🔊 "+text);
    var u=new SpeechSynthesisUtterance(text);
    u.lang=LOC; u.rate=0.92; u.pitch=1.05;
    var done=false;
    function fin(){{if(done)return;done=true;SP=false;orbState(ON?"listening":null);if(cb)cb();}}
    u.onend=fin; u.onerror=fin;
    setTimeout(fin,Math.max(3000,text.split(" ").length*620)+1200);
    window.speechSynthesis.speak(u);
  }}

  /* ── STT ── */
  function listen(){{
    if(!ON||SP||BUSY)return;
    if(rc){{try{{rc.abort();}}catch(e){{}}rc=null;}}
    if(!SRC){{setBubble("❌ Use <b>Google Chrome</b> for voice.");return;}}
    var r=new SRC();
    r.lang=LOC; r.continuous=false; r.interimResults=true; r.maxAlternatives=1;
    rc=r; waveOn(true); orbState("listening"); setBadge("👂 LISTENING…"); setStatus("Speak now…");
    r.onresult=function(e){{
      var txt="",fin=false;
      for(var i=e.resultIndex;i<e.results.length;i++){{
        txt+=e.results[i][0].transcript;
        if(e.results[i].isFinal) fin=true;
      }}
      setHeard(txt.trim());
      if(!fin) return;
      rc=null; waveOn(false); setBadge("⚡ PROCESSING…"); setStatus("Processing…");
      route(txt.trim());
    }};
    r.onerror=function(ev){{
      rc=null; waveOn(false); setStatus("Error: "+ev.error);
      if(ev.error==="not-allowed"){{
        ON=false; orbState(null); btnLabel(false); setBadge("MIC BLOCKED");
        setBubble("❌ Microphone blocked. In Chrome: click 🔒 in address bar → Allow microphone → Reload.");
        return;
      }}
      if(ON&&!SP) setTimeout(listen,600);
    }};
    r.onend=function(){{rc=null; waveOn(false); if(ON&&!SP&&!BUSY) setTimeout(listen,350);}};
    try{{r.start();}}catch(ex){{rc=null;if(ON)setTimeout(listen,600);}}
  }}

  /* ── Main router ── */
  function route(raw){{
    var p=raw.toLowerCase().trim();

    /* universal stop */
    if(/\\b(stop|exit|quit|goodbye|bye|cancel|abort)\\b/.test(p)&&!FLOW&&!PIN_ACTION){{
      speakText("Stopping. Goodbye!",function(){{stopNOVA();}});
      return;
    }}
    /* cancel current flow */
    if(/\\b(cancel|stop|nevermind|go back)\\b/.test(p)&&(FLOW||PIN_ACTION)){{
      FLOW=null; PIN_ACTION=null; STEP=0; D={{}};
      setFlow(null);
      speakText("Cancelled.",function(){{listen();}});
      return;
    }}

    /* active flows */
    if(PIN_ACTION){{  handlePin(raw,p); return; }}
    if(FLOW==="login"){{  loginFlow(raw,p);  return; }}
    if(FLOW==="email"){{  emailFlow(raw,p);  return; }}
    if(FLOW==="tg"){{     tgFlow(raw,p);     return; }}
    if(FLOW==="setpin"){{ setPinFlow(raw,p); return; }}

    freeCmd(raw,p);
  }}

  /* ── Login flow (on login screen) ── */
  function startLogin(){{
    FLOW="login"; STEP=0; D={{}};
    speakText("Please say your name to login.",null);
  }}
  function loginFlow(raw,p){{
    FLOW=null; D={{}};
    setFlow(null);
    speakText("Use Google sign-in to authenticate. A spoken name is not a login.",null);
  }}

  /* ── PIN flow ── */
  function needPin(action,then){{
    if(!PIN_SET){{
      speakText("No PIN set. Say set pin followed by 4 digits to create one.",function(){{listen();}});
      return;
    }}
    PIN_ACTION=action; window._pinThen=then;
    setFlow("🔐 PIN required for: <b>"+action+"</b><br>Say your 4 digits");
    speakText("PIN required. Please say your 4 digit PIN.",null);
  }}
  function handlePin(raw,p){{
    var digits=p.replace(/[^0-9]/g,"");
    if(!digits){{
      var map={{zero:"0",one:"1",two:"2",three:"3",four:"4",five:"5",six:"6",seven:"7",eight:"8",nine:"9"}};
      digits=p.split(/\s+/).map(function(w){{return map[w]||"";}}).join("");
    }}
    if(digits.length>=4){{
      var pin4=digits.slice(0,4);
      var action=PIN_ACTION;
      PIN_ACTION=null; setFlow(null);
      sendCmd("PIN|||"+pin4+"|||"+action);
      speakText("Checking PIN…",null);
      /* Python will respond via bridge_out on next render */
    }} else {{
      speakText("I need 4 digits. Please say all 4 digits of your PIN.",null);
    }}
  }}

  /* ── Set PIN flow ── */
  function setPinFlow(raw,p){{
    var digits=p.replace(/[^0-9]/g,"");
    if(!digits){{
      var map={{zero:"0",one:"1",two:"2",three:"3",four:"4",five:"5",six:"6",seven:"7",eight:"8",nine:"9"}};
      digits=p.split(/\s+/).map(function(w){{return map[w]||"";}}).join("");
    }}
    if(digits.length>=4){{
      FLOW=null; D={{}};
      sendCmd("SET_PIN|||"+digits.slice(0,4));
      speakText("Setting your PIN now.",null);
    }} else {{
      speakText("I need 4 digits for the PIN. Please say 4 numbers.",null);
    }}
  }}

  /* ── Email compose flow ── */
  function emailFlow(raw,p){{
    if(STEP===0){{
      D.to=raw.trim(); STEP=1;
      setFlow("📧 <b>To:</b> "+D.to);
      speakText("Got it. What is the subject?",null);
    }} else if(STEP===1){{
      D.sub=raw.trim(); STEP=2;
      setFlow("📧 <b>To:</b> "+D.to+"<br>📝 <b>Subject:</b> "+D.sub);
      speakText("Good. Now say the message body.",null);
    }} else if(STEP===2){{
      D.body=raw.trim(); STEP=3;
      setFlow("📧 <b>To:</b> "+D.to+"<br>📝 "+D.sub+"<br>💬 "+D.body.slice(0,60));
      speakText("Ready to send to "+D.to+". Subject: "+D.sub+". Say confirm to send or cancel.",null);
    }} else if(STEP===3){{
      if(/confirm|send|yes|ok|sure|proceed|ha|haan/.test(p)){{
        var to=D.to,sub=D.sub,body=D.body;
        FLOW=null; STEP=0; D={{}};
        setFlow(null);
        sendCmd("SEND_EMAIL|||"+to+"|||"+sub+"|||"+body);
        speakText("Sending your email now.",null);
      }} else {{
        FLOW=null; STEP=0; D={{}}; setFlow(null);
        speakText("Cancelled.",function(){{listen();}});
      }}
    }}
  }}

  /* ── Telegram compose flow ── */
  function tgFlow(raw,p){{
    if(STEP===0){{
      D.msg=raw.trim(); STEP=1;
      setFlow("✈️ <b>Message:</b> "+D.msg.slice(0,70));
      speakText(D.msg+". Say confirm to send or cancel.",null);
    }} else if(STEP===1){{
      if(/confirm|send|yes|ok|sure|proceed|ha|haan/.test(p)){{
        var msg=D.msg;
        FLOW=null; STEP=0; D={{}};
        setFlow(null);
        sendCmd("SEND_TG|||"+msg);
        speakText("Sending your Telegram message now.",null);
      }} else {{
        FLOW=null; STEP=0; D={{}}; setFlow(null);
        speakText("Cancelled.",function(){{listen();}});
      }}
    }}
  }}

  /* ── Free commands ── */
  function freeCmd(raw,p){{
    /* Greetings */
    if(/\\b(hello|hi nova|hey nova|hi|hey|namaste|vanakkam)\\b/.test(p)){{
      var h=new Date().getHours();
      var g=h<12?"Good morning":h<17?"Good afternoon":"Good evening";
      speakText(g+" "+(USER||"friend")+"! I am NOVA your voice AI assistant. How can I help you?",null);
      return;
    }}

    /* Help */
    if(/\\b(help|commands|what can you do)\\b/.test(p)){{
      sendCmd(raw); return;
    }}

    /* Time / Date */
    if(/time/.test(p)){{ sendCmd(raw); return; }}
    if(/date|today|day/.test(p)){{ sendCmd(raw); return; }}

    /* Navigation */
    if(/open email|check email|go to email|email/.test(p)&&!/send|compose|write/.test(p)){{
      sendCmd("open email"); return;
    }}
    if(/open telegram|check telegram|go to telegram/.test(p)&&!/send/.test(p)){{
      sendCmd("open telegram"); return;
    }}
    if(/open contacts|contacts/.test(p)){{ sendCmd("open contacts"); return; }}
    if(/open settings|settings/.test(p)){{ sendCmd("open settings"); return; }}
    if(/open admin|admin/.test(p)){{ sendCmd("open admin"); return; }}
    if(/open profile|profile/.test(p)){{ sendCmd("open profile"); return; }}
    if(/home|dashboard|main/.test(p)){{ sendCmd("home"); return; }}

    /* Load emails/tg */
    if(/load email|fetch email|get email|refresh email|check my email/.test(p)){{
      sendCmd("LOAD_EMAILS"); speakText("Loading your emails now.",null); return;
    }}
    if(/load telegram|fetch telegram|get telegram|refresh telegram|check telegram/.test(p)){{
      sendCmd("LOAD_TG"); speakText("Loading Telegram messages.",null); return;
    }}

    /* Read email */
    if(/read email|read my email|first email|latest email/.test(p)){{
      needPin("read_email",function(){{
        var idx=0;
        if(/second/.test(p)) idx=1;
        if(/third/.test(p))  idx=2;
        sendCmd("READ_EMAIL|||"+idx);
      }});
      return;
    }}

    /* Read telegram */
    if(/read telegram|read message|latest message/.test(p)){{
      needPin("read_tg",function(){{sendCmd("READ_TG");}});
      return;
    }}

    /* Summarize */
    if(/summarize|summary|brief/.test(p)){{
      sendCmd("SUMMARIZE_EMAIL|||0");
      speakText("Summarizing your latest email.",null);
      return;
    }}

    /* Send email */
    if(/send email|compose email|write email|new email/.test(p)){{
      needPin("send_email",function(){{
        FLOW="email"; STEP=0; D={{}};
        speakText("Who do you want to send the email to? Say their name or email address.",null);
      }});
      return;
    }}

    /* Send telegram */
    if(/send telegram|telegram message|message on telegram/.test(p)){{
      needPin("send_tg",function(){{
        FLOW="tg"; STEP=0; D={{}};
        speakText("What message do you want to send on Telegram?",null);
      }});
      return;
    }}

    /* Set PIN */
    if(/set pin|create pin|change pin|new pin/.test(p)){{
      /* try to extract digits in same sentence */
      var digits=p.replace(/[^0-9]/g,"");
      if(!digits){{
        var map={{zero:"0",one:"1",two:"2",three:"3",four:"4",five:"5",six:"6",seven:"7",eight:"8",nine:"9"}};
        digits=p.split(/\s+/).map(function(w){{return map[w]||"";}}).join("");
      }}
      if(digits.length>=4){{
        sendCmd("SET_PIN|||"+digits.slice(0,4));
        speakText("Setting PIN now.",null);
      }} else {{
        FLOW="setpin"; STEP=0;
        speakText("Please say your 4 digit PIN now.",null);
      }}
      return;
    }}

    /* Voice login trigger */
    if(!LOGGED_IN||/login|sign in|enter/.test(p)){{
      FLOW="login"; STEP=0; D={{}};
      loginFlow(raw,p);
      return;
    }}

    /* Logout */
    if(/logout|log out|sign out/.test(p)){{
      speakText("Logging you out. Goodbye!",function(){{sendCmd("open admin");}});
      return;
    }}

    /* Not understood */
    sendCmd(raw);
  }}

  /* ── Start / Stop ── */
  function startNOVA(){{
    ON=true; btnLabel(true); orbState("listening");
    setBadge("🚀 STARTING…");
    var greet;
    if(!LOGGED_IN){{
      greet="Please sign in with Google before using voice controls.";
    }} else {{
      var h=new Date().getHours();
      var g=h<12?"Good morning":h<17?"Good afternoon":"Good evening";
      greet=g+" "+(USER||"")+"! I am NOVA. I am ready. Say help to hear all commands, or just tell me what to do.";
    }}
    speakText(greet,function(){{listen();}});
  }}
  function stopNOVA(){{
    ON=false; SP=false; BUSY=false; FLOW=null; PIN_ACTION=null; STEP=0; D={{}};
    if(rc){{try{{rc.abort();}}catch(e){{}}rc=null;}}
    window.speechSynthesis&&window.speechSynthesis.cancel();
    orbState(null); waveOn(false); setFlow(null); btnLabel(false);
    setBadge("TAP ORB TO START");
    setBubble("NOVA stopped. Tap the orb to start again.");
    setHeard(""); setStatus("Stopped");
  }}
  function toggleNOVA(){{ if(ON) stopNOVA(); else startNOVA(); }}
  function repeatLast(){{ if(LAST_SPOKEN) speakText(LAST_SPOKEN,function(){{if(ON)listen();}}); }}
  orb.addEventListener("click",toggleNOVA);
  btnMain.addEventListener("click",toggleNOVA);
  document.getElementById("btnStop").addEventListener("click",stopNOVA);
  document.getElementById("btnRepeat").addEventListener("click",repeatLast);

  /* after PIN is verified by Python, restart listening */
  window._pinVerifiedLast="";
  function checkPinResult(){{
    /* The nova_reply injected on load handles this — but also check badge */
    if(document.getElementById("badge")&&document.getElementById("badge").textContent==="⚡ PROCESSING…"){{
      BUSY=false;
      if(ON&&!SP) setTimeout(listen,300);
    }}
  }}
  setInterval(function(){{
    if(BUSY&&ON&&!SP){{
      var b=document.getElementById("badge");
      /* if Python responded (bubble changed), clear busy */
      if(b&&b.textContent!=="⚡ PROCESSING…"){{ BUSY=false; if(ON&&!SP)setTimeout(listen,300); }}
    }}
  }},1000);

}})();
</script>
</body></html>"""

# ── Sidebar ───────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:8px 0 4px">
          <div style="font-size:20px;font-weight:900;letter-spacing:5px;
            background:linear-gradient(135deg,#6c63ff,#00d4ff);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent">NOVA</div>
          <div style="font-size:9px;color:#555;letter-spacing:3px">VOICE AI ASSISTANT</div>
        </div>""", unsafe_allow_html=True)

        nm = st.session_state.user_name  or "Guest"
        em = st.session_state.user_email or ""
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;padding:6px 2px">
          <div style="width:34px;height:34px;border-radius:50%;flex-shrink:0;
            background:linear-gradient(135deg,#6c63ff,#00d4ff);
            display:flex;align-items:center;justify-content:center;
            font-size:14px;font-weight:700;color:#fff">{nm[0].upper()}</div>
          <div>
            <div style="font-weight:700;font-size:13px">{nm}</div>
            <div style="font-size:10px;color:#7a7a9a;word-break:break-all">{em}</div>
          </div>
        </div>""", unsafe_allow_html=True)

        st.divider()

        langs  = list(LANG_NAMES.keys())
        labels = [LANG_NAMES[k] for k in langs]
        cur    = langs.index(st.session_state.lang) if st.session_state.lang in langs else 0
        sel    = st.selectbox("🌐 Language", labels, index=cur, key="_slang")
        if labels[cur] != sel:
            st.session_state.lang = langs[labels.index(sel)]; st.rerun()

        st.divider()

        nav = [
            ("🎙️ Voice (Main)",  "Voice"),
            ("🏠 Dashboard",     "Dashboard"),
            ("📧 Email",          "Email"),
            ("✈️ Telegram",       "Telegram"),
            ("📱 WhatsApp",       "WhatsApp"),
            ("👤 Profile",        "Profile"),
            ("⚙️ Settings",       "Settings"),
            ("📋 Contacts",       "Contacts"),
            ("🛡️ Admin",          "Admin"),
        ]
        for lbl, pg in nav:
            t = "primary" if st.session_state.page == pg else "secondary"
            if st.button(lbl, key=f"nav_{pg}", use_container_width=True, type=t):
                st.session_state.page = pg; st.rerun()

        st.divider()
        if st.button("🚪 Logout", use_container_width=True, key="logout_btn"):
            st.session_state.logged_in        = False
            st.session_state.auth_provider    = ""
            st.session_state.user_name        = ""
            st.session_state.user_email       = ""
            st.session_state.pin_verified_for = set()
            _log("Logout"); st.rerun()

# ── Voice page (MAIN) ─────────────────────────────────────────────────────────
def page_voice():
    lang = st.session_state.lang

    # Show any status messages
    if st.session_state._bridge_out:
        st.info(f"🔊 NOVA said: *{st.session_state._bridge_out}*")

    if not st.session_state.pin_set:
        st.warning("🔐 No PIN set — say **'set pin 1 2 3 4'** (use your own 4 digits) to create one")

    # Render the voice widget with current state
    nova_reply = st.session_state._bridge_out
    nav_signal = st.session_state._bridge_nav

    # Clear them so they don't repeat
    st.session_state._bridge_out = ""
    st.session_state._bridge_nav = ""

    st.components.v1.html(
        _nova_html(
            lang       = lang,
            logged_in  = st.session_state.logged_in,
            pin_set    = st.session_state.pin_set,
            nova_reply = nova_reply,
            nav_signal = nav_signal,
            emails     = st.session_state.emails,
            tg_msgs    = st.session_state.tg_messages,
            user_name  = st.session_state.user_name,
        ),
        height=700, scrolling=False
    )

    # Bridge input (hidden but required for JS→Python)
    st.markdown("---")
    col1, col2 = st.columns([8, 1])
    with col1:
        cmd = st.text_input(
            "bridge", key="_bridge_in",
            placeholder="NOVA-BRIDGE — auto-filled by voice",
            label_visibility="visible"
        )
    with col2:
        st.write("")
        go = st.button("▶", key="_bgo", type="primary", use_container_width=True)

    if go and cmd.strip() and cmd.strip() != st.session_state._bridge_last:
        st.session_state._bridge_last = cmd.strip()
        process_cmd(cmd.strip())
        st.rerun()

# ── Dashboard ─────────────────────────────────────────────────────────────────
def page_dashboard():
    nm = st.session_state.user_name or "Guest"
    h  = datetime.datetime.now().hour
    greet = "🌅 Good morning" if h<12 else "☀️ Good afternoon" if h<17 else "🌙 Good evening"
    st.markdown(f"## {greet}, {nm}!")
    st.caption(f"📅 {datetime.datetime.now().strftime('%A, %B %d %Y')}")

    if not st.session_state.pin_set:
        st.warning("🔐 No PIN set! Go to **🎙️ Voice** page and say **'set pin 1234'** (your own digits)")

    s = st.session_state.stats
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("📧 Emails Sent",  s["emails_sent"])
    c2.metric("✈️ TG Sent",      s["telegrams_sent"])
    c3.metric("🎙️ Voice Cmds",   s["voice_cmds"])
    c4.metric("📋 Contacts",     len(st.session_state.contacts))

    st.markdown("---")
    qa = st.columns(5)
    for i,(lbl,pg) in enumerate([("🎙️ Voice","Voice"),("📧 Email","Email"),
        ("✈️ Telegram","Telegram"),("📋 Contacts","Contacts"),("🛡️ Admin","Admin")]):
        with qa[i]:
            if st.button(lbl, key=f"dash_{pg}", use_container_width=True):
                st.session_state.page=pg; st.rerun()

    st.markdown("---")
    st.markdown("**📧 Recent Emails**")
    emails = st.session_state.emails
    if not emails:
        col1,col2=st.columns([4,1])
        with col1: st.info("Say **'load emails'** on the Voice page.")
        with col2:
            if st.button("🔄 Load",key="d_em",type="primary"):
                with st.spinner("Loading…"): st.session_state.emails=load_emails()
                st.rerun()
    else:
        cards="".join([f"<div class='ecard'><div class='ef'>{'🔴 ' if e.get('unread') else '⚪ '}{re.sub(r'<[^>]+>','',e['from'])[:26]}</div><div class='es'>{e['subject'][:30]}</div><div class='eb'>{e.get('snippet','')[:70]}</div></div>" for e in emails[:8]])
        st.markdown(f"<div class='hscroll'>{cards}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**✈️ Recent Telegram**")
    msgs = st.session_state.tg_messages
    if not msgs:
        col1,col2=st.columns([4,1])
        with col1: st.info("Say **'load telegram'** on the Voice page.")
        with col2:
            if st.button("🔄 Load",key="d_tg",type="primary"):
                with st.spinner("Loading…"): st.session_state.tg_messages=load_tg()
                st.rerun()
    else:
        cards="".join([f"<div class='tcard'><div class='tf'>{m['from']} · {m['date']}</div><div class='tm'>{m['text'][:80]}</div></div>" for m in reversed(msgs[-6:])])
        st.markdown(f"<div class='hscroll'>{cards}</div>", unsafe_allow_html=True)

# ── Email page ────────────────────────────────────────────────────────────────
def page_email():
    lang = st.session_state.lang
    loc  = _locale(lang)
    st.markdown("## 📧 Email")
    st.info("🎙️ Control by voice — say **'load emails'**, **'read email'**, **'send email'**, **'summarize email'**")

    if not GOOGLE_OK:
        st.error("`pip install google-auth google-auth-oauthlib google-api-python-client`"); return
    if not google_connected():
        st.warning("Gmail not connected — go to ⚙️ Settings.")
        if st.button("⚙️ Settings",type="primary"): st.session_state.page="Settings"; st.rerun()
        return

    col1,col2 = st.columns([3,1])
    with col1: st.markdown("### Inbox")
    with col2:
        if st.button("🔄 Refresh",key="em_ref",type="primary"):
            with st.spinner("Loading…"): st.session_state.emails=load_emails()
            st.rerun()

    emails = st.session_state.emails
    if not emails:
        st.info("Click 🔄 Refresh or say 'load emails' to load your inbox.")
    else:
        cards="".join([f"<div class='ecard'><div class='ef'>{'🔴' if e.get('unread') else '⚪'} {re.sub(r'<[^>]+>','',e['from'])[:24]}</div><div class='es'>{e['subject'][:28]}</div><div class='eb'>{e.get('snippet','')[:70]}</div></div>" for e in emails[:8]])
        st.markdown(f"<div class='hscroll'>{cards}</div>", unsafe_allow_html=True)
        st.markdown("---")
        for i,e in enumerate(emails[:10]):
            frm=re.sub(r'<[^>]+>','',e["from"]).strip()
            pfx="🔴 " if e.get("unread") else "⚪ "
            with st.expander(f"{pfx}**{frm[:26]}** — {e['subject'][:42]}"):
                st.caption(f"📅 {e['date']}")
                body=_clean(e.get("body","") or e.get("snippet",""))
                st.markdown((body[:600]+("…" if len(body)>600 else "")) if body else "*(empty)*")
                b1,b2,b3=st.columns(3)
                with b1:
                    if st.button("↩️ Reply",key=f"rp_{i}"):
                        st.session_state.compose_to=e["from"]
                        st.session_state.compose_sub=f"Re: {e['subject']}"
                        st.session_state.page="Voice"; st.rerun()
                with b2:
                    read_t=(f"Email from {frm}. Subject: {e['subject']}. {_clean(e.get('body','') or e.get('snippet',''))[:400]}").replace("'","").replace('"',"")[:500]
                    st.components.v1.html(f"""<button onclick="(function(){{var u=new SpeechSynthesisUtterance('{read_t}');u.lang='{loc}';u.rate=0.88;window.speechSynthesis.speak(u);}})();" style="padding:7px 14px;background:rgba(168,85,247,.2);border:1px solid rgba(168,85,247,.5);color:#a855f7;border-radius:8px;cursor:pointer;font-size:12px;font-weight:700">🔊 Read</button>""",height=42)
                with b3:
                    if st.button("✨ Summarize",key=f"sum_{i}"):
                        with st.spinner("Summarizing…"):
                            s=summarize_email(e.get("body",""),e["subject"])
                        st.info(f"**Summary:** {s}")

    st.markdown("---")
    st.markdown("### ✍️ Compose (or say **'send email'** by voice)")
    if "send_email" in st.session_state.pin_verified_for or not st.session_state.pin_set:
        to  =st.text_input("To:",    value=st.session_state.compose_to,  placeholder="email@example.com",key="em_to")
        sub =st.text_input("Subject:",value=st.session_state.compose_sub,placeholder="Subject",key="em_sub")
        body=st.text_area("Message:",value=st.session_state.compose_body,placeholder="Your message…",height=120,key="em_body")
        if st.button("📤 Send Email",type="primary",key="em_send"):
            if to.strip() and "@" in to and sub.strip() and body.strip():
                ok,msg=do_send_email(to.strip(),sub.strip(),body.strip())
                if ok: st.success(f"✅ {msg}"); st.session_state.compose_to=st.session_state.compose_sub=st.session_state.compose_body=""
                else: st.error(f"❌ {msg}")
            else: st.error("Fill all fields.")
    else:
        st.info("🔐 PIN required to compose. Go to **🎙️ Voice** page and say **'send email'** — NOVA will ask for your PIN.")
        if st.button("🎙️ Go to Voice Page",type="primary"):
            st.session_state.page="Voice"; st.rerun()

# ── Telegram page ─────────────────────────────────────────────────────────────
def page_telegram():
    lang=st.session_state.lang; loc=_locale(lang)
    st.markdown("## ✈️ Telegram")
    st.info("🎙️ Say **'load telegram'**, **'read telegram'**, **'send telegram'** on Voice page")

    if not tg_ok():
        st.warning("Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `nova.env`."); return

    col1,col2=st.columns([3,1])
    with col1: st.markdown("### Messages")
    with col2:
        if st.button("🔄 Refresh",key="tg_ref",type="primary"):
            with st.spinner("Loading…"): st.session_state.tg_messages=load_tg()
            st.rerun()

    msgs=st.session_state.tg_messages
    if not msgs:
        st.info("Click 🔄 Refresh or say 'load telegram'")
    else:
        cards="".join([f"<div class='tcard'><div class='tf'>{m['from']} · {m['date']}</div><div class='tm'>{m['text'][:80]}</div></div>" for m in reversed(msgs[-8:])])
        st.markdown(f"<div class='hscroll'>{cards}</div>",unsafe_allow_html=True)
        st.markdown("---")
        for i,m in enumerate(reversed(msgs[-12:])):
            c1,c2,c3=st.columns([1,6,2])
            with c1:
                init=m["from"][0].upper() if m["from"] else "?"
                st.markdown(f'<div style="width:30px;height:30px;border-radius:50%;background:linear-gradient(135deg,#0088cc,#00aaff);display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#fff">{init}</div>',unsafe_allow_html=True)
            with c2: st.markdown(f"**{m['from']}:** {m['text']}")
            with c3: st.caption(m["date"])
            st.divider()

    st.markdown("---")
    st.markdown("### 📤 Send")
    if "send_tg" in st.session_state.pin_verified_for or not st.session_state.pin_set:
        txt=st.text_area("Message:",height=80,key="tg_txt")
        if st.button("✈️ Send",type="primary",key="tg_send"):
            if txt.strip():
                ok,msg=send_tg(txt.strip())
                if ok: st.success(f"✅ {msg}")
                else: st.error(f"❌ {msg}")
    else:
        st.info("🔐 Go to **🎙️ Voice** page and say **'send telegram'** — NOVA asks for PIN then sends.")
        if st.button("🎙️ Go to Voice Page",type="primary"):
            st.session_state.page="Voice"; st.rerun()

# ── WhatsApp ──────────────────────────────────────────────────────────────────
def page_whatsapp():
    st.markdown("## 📱 WhatsApp")
    st.info("WhatsApp requires Twilio credentials.")
    st.link_button("🌐 Open WhatsApp Web","https://web.whatsapp.com")

# ── Profile ───────────────────────────────────────────────────────────────────
def page_profile():
    st.markdown("## 👤 Profile")
    if google_connected():
        info=google_info()
        if info:
            st.session_state.user_name=info.get("name",st.session_state.user_name)
            st.session_state.user_email=info.get("email",st.session_state.user_email)
            if info.get("picture"): st.image(info["picture"],width=80)
        st.success(f"✅ Google: {st.session_state.user_email}")
    with st.form("pf"):
        n=st.text_input("Name:", value=st.session_state.user_name)
        e=st.text_input("Email:",value=st.session_state.user_email)
        st.text_input("Phone:",placeholder="+91 XXXXXXXXXX")
        if st.form_submit_button("💾 Save",type="primary"):
            st.session_state.user_name=n; st.session_state.user_email=e
            _log(f"Profile: {n}"); st.success("✅ Saved!")

# ── Settings ──────────────────────────────────────────────────────────────────
def page_settings():
    st.markdown("## ⚙️ Settings")
    t1,t2=st.tabs(["🔗 Gmail","🔧 Services"])
    with t1:
        if google_connected():
            info=google_info(); st.success(f"✅ Connected: **{info.get('email','')}**")
            if st.button("🔌 Disconnect",key="disc"):
                if Path(TOKEN_FILE).exists(): os.remove(TOKEN_FILE)
                st.success("Disconnected."); st.rerun()
        else:
            st.error("❌ Not connected")
            if not Path(CREDENTIALS_FILE).exists():
                st.warning(f"`{CREDENTIALS_FILE}` not found.")
                st.markdown("""1. [Google Cloud Console](https://console.cloud.google.com) → Enable Gmail API\n2. OAuth 2.0 → Desktop app → Download `credentials.json`\n3. Place in app folder → Restart → Connect""")
            else:
                if not st.session_state.get("_google_auth_url"):
                    _start_google_oauth()
                auth_url = st.session_state.get("_google_auth_url")
                if auth_url:
                    st.link_button("🔗 Connect Gmail with Google", auth_url, type="primary")
    with t2:
        a,b,c=st.columns(3)
        with a: st.success("📧 Gmail ✅") if google_connected() else st.error("📧 Gmail ❌")
        with b:
            connected, message = telegram_status()
            if connected:
                st.success(f"✈️ {message}")
                st.caption("Open your bot in Telegram and send /start before loading messages.")
            else:
                st.warning(f"✈️ {message}")
        with c: st.success("🌐 Requests ✅") if REQUESTS_OK else st.error("🌐 Requests ❌")

# ── Contacts ──────────────────────────────────────────────────────────────────
def page_contacts():
    st.markdown("## 📋 Contacts")
    t1,t2=st.tabs(["👥 All","➕ Add"])
    with t1:
        srch=st.text_input("🔍 Search:",placeholder="Name or email",key="cs")
        contacts=st.session_state.contacts
        if srch: contacts=[c for c in contacts if srch.lower() in c["name"].lower() or srch.lower() in c.get("email","").lower()]
        for i,c in enumerate(contacts):
            a,b,cc,d=st.columns([1,3,3,1])
            with a: st.markdown(f'<div style="width:30px;height:30px;border-radius:50%;background:linear-gradient(135deg,#6c63ff,#00d4ff);display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#fff">{c["name"][0].upper()}</div>',unsafe_allow_html=True)
            with b: st.markdown(f"**{c['name']}**")
            with cc: st.caption(c.get("email",""))
            with d:
                if st.button("📧",key=f"ce_{i}"):
                    st.session_state.compose_to=c.get("email",""); st.session_state.page="Email"; st.rerun()
            st.divider()
    with t2:
        with st.form("cadd",clear_on_submit=True):
            nm=st.text_input("Name *"); em=st.text_input("Email *"); ph=st.text_input("Phone")
            if st.form_submit_button("💾 Save",type="primary"):
                if not nm.strip(): st.error("Name required.")
                elif "@" not in em: st.error("Valid email required.")
                else:
                    st.session_state.contacts.append({"name":nm.strip(),"email":em.strip(),"phone":ph.strip()})
                    _log(f"Contact: {nm}"); st.success(f"✅ {nm} saved!")

# ── Admin ─────────────────────────────────────────────────────────────────────
def page_admin():
    st.markdown("## 🛡️ Admin")
    t1,t2,t3=st.tabs(["📊 Stats","🔐 PIN","📋 Log"])
    with t1:
        s=st.session_state.stats; a,b,c,d=st.columns(4)
        a.metric("📧 Emails",s["emails_sent"]); b.metric("✈️ Telegrams",s["telegrams_sent"])
        c.metric("🔑 Logins",s["logins"]); d.metric("🎙️ Voice Cmds",s["voice_cmds"])
        st.markdown("---")
        if st.session_state.pin_set: st.success("🔐 PIN is set.")
        else: st.error("🔐 No PIN — say 'set pin 1234' on Voice page (use your own digits)")
    with t2:
        st.markdown("### 🔐 Voice PIN")
        st.info("Say **'set pin'** on the Voice page to set by voice.\nOr use the form below.")
        if st.session_state.pin_set: st.success(f"✅ PIN configured.")
        else: st.error("❌ No PIN set.")
        with st.form("pinf",clear_on_submit=True):
            p1=st.text_input("New PIN (4 digits):",type="password",max_chars=4)
            p2=st.text_input("Confirm:",type="password",max_chars=4)
            if st.form_submit_button("💾 Save",type="primary"):
                p1,p2=p1.strip(),p2.strip()
                if not p1.isdigit() or len(p1)!=4: st.error("4 digits only.")
                elif p1!=p2: st.error("PINs don't match.")
                else:
                    st.session_state.user_pin=p1; st.session_state.pin_set=True
                    st.session_state.pin_verified_for=set()
                    _log("PIN set"); st.success("✅ PIN saved!")
        if st.session_state.pin_set:
            col1,col2=st.columns(2)
            with col1:
                if st.button("🔄 Reset Verifications",key="rv"):
                    st.session_state.pin_verified_for=set(); st.success("Reset.")
            with col2:
                if st.button("🗑️ Remove PIN",key="rmp"):
                    st.session_state.user_pin=""; st.session_state.pin_set=False
                    st.session_state.pin_verified_for=set(); st.rerun()
    with t3:
        log=st.session_state.activity_log
        if not log: st.info("No activity yet.")
        for entry in log[:50]:
            a,b=st.columns([1,5])
            with a: st.caption(entry["time"])
            with b: st.markdown(entry["action"])
            st.divider()

# ── Login page ────────────────────────────────────────────────────────────────
def page_login():
    st.markdown("""<style>
section[data-testid="stSidebar"]{display:none!important;}
[data-testid="collapsedControl"]{display:none!important;}
</style>""", unsafe_allow_html=True)

    _,col,_ = st.columns([1,2,1])
    with col:
        st.markdown("""
        <div style="text-align:center;padding:20px 0 10px">
          <div style="font-size:52px;margin-bottom:8px">🎙️</div>
          <div style="font-size:28px;font-weight:900;letter-spacing:6px;
            background:linear-gradient(135deg,#6c63ff,#00d4ff);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent">NOVA</div>
          <div style="font-size:10px;color:#7a7a9a;letter-spacing:3px;margin-top:4px">
            VOICE AI ASSISTANT</div>
          <div style="font-size:12px;color:#555;margin-top:8px">
            Secure Google sign-in · Voice controls after login</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("### Sign in with Google")
        if not GOOGLE_OK:
            st.error("Google sign-in packages are missing. Install requirements.txt and restart NOVA.")
        elif not CREDENTIALS_FILE.exists():
            st.error("Google OAuth client file `credentials.json` is missing.")
        else:
            if not st.session_state.get("_google_auth_url"):
                _start_google_oauth()
            auth_url = st.session_state.get("_google_auth_url")
            if auth_url:
                st.link_button("🔵 Continue with Google", auth_url, type="primary",
                               use_container_width=True)
            st.caption("Google handles your password; NOVA never receives it.")

        st.markdown("---")
        st.markdown("### Or use a local account")
        tl,ts=st.tabs(["🔑 Login","✨ Sign Up"])
        with tl:
            with st.form("lf"):
                le=st.text_input("Email",placeholder="you@example.com",key="l_e")
                lp=st.text_input("Password",type="password",key="l_p")
                if st.form_submit_button("🔑 Login",type="primary",use_container_width=True):
                    e=le.strip().lower(); p=lp.strip()
                    if not e or not p: st.error("Enter email and password.")
                    elif e not in st.session_state.local_users: st.error("No account. Sign up first.")
                    elif not _chkpw(p,st.session_state.local_users[e]["password"]): st.error("❌ Wrong password.")
                    else:
                        st.session_state.user_name=st.session_state.local_users[e]["name"]
                        st.session_state.auth_provider="local"
                        st.session_state.user_email=e; st.session_state.logged_in=True
                        st.session_state.stats["logins"]+=1; _log(f"Login: {e}"); st.rerun()
        with ts:
            with st.form("sf"):
                sn=st.text_input("Full Name",key="s_n"); se=st.text_input("Email",key="s_e")
                sp=st.text_input("Password",type="password",placeholder="Min 6 chars",key="s_p")
                sp2=st.text_input("Confirm",type="password",key="s_p2")
                if st.form_submit_button("✨ Create Account",type="primary",use_container_width=True):
                    n=sn.strip(); e=se.strip().lower(); p=sp.strip(); p2=sp2.strip()
                    if not n: st.error("Name required.")
                    elif "@" not in e: st.error("Valid email required.")
                    elif len(p)<6: st.error("Min 6 chars.")
                    elif p!=p2: st.error("Passwords don't match.")
                    elif e in st.session_state.local_users: st.error("Exists. Login instead.")
                    else:
                        st.session_state.local_users[e]={"name":n,"password":_hash(p)}
                        st.session_state.auth_provider="local"
                        st.session_state.user_name=n; st.session_state.user_email=e
                        st.session_state.logged_in=True
                        st.session_state.stats["logins"]+=1; _log(f"Signup: {e}"); st.rerun()

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    _complete_google_oauth()

    if (st.session_state.logged_in
            and st.session_state.auth_provider not in {"google", "local"}):
        st.session_state.logged_in = False
        st.session_state.user_name = ""
        st.session_state.user_email = ""

    # Not logged in → login page
    if not st.session_state.logged_in:
        page_login(); return

    # Auto-fill from Google
    if google_connected() and not st.session_state.user_name:
        info=google_info()
        if info:
            st.session_state.user_name=info.get("name","")
            st.session_state.user_email=info.get("email","")

    render_sidebar()

    # Process bridge command (from voice page)
    bi = st.session_state.get("_bridge_in","").strip()
    if bi and bi != st.session_state.get("_bridge_last",""):
        st.session_state._bridge_last = bi
        process_cmd(bi)
        # Don't rerun here — page_voice will rerun after rendering

    page = st.session_state.page
    {
        "Voice":     page_voice,
        "Dashboard": page_dashboard,
        "Email":     page_email,
        "Telegram":  page_telegram,
        "WhatsApp":  page_whatsapp,
        "Profile":   page_profile,
        "Settings":  page_settings,
        "Contacts":  page_contacts,
        "Admin":     page_admin,
    }.get(page, page_voice)()


if __name__ == "__main__":
    main()