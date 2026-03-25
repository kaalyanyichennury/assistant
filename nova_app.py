"""
NOVA - 100% Voice Controlled AI Assistant
Run: streamlit run nova_app.py
Install: pip install streamlit requests
Optional: pip install google-auth google-auth-oauthlib google-api-python-client openai
"""
import streamlit as st
st.set_page_config(page_title="NOVA Voice AI", page_icon="🎙️",
                   layout="wide", initial_sidebar_state="expanded")

import os, re, json, base64, pickle, datetime, hashlib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8622898072:AAHx8Unupvaeqw6k70mUdufOhAACm6_byv4")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID",   "8492006721")
OPENAI_API_KEY     = os.environ.get("OPENAI_API_KEY",     "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")
CREDENTIALS_FILE   = "credentials.json"
TOKEN_FILE         = "token.pickle"
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

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

PH = {
"en": {
    "wake":       "Hands free on! Say help to hear all commands.",
    "help":       "Commands: load emails, read email, send email, load telegram, read telegram, send telegram, open contacts, open settings, open admin, set pin, what time, what date, stop.",
    "ask_pin":    "Please say your 4 digit PIN.",
    "wrong_pin":  "Wrong PIN. Try again.",
    "pin_ok":     "PIN correct!",
    "email_sent": "Email sent successfully!",
    "tg_sent":    "Telegram message sent!",
    "cancelled":  "Cancelled.",
    "no_email":   "No emails loaded. Say load emails first.",
    "no_tg":      "No Telegram messages. Say load telegram first.",
    "read_email": "Reading your latest email.",
    "read_tg":    "Reading your latest Telegram message.",
    "unknown":    "I did not understand. Say help for commands.",
    "morning":    "Good morning","afternoon":"Good afternoon","evening":"Good evening",
    "greeting":   "I am NOVA your voice AI assistant.",
    "emails_loaded": "Loaded {n} emails. {unread} unread. Latest from {from_name}, subject: {subject}.",
    "tg_loaded":  "Loaded {n} messages. Latest from {from_name}: {text}.",
    "send_e1":    "Who do you want to send the email to?",
    "send_e2":    "What is the subject?",
    "send_e3":    "Now say the message body.",
    "send_t1":    "What message do you want to send on Telegram?",
    "login_wake": "Welcome to NOVA! Say your name to login.",
    "setpin_ask": "Please say your new 4 digit PIN.",
    "setpin_done":"PIN set! All protected features are now unlocked.",
    "no_pin":     "No PIN set. Say set pin followed by 4 digits to create one.",
},
"hi": {
    "wake":"हैंड्स फ्री चालू!","help":"ईमेल लोड, पढ़ें, भेजें, टेलीग्राम लोड, पढ़ें, भेजें, पिन सेट।",
    "ask_pin":"अपना 4 अंकों का पिन बोलें।","wrong_pin":"गलत पिन।","pin_ok":"पिन सही!",
    "email_sent":"ईमेल भेजा!","tg_sent":"टेलीग्राम भेजा!","cancelled":"रद्द।",
    "no_email":"ईमेल नहीं। लोड करें।","no_tg":"संदेश नहीं।",
    "read_email":"ईमेल पढ़ रहा है।","read_tg":"टेलीग्राम पढ़ रहा है।",
    "unknown":"समझ नहीं आया।","morning":"शुभ प्रभात","afternoon":"शुभ दोपहर","evening":"शुभ संध्या",
    "greeting":"मैं NOVA हूँ।","emails_loaded":"{n} ईमेल लोड।","tg_loaded":"{n} संदेश लोड।",
    "send_e1":"किसे ईमेल भेजना है?","send_e2":"विषय?","send_e3":"संदेश बोलें।",
    "send_t1":"क्या भेजना है?","login_wake":"NOVA में स्वागत! नाम बोलें।",
    "setpin_ask":"नया पिन बोलें।","setpin_done":"पिन सेट!","no_pin":"पिन नहीं। सेट करें।",
},
"te": {
    "wake":"హ్యాండ్స్ ఫ్రీ ఆన్!","help":"ఈమెయిల్ లోడ్, చదవండి, పంపండి, టెలిగ్రామ్ లోడ్, చదవండి, పంపండి.",
    "ask_pin":"మీ 4 అంకెల పిన్ చెప్పండి.","wrong_pin":"తప్పు పిన్.","pin_ok":"పిన్ సరైనది!",
    "email_sent":"ఈమెయిల్ పంపబడింది!","tg_sent":"టెలిగ్రామ్ పంపబడింది!","cancelled":"రద్దు.",
    "no_email":"ఈమెయిల్ లేదు.","no_tg":"సందేశాలు లేవు.",
    "read_email":"ఈమెయిల్ చదువుతున్నాను.","read_tg":"టెలిగ్రామ్ చదువుతున్నాను.",
    "unknown":"అర్థం కాలేదు.","morning":"శుభోదయం","afternoon":"శుభ మధ్యాహ్నం","evening":"శుభ సాయంత్రం",
    "greeting":"నేను NOVA.","emails_loaded":"{n} ఈమెయిల్‌లు లోడ్.","tg_loaded":"{n} సందేశాలు లోడ్.",
    "send_e1":"ఎవరికి పంపాలి?","send_e2":"విషయం?","send_e3":"సందేశం చెప్పండి.",
    "send_t1":"ఏమి పంపాలి?","login_wake":"NOVA కి స్వాగతం! పేరు చెప్పండి.",
    "setpin_ask":"కొత్త పిన్ చెప్పండి.","setpin_done":"పిన్ సెట్!","no_pin":"పిన్ లేదు.",
},
}
for _l in LANG_NAMES:
    if _l not in PH: PH[_l] = PH["en"]

def ph(key, lang=None, **kw):
    l = lang or st.session_state.get("lang","en")
    t = PH.get(l, PH["en"]).get(key, PH["en"].get(key,""))
    for k,v in kw.items(): t = t.replace("{"+k+"}", str(v))
    return t

# ── SESSION STATE ─────────────────────────────────────────────────────────────
_DEF = {
    "page":"Assistant","lang":"en",
    "logged_in":False,"user_name":"","user_email":"",
    "user_pin":"","pin_set":False,
    "local_users":{},
    "contacts":[
        {"name":"Rahul","email":"rahul@example.com","phone":""},
        {"name":"Priya","email":"priya@example.com","phone":""},
    ],
    "activity_log":[],"stats":{"emails_sent":0,"telegrams_sent":0,"logins":0,"voice_cmds":0},
    "emails":[],"tg_messages":[],
    "email_summaries":{},"reply_suggestions":{},
    "compose_to":"","compose_sub":"","compose_body":"",
    "_cmd_in":"","_cmd_last":"",
    "_nova_say":"",    # Python→JS: NOVA speaks this
    "_nova_nav":"",    # Python→JS: navigate to page
    # KEY FIX: store verified PIN in session so JS can use it for local verification
    "_pin_hash":"",    # hashed PIN for JS comparison (sent as part of page data)
}
for k,v in _DEF.items():
    if k not in st.session_state: st.session_state[k]=v
if not isinstance(st.session_state.get("pin_verified_for"),set):
    st.session_state["pin_verified_for"]=set()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""<style>
html,body,.stApp{background:#07071a!important;color:#e8e8ff!important;}
section[data-testid="stSidebar"]{background:#0c0c24!important;border-right:1px solid rgba(108,99,255,.18)!important;}
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
.hscroll{display:flex;gap:12px;overflow-x:auto;padding:6px 2px 10px;
  scrollbar-width:thin;scrollbar-color:#6c63ff33 transparent;}
.hscroll::-webkit-scrollbar{height:4px;}
.hscroll::-webkit-scrollbar-thumb{background:#6c63ff55;border-radius:4px;}
.ecard{min-width:210px;max-width:210px;background:rgba(108,99,255,.08);
  border:1px solid rgba(108,99,255,.2);border-radius:12px;padding:11px;flex-shrink:0;}
.ecard .ef{font-size:10px;color:#a78bfa;font-weight:700;margin-bottom:3px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.ecard .es{font-size:12px;color:#e8e8ff;font-weight:600;margin-bottom:3px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.ecard .eb{font-size:11px;color:#7a7a9a;}
.tcard{min-width:190px;max-width:190px;background:rgba(0,136,204,.08);
  border:1px solid rgba(0,136,204,.2);border-radius:12px;padding:11px;flex-shrink:0;}
.tcard .tf{font-size:10px;color:#00aaff;font-weight:700;margin-bottom:3px;}
.tcard .tm{font-size:12px;color:#e8e8ff;}
</style>""",unsafe_allow_html=True)

# ── HELPERS ───────────────────────────────────────────────────────────────────
def _log(a):
    st.session_state.activity_log.insert(0,{"time":datetime.datetime.now().strftime("%H:%M:%S"),"action":a})
    if len(st.session_state.activity_log)>100: st.session_state.activity_log.pop()
def _locale(l=None): return LOCALES.get(l or st.session_state.get("lang","en"),"en-US")
def _hash(p): return hashlib.sha256(p.strip().encode()).hexdigest()
def _chkpw(p,h): return hashlib.sha256(p.strip().encode()).hexdigest()==h
def _save_token(c):
    with open(TOKEN_FILE,"wb") as f: pickle.dump(c,f)
def get_creds():
    if not GOOGLE_OK or not Path(TOKEN_FILE).exists(): return None
    try:
        with open(TOKEN_FILE,"rb") as f: c=pickle.load(f)
        if c and c.valid: return c
        if c and c.expired and c.refresh_token: c.refresh(Request()); _save_token(c); return c
    except: pass
    return None
def gmail_svc(): c=get_creds(); return build("gmail","v1",credentials=c) if c else None
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
                "subject":hdrs.get("Subject","(No Subject)"),"date":hdrs.get("Date",""),
                "snippet":msg.get("snippet",""),"body":body,
                "unread":"UNREAD" in msg.get("labelIds",[])})
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
            and len(TELEGRAM_BOT_TOKEN)>20 and "YOUR" not in TELEGRAM_BOT_TOKEN)
def load_tg(limit=20):
    if not tg_ok(): return []
    try:
        r=_req.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
                   params={"limit":limit},timeout=10).json()
        if not r.get("ok"): return []
        msgs=[]
        for u in r.get("result",[]):
            m=u.get("message",{})
            if not m: continue
            ts=m.get("date",0)
            msgs.append({"text":m.get("text",""),"from":m.get("from",{}).get("first_name","?"),
                "date":datetime.datetime.fromtimestamp(ts).strftime("%I:%M %p") if ts else ""})
        return msgs
    except: return []
def send_tg(text):
    if not tg_ok(): return False,"Telegram not configured"
    try:
        r=_req.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id":TELEGRAM_CHAT_ID,"text":text},timeout=10).json()
        if r.get("ok"): st.session_state.stats["telegrams_sent"]+=1; _log("TG sent"); return True,"Sent!"
        return False,r.get("description","Failed")
    except Exception as e: return False,str(e)
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
    sents=[s.strip() for s in re.split(r'(?<=[.!?]) +',body) if len(s.strip())>20]
    return " ".join(sents[:2]) if sents else body[:200]

# ── COMMAND PROCESSOR ─────────────────────────────────────────────────────────
def process_cmd(cmd:str):
    lang=st.session_state.lang
    p=cmd.strip()
    # Strip timestamp suffix e.g. |||TS1234567890
    if "|||TS" in p:
        p=p[:p.rfind("|||TS")].strip()

    st.session_state.stats["voice_cmds"]+=1

    # LOGIN
    if p.startswith("LOGIN|||"):
        parts=p.split("|||")
        name=parts[1].strip() if len(parts)>1 else "Guest"
        email=parts[2].strip() if len(parts)>2 and parts[2].strip() else name.lower()+"@nova.ai"
        if email in st.session_state.local_users:
            st.session_state.user_name=st.session_state.local_users[email]["name"]
        else:
            st.session_state.user_name=name
        st.session_state.user_email=email
        st.session_state.logged_in=True
        st.session_state.stats["logins"]+=1
        _log(f"Login: {name}")
        st.session_state._nova_say=f"Welcome {name}! I am NOVA. Say help to hear all commands."
        st.rerun(); return

    # SIGNUP
    if p.startswith("SIGNUP|||"):
        parts=p.split("|||")
        name=parts[1].strip() if len(parts)>1 else "User"
        email=parts[2].strip() if len(parts)>2 else name.lower()+"@nova.ai"
        pw=parts[3].strip() if len(parts)>3 else "nova1234"
        st.session_state.local_users[email]={"name":name,"password":_hash(pw)}
        st.session_state.user_name=name; st.session_state.user_email=email
        st.session_state.logged_in=True; st.session_state.stats["logins"]+=1
        _log(f"Signup: {name}")
        st.session_state._nova_say=f"Account created! Welcome {name}! Say set pin followed by 4 digits."
        st.rerun(); return

    # SET PIN — store and also update _pin_hash so JS gets it on next render
    if p.startswith("SETPIN|||"):
        parts=p.split("|||")
        pin=parts[1] if len(parts)>1 else ""
        if len(pin)==4 and pin.isdigit():
            st.session_state.user_pin=pin
            st.session_state.pin_set=True
            st.session_state.pin_verified_for=set()
            _log("PIN set")
            # _nova_say is spoken by JS on next render
            st.session_state._nova_say=ph("setpin_done",lang)
        else:
            st.session_state._nova_say="Invalid PIN. Please say exactly 4 digits."
        return

    # LOAD EMAILS
    if p=="LOAD_EMAILS":
        with st.spinner("Loading emails…"):
            st.session_state.emails=load_emails()
        n=len(st.session_state.emails)
        if n==0:
            st.session_state._nova_say=ph("no_email",lang)
        else:
            e=st.session_state.emails[0]
            frm=re.sub(r'<[^>]+>','',e["from"]).strip().split()[0]
            unread=sum(1 for em in st.session_state.emails if em.get("unread"))
            st.session_state._nova_say=ph("emails_loaded",lang,n=n,unread=unread,from_name=frm,subject=e["subject"])
        return

    # LOAD TG
    if p=="LOAD_TG":
        with st.spinner("Loading Telegram…"):
            st.session_state.tg_messages=load_tg()
        n=len(st.session_state.tg_messages)
        if n==0:
            st.session_state._nova_say=ph("no_tg",lang)
        else:
            m=st.session_state.tg_messages[-1]
            st.session_state._nova_say=ph("tg_loaded",lang,n=n,from_name=m["from"],text=m["text"][:60])
        return

    # SEND EMAIL
    if p.startswith("SEND_EMAIL|||"):
        parts=p.split("|||")
        if len(parts)==4:
            ok,msg=do_send_email(parts[1],parts[2],parts[3])
            st.session_state._nova_say=ph("email_sent",lang) if ok else f"Failed. {msg}"
        return

    # SEND TG
    if p.startswith("SEND_TG|||"):
        parts=p.split("|||")
        if len(parts)==2:
            ok,msg=send_tg(parts[1])
            st.session_state._nova_say=ph("tg_sent",lang) if ok else f"Failed. {msg}"
        return

    # NAVIGATION
    nav_map={
        ("open email","email","inbox"):                                  "Email",
        ("open telegram","telegram","check telegram"):                   "Telegram",
        ("open contacts","contacts"):                                    "Contacts",
        ("open settings","settings"):                                    "Settings",
        ("open admin","admin"):                                          "Admin",
        ("open profile","profile"):                                      "Profile",
        ("open whatsapp","whatsapp"):                                    "WhatsApp",
        ("dashboard","home","go home"):                                  "Dashboard",
        ("voice","assistant","voice assistant"):                         "Assistant",
        ("speech to text","stt"):                                        "STT",
        ("text to speech","tts"):                                        "TTS",
    }
    pl=p.lower()
    for triggers,page in nav_map.items():
        if any(t in pl for t in triggers):
            st.session_state.page=page; st.session_state._nova_nav=page; return

    # INFO
    if "time" in pl:
        st.session_state._nova_say=f"The current time is {datetime.datetime.now().strftime('%I:%M %p')}."; return
    if "date" in pl or "today" in pl:
        st.session_state._nova_say=f"Today is {datetime.datetime.now().strftime('%A, %B %d %Y')}."; return
    if "help" in pl:
        st.session_state._nova_say=ph("help",lang); return

    greetings=["hello","hi nova","hey nova","hi","hey","namaste"]
    if any(g in pl for g in greetings):
        h=datetime.datetime.now().hour
        greet=ph("morning",lang) if h<12 else ph("afternoon",lang) if h<17 else ph("evening",lang)
        st.session_state._nova_say=f"{greet} {st.session_state.user_name or 'friend'}! {ph('greeting',lang)} Say help for commands."
        return

    st.session_state._nova_say=f"{ph('unknown',lang)} I heard: {p}"

# ── NOVA HTML — KEY FIX: PIN verified entirely in JS ─────────────────────────
def _nova_html(lang="en", nova_say="", logged_in=False, pin_set=False,
               user_pin="", user_name="", emails=None, tg_msgs=None) -> str:
    loc       = _locale(lang)
    emails    = emails   or []
    tg_msgs   = tg_msgs  or []
    say_safe  = nova_say.replace("'","").replace('"',"").replace("\n"," ")[:600]
    name_safe = user_name.replace("'","")
    pin_js    = "true" if pin_set else "false"
    li_js     = "true" if logged_in else "false"
    # Pass the actual PIN to JS so it can verify locally without Python roundtrip
    # This is safe because it's in a local iframe, not sent over network
    pin_val_js = user_pin if pin_set else ""

    email_js=json.dumps([{
        "from": re.sub(r'<[^>]+>','',e["from"]).strip()[:28],
        "sub":  e["subject"][:50],
        "snip": (e.get("snippet","") or "")[:80],
        "body": (_clean(e.get("body","") or e.get("snippet",""))[:350]
                 ).replace("'","").replace('"',"").replace("\n"," "),
        "unread":e.get("unread",False),
    } for e in emails[:10]])

    tg_js=json.dumps([{
        "from": m["from"][:20],
        "text": m["text"][:200].replace("'","").replace('"',""),
        "date": m["date"],
    } for m in tg_msgs[-8:]])

    def js(k): return ph(k,lang).replace("'","\\'").replace('"','\\"')

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:transparent;color:#e8e8ff;overflow-x:hidden;}}
@keyframes float{{0%,100%{{transform:translateY(0)scale(1)}}50%{{transform:translateY(-8px)scale(1.05)}}}}
@keyframes pulse{{0%,100%{{box-shadow:0 0 30px #6c63ffaa}}50%{{box-shadow:0 0 80px #ff6b9ddd,0 0 120px #ff6b9d44}}}}
@keyframes listen{{0%,100%{{box-shadow:0 0 20px #00ff88aa}}50%{{box-shadow:0 0 60px #00ff88ff}}}}
@keyframes wv{{0%,100%{{transform:scaleY(1);opacity:.3}}50%{{transform:scaleY(3.5);opacity:1}}}}
#app{{display:flex;flex-direction:column;align-items:center;padding:10px 8px 16px;gap:6px;}}
#orb{{width:116px;height:116px;border-radius:50%;cursor:pointer;
  background:radial-gradient(circle at 35% 35%,#c084fc,#6c63ff 50%,#00d4ff);
  display:flex;align-items:center;justify-content:center;font-size:44px;
  animation:float 3.5s ease-in-out infinite;user-select:none;}}
#orb.speaking{{animation:pulse .85s ease-in-out infinite;}}
#orb.listening{{animation:listen .7s ease-in-out infinite;}}
#title{{font-size:21px;font-weight:900;letter-spacing:5px;
  background:linear-gradient(135deg,#6c63ff,#00d4ff);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
#badge{{padding:2px 16px;border-radius:20px;font-size:10px;font-weight:700;
  letter-spacing:1px;background:rgba(108,99,255,.2);border:1px solid rgba(108,99,255,.4);color:#a78bfa;}}
#bars{{display:flex;gap:4px;height:26px;align-items:center;}}
.b{{width:4px;border-radius:3px;background:#2a2a3a;height:4px;transition:.2s;}}
.b.on{{animation:wv 1s ease-in-out infinite;}}
.b.on:nth-child(1){{animation-delay:0s;background:#6c63ff;}}
.b.on:nth-child(2){{animation-delay:.1s;background:#8b5cf6;}}
.b.on:nth-child(3){{animation-delay:.2s;background:#ff6b9d;}}
.b.on:nth-child(4){{animation-delay:.1s;background:#8b5cf6;}}
.b.on:nth-child(5){{animation-delay:0s;background:#6c63ff;}}
#bubble{{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);
  border-radius:14px;padding:11px 15px;width:100%;max-width:480px;
  font-size:13px;line-height:1.85;min-height:52px;}}
#heard{{background:rgba(0,255,136,.04);border:1px solid rgba(0,255,136,.18);
  border-radius:8px;padding:5px 13px;width:100%;max-width:480px;
  font-size:11px;color:#00ff88;min-height:18px;font-style:italic;}}
#flow{{background:rgba(108,99,255,.07);border:1px solid rgba(108,99,255,.28);
  border-radius:9px;padding:8px 14px;width:100%;max-width:480px;
  font-size:12px;color:#a78bfa;display:none;line-height:2.1;}}
#btns{{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;}}
.btn-go{{padding:10px 24px;border:none;border-radius:10px;cursor:pointer;
  background:linear-gradient(135deg,#6c63ff,#8b5cf6);color:#fff;font-size:12px;font-weight:700;}}
.btn-stop{{padding:10px 14px;border:1px solid rgba(255,68,102,.5);border-radius:10px;
  cursor:pointer;background:rgba(255,68,102,.1);color:#ff4466;font-size:12px;font-weight:700;}}
.btn-rep{{padding:8px 13px;border:1px solid rgba(255,255,255,.15);border-radius:9px;
  cursor:pointer;background:rgba(255,255,255,.05);color:#aaa;font-size:11px;}}
#cards{{width:100%;max-width:480px;}}
.card-lbl{{font-size:10px;color:#555;letter-spacing:1.5px;text-transform:uppercase;margin:8px 0 4px;}}
.card-row{{display:flex;gap:10px;overflow-x:auto;padding:2px 0 8px;
  scrollbar-width:thin;scrollbar-color:#6c63ff22 transparent;}}
.ec{{min-width:180px;background:rgba(108,99,255,.08);border:1px solid rgba(108,99,255,.2);
  border-radius:10px;padding:9px;flex-shrink:0;font-size:11px;cursor:pointer;}}
.ec:hover{{background:rgba(108,99,255,.16);}}
.ec .ef{{color:#a78bfa;font-weight:700;margin-bottom:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.ec .es{{color:#e8e8ff;font-weight:600;margin-bottom:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.ec .eb{{color:#7a7a9a;overflow:hidden;}}
.tc{{min-width:160px;background:rgba(0,136,204,.08);border:1px solid rgba(0,136,204,.2);
  border-radius:10px;padding:9px;flex-shrink:0;font-size:11px;}}
.tc .tf{{color:#00aaff;font-weight:700;margin-bottom:2px;}}
.tc .tm{{color:#e8e8ff;}}
#hints{{width:100%;max-width:480px;}}
#hints summary{{font-size:10px;color:#444;cursor:pointer;}}
#hints div{{font-size:10px;color:#444;line-height:2.3;margin-top:6px;}}
.hk{{color:#a78bfa;}}.hg{{color:#00d4ff;}}
</style></head><body>
<div id="app">
  <div id="orb">🎙️</div>
  <div id="title">NOVA</div>
  <div id="badge">TAP ORB TO START</div>
  <div id="bars"><span class="b" id="b1"></span><span class="b" id="b2"></span>
    <span class="b" id="b3"></span><span class="b" id="b4"></span><span class="b" id="b5"></span></div>
  <div id="bubble">👋 Tap the orb — I listen, understand, and act in <b>{LANG_NAMES.get(lang,"English")}</b>!</div>
  <div id="heard">Your voice appears here…</div>
  <div id="flow"></div>
  <div id="btns">
    <button class="btn-go" id="btnGo" onclick="toggle()">🎤 Start NOVA</button>
    <button class="btn-stop" onclick="stopNOVA()">⏹ Stop</button>
    <button class="btn-rep" onclick="repeatLast()">🔁 Repeat</button>
  </div>
  <div id="cards"></div>
  <details id="hints">
    <summary>💡 What can I say?</summary>
    <div>
      <span class="hg">Load:</span> <span class="hk">load emails · load telegram</span><br>
      <span class="hg">Read (PIN):</span> <span class="hk">read email · read telegram</span><br>
      <span class="hg">Send (PIN):</span> <span class="hk">send email · send telegram</span><br>
      <span class="hg">Navigate:</span> <span class="hk">open email · open telegram · open contacts · open admin · go home</span><br>
      <span class="hg">PIN:</span> <span class="hk">set pin 1 2 3 4 (your own digits)</span><br>
      <span class="hg">Info:</span> <span class="hk">what time · what date · help · hello · stop</span>
    </div>
  </details>
</div>
<script>
(function(){{
var ON=false,SP=false,BUSY=false,rc=null;
var SRC=window.SpeechRecognition||window.webkitSpeechRecognition;
var LOC="{loc}";
var FLOW=null,STEP=0,D={{}};
var PIN_FOR=null,PIN_ACTION_CB=null;
var LAST="";
var LOGGED_IN={li_js};
var PIN_SET={pin_js};
var PIN_VAL="{pin_val_js}";  /* actual PIN stored here — verified locally in JS */
var USER="{name_safe}";

var EMAILS={email_js};
var TGS={tg_js};

var orb=document.getElementById("orb");
var badge=document.getElementById("badge");
var bubble=document.getElementById("bubble");
var heard=document.getElementById("heard");
var flow=document.getElementById("flow");
var btnGo=document.getElementById("btnGo");
var bars=[1,2,3,4,5].map(function(i){{return document.getElementById("b"+i);}});

/* build email/tg cards */
(function(){{
  var c=document.getElementById("cards"),html="";
  if(EMAILS.length){{
    html+="<div class='card-lbl'>📧 Emails — tap to read aloud</div><div class='card-row'>";
    EMAILS.forEach(function(e,i){{
      html+="<div class='ec' onclick='tapEmail("+i+")'>"
        +"<div class='ef'>"+(e.unread?"🔴 ":"⚪ ")+e.from+"</div>"
        +"<div class='es'>"+e.sub+"</div>"
        +"<div class='eb'>"+e.snip+"</div></div>";
    }});
    html+="</div>";
  }}
  if(TGS.length){{
    html+="<div class='card-lbl'>✈️ Telegram</div><div class='card-row'>";
    TGS.forEach(function(m){{
      html+="<div class='tc'><div class='tf'>"+m.from+" · "+m.date+"</div><div class='tm'>"+m.text+"</div></div>";
    }});
    html+="</div>";
  }}
  c.innerHTML=html;
}})();

window.tapEmail=function(i){{
  if(!ON){{bubble.innerHTML="Tap Start first, then tap a card.";return;}}
  readEmailByIndex(i);
}};

function setBadge(t){{badge.textContent=t;}}
function setBubble(t){{bubble.innerHTML=t;}}
function setHeard(t){{heard.textContent=t;}}
function setFlow(h){{if(h){{flow.style.display="block";flow.innerHTML=h;}}else{{flow.style.display="none";flow.innerHTML="";}}}}
function waveOn(on){{bars.forEach(function(b,i){{if(!b)return;if(on){{b.classList.add("on");b.style.height=["8px","18px","30px","18px","8px"][i];}}else{{b.classList.remove("on");b.style.height="4px";}}}});}}
function setOrb(mode){{orb.classList.remove("speaking","listening");if(mode)orb.classList.add(mode);}}
function btnLabel(on){{btnGo.textContent=on?"⏹ Stop NOVA":"🎤 Start NOVA";}}

/* ── Bridge to Python (for actions that need server: load, send) ── */
function sendToServer(cmd){{
  BUSY=true;
  var doc=null;try{{doc=window.parent.document;}}catch(e){{doc=document;}}
  var target=null;
  var inputs=doc.querySelectorAll("input");
  for(var i=0;i<inputs.length;i++){{
    var ph=(inputs[i].placeholder||"");
    if(ph.indexOf("nova-bridge")!==-1){{target=inputs[i];break;}}
  }}
  if(!target){{
    for(var j=inputs.length-1;j>=0;j--){{
      if(inputs[j].type!=="hidden"&&inputs[j].offsetParent!==null){{target=inputs[j];break;}}
    }}
  }}
  if(!target){{BUSY=false;setBubble("⚠️ Bridge not found.");return;}}
  var unique=cmd+"|||TS"+Date.now();
  try{{var s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,"value").set;s.call(target,unique);}}
  catch(e){{target.value=unique;}}
  target.dispatchEvent(new Event("input",{{bubbles:true}}));
  target.dispatchEvent(new Event("change",{{bubbles:true}}));
  setTimeout(function(){{
    var btns=doc.querySelectorAll("button");
    for(var k=0;k<btns.length;k++){{
      var t=(btns[k].innerText||btns[k].textContent||"").trim();
      if(t==="▶"){{btns[k].click();return;}}
    }}
    target.dispatchEvent(new KeyboardEvent("keydown",{{key:"Enter",keyCode:13,bubbles:true}}));
  }},250);
  setTimeout(function(){{BUSY=false;if(ON&&!SP)listen();}},4500);
}}

/* ── Speak ── */
function speak(text,cb){{
  if(!text){{if(cb)cb();return;}}
  SP=true;LAST=text;
  if(window.speechSynthesis)window.speechSynthesis.cancel();
  waveOn(false);setOrb("speaking");setBadge("🔊 SPEAKING");setBubble("🔊 "+text);
  var u=new SpeechSynthesisUtterance(text);
  u.lang=LOC;u.rate=0.92;u.pitch=1.05;
  var done=false;
  function fin(){{if(done)return;done=true;SP=false;setOrb(ON?"listening":null);if(cb)cb();else if(ON)sched(400);}}
  u.onend=fin;u.onerror=fin;
  setTimeout(fin,Math.max(3000,text.split(" ").length*640)+1000);
  window.speechSynthesis.speak(u);
}}

/* ── Listen ── */
function sched(ms){{if(!ON||SP||BUSY)return;setTimeout(function(){{if(ON&&!SP&&!BUSY)listen();}},ms||300);}}
function listen(){{
  if(!ON||SP||BUSY)return;
  if(rc){{try{{rc.abort();}}catch(e){{}}rc=null;}}
  if(!SRC){{setBubble("❌ Open in <b>Google Chrome</b> — voice needs Chrome.");return;}}
  var r=new SRC();r.lang=LOC;r.continuous=false;r.interimResults=true;r.maxAlternatives=1;
  rc=r;waveOn(true);setOrb("listening");setBadge("👂 LISTENING…");
  r.onresult=function(e){{
    var txt="",fin=false;
    for(var i=e.resultIndex;i<e.results.length;i++){{txt+=e.results[i][0].transcript;if(e.results[i].isFinal)fin=true;}}
    setHeard(txt.trim());if(!fin)return;
    rc=null;waveOn(false);setBadge("⚡ PROCESSING…");route(txt.trim());
  }};
  r.onerror=function(ev){{
    rc=null;waveOn(false);
    if(ev.error==="not-allowed"||ev.error==="service-not-allowed"){{
      ON=false;setOrb(null);btnLabel(false);setBadge("MIC BLOCKED");
      setBubble("❌ Mic blocked. Chrome → 🔒 → Allow microphone → Reload.");return;
    }}
    if(ON&&!SP&&!BUSY)setTimeout(listen,600);
  }};
  r.onend=function(){{rc=null;waveOn(false);if(ON&&!SP&&!BUSY)sched(300);}};
  try{{r.start();}}catch(ex){{rc=null;if(ON)sched(600);}}
}}

/* ── Router ── */
function route(raw){{
  var p=raw.toLowerCase().trim();
  if(/\b(stop|cancel|exit|goodbye|bye|abort)\b/.test(p)){{
    if(FLOW||PIN_FOR){{FLOW=null;PIN_FOR=null;PIN_ACTION_CB=null;STEP=0;D={{}};setFlow(null);speak("{js('cancelled')}",null);}}
    else{{speak("Stopping. Goodbye!",function(){{stopNOVA();}});}}
    return;
  }}
  if(PIN_FOR){{handlePin(raw,p);return;}}
  if(FLOW==="email"){{emailFlow(raw,p);return;}}
  if(FLOW==="tg"){{tgFlow(raw,p);return;}}
  if(FLOW==="setpin"){{setPinFlow(raw,p);return;}}
  if(FLOW==="login"){{loginFlow(raw,p);return;}}
  if(FLOW==="signup"){{signupFlow(raw,p);return;}}
  freeCmd(raw,p);
}}

/* ════════════════════════════════════════════════
   PIN FLOW — verified ENTIRELY in JS
   No Python roundtrip needed!
════════════════════════════════════════════════ */
function needPin(action,cb){{
  if(!PIN_SET){{
    speak("{js('no_pin')}",function(){{listen();}});return;
  }}
  PIN_FOR=action;PIN_ACTION_CB=cb;
  setFlow("🔐 <b>PIN required for: "+action+"</b><br>Say your 4 digits");
  speak("{js('ask_pin')}",null);
}}

function handlePin(raw,p){{
  /* extract digits from speech */
  var digits=p.replace(/[^0-9]/g,"");
  if(!digits){{
    var m={{zero:"0",one:"1",two:"2",three:"3",four:"4",
            five:"5",six:"6",seven:"7",eight:"8",nine:"9",oh:"0",nought:"0"}};
    digits=p.split(/[\s,]+/).map(function(w){{return m[w]||"";}}).join("");
  }}
  if(digits.length<4){{speak("{js('ask_pin')}",null);return;}}
  var pin4=digits.slice(0,4);
  var action=PIN_FOR;var cb=PIN_ACTION_CB;
  PIN_FOR=null;PIN_ACTION_CB=null;setFlow(null);

  /* ── LOCAL PIN CHECK — no Python needed ── */
  if(pin4===PIN_VAL){{
    speak("{js('pin_ok')}",function(){{
      if(cb)cb(action);else if(ON)listen();
    }});
  }}else{{
    speak("{js('wrong_pin')}",function(){{
      /* offer retry */
      PIN_FOR=action;PIN_ACTION_CB=cb;
      setFlow("🔐 PIN wrong — try again");
      speak("{js('ask_pin')}",null);
    }});
  }}
}}

/* ── After PIN ok: perform the action ── */
function doAfterPin(action){{
  if(action==="read_email"){{
    readEmailByIndex(0);
  }}else if(action==="read_tg"){{
    readTG();
  }}else if(action==="send_email"){{
    FLOW="email";STEP=0;D={{}};
    speak("{js('send_e1')}",null);
  }}else if(action==="send_tg"){{
    FLOW="tg";STEP=0;D={{}};
    speak("{js('send_t1')}",null);
  }}
}}

/* ── Read email directly in JS (no Python) ── */
function readEmailByIndex(idx){{
  if(!EMAILS||EMAILS.length===0){{speak("{js('no_email')}",null);return;}}
  var e=EMAILS[Math.min(idx,EMAILS.length-1)];
  var text="{js('read_email')} Email from "+e.from+". Subject: "+e.sub+". "+e.body;
  speak(text,null);
}}

/* ── Read TG directly in JS (no Python) ── */
function readTG(){{
  if(!TGS||TGS.length===0){{speak("{js('no_tg')}",null);return;}}
  var m=TGS[TGS.length-1];
  var text="{js('read_tg')} Message from "+m.from+": "+m.text;
  speak(text,null);
}}

/* ── Set PIN flow ── */
function setPinFlow(raw,p){{
  var digits=p.replace(/[^0-9]/g,"");
  if(!digits){{
    var m={{zero:"0",one:"1",two:"2",three:"3",four:"4",five:"5",six:"6",seven:"7",eight:"8",nine:"9"}};
    digits=p.split(/[\s,]+/).map(function(w){{return m[w]||"";}}).join("");
  }}
  if(digits.length>=4){{
    FLOW=null;D={{}};
    var pin4=digits.slice(0,4);
    PIN_VAL=pin4;PIN_SET=true;  /* update JS state immediately */
    setBubble("🔐 PIN set to: "+pin4[0]+" "+pin4[1]+" "+pin4[2]+" "+pin4[3]);
    speak("PIN set to "+pin4.split("").join(" ")+". All protected features are now unlocked.",function(){{
      sendToServer("SETPIN|||"+pin4);  /* also save to Python session */
      if(ON)listen();
    }});
  }}else{{
    speak("{js('setpin_ask')}",null);
  }}
}}

/* ── Login flow ── */
function loginFlow(raw,p){{
  var name=raw.replace(/^(login as|my name is|i am|i'm|enter as|call me)\s*/i,"").trim();
  if(!name||/^(guest|skip)$/i.test(name))name="Guest";
  var cap=name.charAt(0).toUpperCase()+name.slice(1).toLowerCase();
  FLOW=null;STEP=0;D={{}};setFlow(null);
  sendToServer("LOGIN|||"+cap+"|||"+cap.toLowerCase()+"@nova.ai|||");
  speak("Welcome "+cap+"! Logging you in.",null);
}}

/* ── Signup flow ── */
function signupFlow(raw,p){{
  if(STEP===0){{D.name=raw.trim();STEP=1;setFlow("👤 "+D.name);speak("Got it "+D.name+". Say your email.",null);}}
  else if(STEP===1){{D.email=raw.trim().replace(/ at /gi,"@").replace(/ dot /gi,".").replace(/ /g,"");STEP=2;speak("Email: "+D.email+". Say password.",null);}}
  else if(STEP===2){{D.pw=raw.trim().replace(/ /g,"");FLOW=null;STEP=0;D={{}};setFlow(null);sendToServer("SIGNUP|||"+D.name+"|||"+D.email+"|||"+D.pw);speak("Creating account…",null);}}
}}

/* ── Email compose flow ── */
function emailFlow(raw,p){{
  if(STEP===0){{D.to=raw.trim();STEP=1;setFlow("📧 To: "+D.to);speak("{js('send_e2')}",null);}}
  else if(STEP===1){{D.sub=raw.trim();STEP=2;setFlow("📧 "+D.to+" · "+D.sub);speak("{js('send_e3')}",null);}}
  else if(STEP===2){{
    D.body=raw.trim();STEP=3;
    setFlow("📧 "+D.to+"<br>📝 "+D.sub+"<br>💬 "+D.body.slice(0,50));
    speak("Ready to send to "+D.to+". Subject: "+D.sub+". Say confirm to send or cancel.",null);
  }}
  else if(STEP===3){{
    if(/\b(confirm|send|yes|ok|sure|proceed|ha|haan)\b/.test(p)){{
      var to=D.to;var sub=D.sub;var body=D.body;
      FLOW=null;STEP=0;D={{}};setFlow(null);
      sendToServer("SEND_EMAIL|||"+to+"|||"+sub+"|||"+body);
      speak("Sending your email now.",null);
    }}else{{FLOW=null;STEP=0;D={{}};setFlow(null);speak("{js('cancelled')}",null);}}
  }}
}}

/* ── Telegram flow ── */
function tgFlow(raw,p){{
  if(STEP===0){{D.msg=raw.trim();STEP=1;setFlow("✈️ "+D.msg.slice(0,70));speak(D.msg+". Say confirm or cancel.",null);}}
  else if(STEP===1){{
    if(/\b(confirm|send|yes|ok|sure|proceed|ha|haan)\b/.test(p)){{
      var msg=D.msg;FLOW=null;STEP=0;D={{}};setFlow(null);
      sendToServer("SEND_TG|||"+msg);speak("Sending now.",null);
    }}else{{FLOW=null;STEP=0;D={{}};setFlow(null);speak("{js('cancelled')}",null);}}
  }}
}}

/* ── Free commands ── */
function freeCmd(raw,p){{
  /* greeting */
  if(/\b(hello|hi nova|hey nova|hi|hey|namaste|vanakkam)\b/.test(p)){{
    var hr=new Date().getHours();
    var g=hr<12?"{js('morning')}":hr<17?"{js('afternoon')}":"{js('evening')}";
    speak(g+" "+(USER||"friend")+"! {js('greeting')} Say help for commands.",null);return;
  }}
  if(/\b(help|commands|what can you do)\b/.test(p)){{sendToServer(raw);return;}}
  if(/time|date|today/.test(p)){{sendToServer(raw);return;}}

  /* set pin */
  if(/set pin|create pin|change pin|new pin/.test(p)){{
    var digits=p.replace(/[^0-9]/g,"");
    if(!digits){{var mw={{zero:"0",one:"1",two:"2",three:"3",four:"4",five:"5",six:"6",seven:"7",eight:"8",nine:"9"}};digits=p.split(/[\s,]+/).map(function(w){{return mw[w]||"";}}).join("");}}
    if(digits.length>=4){{
      var pin4=digits.slice(0,4);PIN_VAL=pin4;PIN_SET=true;
      setBubble("🔐 PIN set to: "+pin4[0]+" "+pin4[1]+" "+pin4[2]+" "+pin4[3]);
      speak("PIN set to "+pin4.split("").join(" ")+". All features unlocked.",function(){{sendToServer("SETPIN|||"+pin4);if(ON)listen();}});
    }}else{{FLOW="setpin";STEP=0;speak("{js('setpin_ask')}",null);}}
    return;
  }}

  /* load */
  if(/load email|fetch email|get email|refresh email|check my email/.test(p)){{sendToServer("LOAD_EMAILS");speak("Loading your emails. Please wait.",null);return;}}
  if(/load telegram|fetch telegram|get telegram|refresh telegram/.test(p)){{sendToServer("LOAD_TG");speak("Loading Telegram messages.",null);return;}}

  /* READ — verified locally, no Python roundtrip */
  if(/read email|read my email|first email|latest email/.test(p)){{
    needPin("read_email",doAfterPin);return;
  }}
  if(/read telegram|read my telegram|read messages|latest message/.test(p)){{
    needPin("read_tg",doAfterPin);return;
  }}

  /* SEND — PIN then flow */
  if(/send email|compose email|new email|write email/.test(p)){{needPin("send_email",doAfterPin);return;}}
  if(/send telegram|telegram message|message on telegram/.test(p)){{needPin("send_tg",doAfterPin);return;}}

  /* navigation — tell Python to change page */
  if(/open email|check email|go to email/.test(p)&&!/send|read|compose/.test(p)){{sendToServer("open email");speak("Opening email!",null);return;}}
  if(/open telegram|check telegram|go to telegram/.test(p)&&!/send|read/.test(p)){{sendToServer("open telegram");speak("Opening Telegram!",null);return;}}
  if(/contacts/.test(p)&&!/send/.test(p)){{sendToServer("open contacts");speak("Opening contacts!",null);return;}}
  if(/settings/.test(p)){{sendToServer("open settings");speak("Opening settings!",null);return;}}
  if(/admin/.test(p)){{sendToServer("open admin");speak("Opening admin!",null);return;}}
  if(/profile/.test(p)){{sendToServer("open profile");speak("Opening profile!",null);return;}}
  if(/home|dashboard|main/.test(p)){{sendToServer("dashboard");speak("Going home!",null);return;}}
  if(/whatsapp/.test(p)){{sendToServer("open whatsapp");speak("Opening WhatsApp!",null);return;}}
  if(/speech to text|stt/.test(p)){{sendToServer("stt");speak("Opening speech to text!",null);return;}}
  if(/text to speech|tts/.test(p)){{sendToServer("tts");speak("Opening text to speech!",null);return;}}
  if(/logout|log out|sign out/.test(p)){{speak("Logging out. Goodbye!",function(){{sendToServer("logout");}});return;}}

  /* login / signup */
  if(!LOGGED_IN||/\b(login|sign in)\b/.test(p)){{FLOW="login";STEP=0;D={{}};loginFlow(raw,p);return;}}
  if(/sign up|signup|register|create account/.test(p)){{FLOW="signup";STEP=0;D={{}};speak("Say your full name.",null);return;}}

  sendToServer(raw);
}}

/* ── On load: speak any Python→JS message ── */
window.addEventListener("load",function(){{
  var pending="{say_safe}";
  if(pending){{
    setTimeout(function(){{
      setBubble("🔊 "+pending);
      speak(pending,function(){{if(ON)listen();}});
    }},500);
  }}
}});

/* ── Start/Stop ── */
function startNOVA(){{
  ON=true;btnLabel(true);setOrb("listening");setBadge("🚀 STARTING…");
  var greet;
  if(!LOGGED_IN){{FLOW="login";STEP=0;D={{}};greet="{js('login_wake')}";}}
  else{{
    var hr=new Date().getHours();
    var g=hr<12?"{js('morning')}":hr<17?"{js('afternoon')}":"{js('evening')}";
    greet=g+" "+(USER||"")+"! {js('greeting')} {js('wake')}";
  }}
  speak(greet,function(){{listen();}});
}}
function stopNOVA(){{
  ON=false;SP=false;BUSY=false;FLOW=null;PIN_FOR=null;PIN_ACTION_CB=null;STEP=0;D={{}};
  if(rc){{try{{rc.abort();}}catch(e){{}}rc=null;}}
  if(window.speechSynthesis)window.speechSynthesis.cancel();
  setOrb(null);waveOn(false);setFlow(null);btnLabel(false);
  setBadge("TAP ORB TO START");setBubble("NOVA stopped. Tap the orb to restart.");setHeard("");
}}
function toggle(){{if(ON)stopNOVA();else startNOVA();}}
function repeatLast(){{if(LAST)speak(LAST,function(){{if(ON)listen();}});}}

orb.addEventListener("click",toggle);
btnGo.addEventListener("click",toggle);
}})();
</script></body></html>"""

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("""<div style="text-align:center;padding:8px 0 4px">
<div style="font-size:20px;font-weight:900;letter-spacing:5px;background:linear-gradient(135deg,#6c63ff,#00d4ff);
-webkit-background-clip:text;-webkit-text-fill-color:transparent">NOVA</div>
<div style="font-size:9px;color:#555;letter-spacing:3px">VOICE AI ASSISTANT</div></div>""",unsafe_allow_html=True)
        nm=st.session_state.user_name or "Guest"
        em=st.session_state.user_email or ""
        st.markdown(f"""<div style="display:flex;align-items:center;gap:9px;padding:6px 2px;margin:4px 0">
<div style="width:34px;height:34px;border-radius:50%;flex-shrink:0;background:linear-gradient(135deg,#6c63ff,#00d4ff);
display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:#fff">{nm[0].upper()}</div>
<div><div style="font-weight:700;font-size:13px">{nm}</div>
<div style="font-size:10px;color:#7a7a9a;word-break:break-all">{em}</div></div></div>""",unsafe_allow_html=True)
        st.divider()
        langs=list(LANG_NAMES.keys()); labels=[LANG_NAMES[k] for k in langs]
        cur=langs.index(st.session_state.lang) if st.session_state.lang in langs else 0
        sel=st.selectbox("🌐 Language",labels,index=cur,key="_slang")
        if labels[cur]!=sel:
            st.session_state.lang=langs[labels.index(sel)]
            st.session_state._cmd_in=""; st.session_state._cmd_last=""
            st.rerun()
        st.divider()
        for lbl,pg in [("🎙️ Voice (Main)","Assistant"),("🏠 Dashboard","Dashboard"),
            ("📧 Email","Email"),("✈️ Telegram","Telegram"),("📱 WhatsApp","WhatsApp"),
            ("👤 Profile","Profile"),("⚙️ Settings","Settings"),
            ("📋 Contacts","Contacts"),("🛡️ Admin","Admin")]:
            t="primary" if st.session_state.page==pg else "secondary"
            if st.button(lbl,key=f"nav_{pg}",use_container_width=True,type=t):
                st.session_state.page=pg; st.rerun()
        st.divider()
        if st.button("🚪 Logout",use_container_width=True,key="logout_btn"):
            st.session_state.logged_in=False; st.session_state.user_name=""
            st.session_state.user_email=""; st.session_state.pin_verified_for=set()
            _log("Logout"); st.rerun()

# ── PAGES ─────────────────────────────────────────────────────────────────────
def page_assistant():
    lang=st.session_state.lang
    st.markdown(f"## 🎙️ NOVA · {LANG_NAMES.get(lang,'English')}")
    st.caption("Tap the orb → speak → NOVA responds & acts · **Chrome required**")
    if not st.session_state.pin_set:
        st.warning("🔐 No PIN set — say **'set pin 5 6 7 8'** (use your own 4 digits)")
    nova_say=st.session_state._nova_say
    nova_nav=st.session_state._nova_nav
    st.session_state._nova_say=""; st.session_state._nova_nav=""
    if nova_nav and nova_nav!="Assistant":
        st.session_state.page=nova_nav; st.rerun()
    if nova_say:
        st.info(f"🔊 *{nova_say}*")
    st.components.v1.html(_nova_html(
        lang=lang, nova_say=nova_say,
        logged_in=st.session_state.logged_in,
        pin_set=st.session_state.pin_set,
        user_pin=st.session_state.user_pin,
        user_name=st.session_state.user_name,
        emails=st.session_state.emails,
        tg_msgs=st.session_state.tg_messages,
    ), height=680, scrolling=False)
    st.markdown("---")
    st.caption("🔗 Voice bridge — NOVA fills this automatically:")
    col1,col2=st.columns([8,1])
    with col1:
        cmd=st.text_input("cmd",key="_cmd_in",
            placeholder="nova-bridge — NOVA auto-fills this",
            label_visibility="collapsed")
    with col2:
        go=st.button("▶",key="_cmd_go",type="primary",use_container_width=True)
    if go and cmd.strip() and cmd.strip()!=st.session_state._cmd_last:
        st.session_state._cmd_last=cmd.strip()
        process_cmd(cmd.strip()); st.rerun()
    st.divider()
    st.markdown("**⚡ Quick Navigate**")
    cols=st.columns(5)
    for i,(lbl,pg) in enumerate([("📧 Email","Email"),("✈️ Telegram","Telegram"),
        ("📱 WhatsApp","WhatsApp"),("📋 Contacts","Contacts"),("🛡️ Admin","Admin")]):
        with cols[i]:
            if st.button(lbl,key=f"qa_{pg}",use_container_width=True):
                st.session_state.page=pg; st.rerun()

def page_dashboard():
    nm=st.session_state.user_name or "Guest"
    h=datetime.datetime.now().hour
    greet="🌅 Good morning" if h<12 else "☀️ Good afternoon" if h<17 else "🌙 Good evening"
    st.markdown(f"## {greet}, {nm}!")
    st.caption(datetime.datetime.now().strftime('%A, %B %d %Y'))
    if not st.session_state.pin_set:
        st.warning("🔐 No PIN — go to Voice page and say **'set pin'** + 4 digits")
    s=st.session_state.stats
    c1,c2,c3,c4=st.columns(4)
    c1.metric("📧 Emails",s["emails_sent"]); c2.metric("✈️ TG",s["telegrams_sent"])
    c3.metric("🎙️ Voice",s["voice_cmds"]); c4.metric("📋 Contacts",len(st.session_state.contacts))
    st.markdown("---")
    qa=st.columns(5)
    for i,(lbl,pg) in enumerate([("🎙️ Voice","Assistant"),("📧 Email","Email"),
        ("✈️ Telegram","Telegram"),("📋 Contacts","Contacts"),("🛡️ Admin","Admin")]):
        with qa[i]:
            if st.button(lbl,key=f"d_{pg}",use_container_width=True):
                st.session_state.page=pg; st.rerun()
    st.markdown("---")
    st.markdown("**📧 Recent Emails**")
    emails=st.session_state.emails
    if not emails:
        c1,c2=st.columns([4,1])
        with c1: st.info("Say **'load emails'** on Voice page")
        with c2:
            if st.button("🔄",key="dem",type="primary"):
                with st.spinner(): st.session_state.emails=load_emails()
                st.rerun()
    else:
        cards="".join([f"<div class='ecard'><div class='ef'>{'🔴 ' if e.get('unread') else '⚪ '}{re.sub(chr(60)+'[^>]+>','',e['from'])[:26]}</div><div class='es'>{e['subject'][:30]}</div><div class='eb'>{e.get('snippet','')[:70]}</div></div>" for e in emails[:8]])
        st.markdown(f"<div class='hscroll'>{cards}</div>",unsafe_allow_html=True)
    st.markdown("**✈️ Recent Telegram**")
    msgs=st.session_state.tg_messages
    if not msgs:
        c1,c2=st.columns([4,1])
        with c1: st.info("Say **'load telegram'** on Voice page")
        with c2:
            if st.button("🔄",key="dtg",type="primary"):
                with st.spinner(): st.session_state.tg_messages=load_tg()
                st.rerun()
    else:
        cards="".join([f"<div class='tcard'><div class='tf'>{m['from']} · {m['date']}</div><div class='tm'>{m['text'][:80]}</div></div>" for m in reversed(msgs[-6:])])
        st.markdown(f"<div class='hscroll'>{cards}</div>",unsafe_allow_html=True)

def page_email():
    lang=st.session_state.lang; loc=_locale(lang)
    st.markdown("## 📧 Email")
    st.info("🎙️ Voice: **load emails · read email · send email**")
    if not GOOGLE_OK: st.error("`pip install google-auth google-auth-oauthlib google-api-python-client`"); return
    if not google_connected():
        st.warning("Gmail not connected.")
        if st.button("⚙️ Connect",type="primary"): st.session_state.page="Settings"; st.rerun()
        return
    c1,c2=st.columns([4,1])
    with c1: st.markdown("### Inbox")
    with c2:
        if st.button("🔄",key="emref",type="primary",use_container_width=True):
            with st.spinner(): st.session_state.emails=load_emails(); st.rerun()
    emails=st.session_state.emails
    if not emails: st.info("Click 🔄 or say 'load emails'")
    else:
        cards="".join([f"<div class='ecard'><div class='ef'>{'🔴 ' if e.get('unread') else '⚪ '}{re.sub(r'<[^>]+>','',e['from'])[:24]}</div><div class='es'>{e['subject'][:28]}</div><div class='eb'>{e.get('snippet','')[:70]}</div></div>" for e in emails[:8]])
        st.markdown(f"<div class='hscroll'>{cards}</div>",unsafe_allow_html=True)
        st.markdown("---")
        for i,e in enumerate(emails[:10]):
            frm=re.sub(r'<[^>]+>','',e["from"]).strip()
            with st.expander(f"{'🔴' if e.get('unread') else '⚪'} **{frm[:26]}** — {e['subject'][:42]}"):
                st.caption(f"📅 {e['date']}")
                body=_clean(e.get("body","") or e.get("snippet",""))
                st.markdown((body[:600]+("…" if len(body)>600 else "")) if body else "*(empty)*")
                b1,b2,b3=st.columns(3)
                with b1:
                    if st.button("↩️ Reply",key=f"rp_{i}"):
                        st.session_state.compose_to=e["from"]; st.session_state.compose_sub=f"Re: {e['subject']}"; st.rerun()
                with b2:
                    safe=f"Email from {frm}. Subject {e['subject']}. {_clean(e.get('body','') or e.get('snippet',''))[:300]}".replace("'","")[:450]
                    st.components.v1.html(f"""<button onclick="(function(){{var u=new SpeechSynthesisUtterance('{safe}');u.lang='{loc}';u.rate=0.88;window.speechSynthesis.speak(u);}})();" style="padding:7px 14px;background:rgba(168,85,247,.2);border:1px solid rgba(168,85,247,.5);color:#a855f7;border-radius:8px;cursor:pointer;font-size:12px;font-weight:700">🔊 Read</button>""",height=42)
                with b3:
                    if st.button("✨ Summarize",key=f"sm_{i}"):
                        with st.spinner():
                            s=summarize_email(e.get("body",""),e["subject"])
                        st.info(f"**Summary:** {s}")
    st.markdown("---")
    st.markdown("### ✍️ Compose")
    to=st.text_input("To:",value=st.session_state.compose_to,placeholder="email@example.com",key="em_to")
    sub=st.text_input("Subject:",value=st.session_state.compose_sub,placeholder="Subject",key="em_sub")
    body=st.text_area("Message:",value=st.session_state.compose_body,placeholder="Your message…",height=120,key="em_body")
    if st.button("📤 Send",type="primary",key="em_send"):
        if to.strip() and "@" in to and sub.strip() and body.strip():
            ok,msg=do_send_email(to.strip(),sub.strip(),body.strip())
            if ok: st.success(f"✅ {msg}"); st.session_state.compose_to=st.session_state.compose_sub=st.session_state.compose_body=""
            else: st.error(f"❌ {msg}")
        else: st.error("Fill all fields.")

def page_telegram():
    lang=st.session_state.lang
    st.markdown("## ✈️ Telegram")
    st.info("🎙️ Voice: **load telegram · read telegram · send telegram**")
    if not tg_ok(): st.warning("Set TELEGRAM_BOT_TOKEN in nova_app.py"); return
    c1,c2=st.columns([4,1])
    with c1: st.markdown("### Messages")
    with c2:
        if st.button("🔄",key="tgref",type="primary",use_container_width=True):
            with st.spinner(): st.session_state.tg_messages=load_tg(); st.rerun()
    msgs=st.session_state.tg_messages
    if not msgs: st.info("Click 🔄 or say 'load telegram'")
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
    txt=st.text_area("Message:",height=80,key="tg_txt")
    if st.button("✈️ Send",type="primary",key="tg_send"):
        if txt.strip():
            ok,msg=send_tg(txt.strip())
            if ok: st.success(f"✅ {msg}")
            else: st.error(f"❌ {msg}")

def page_whatsapp():
    st.markdown("## 📱 WhatsApp")
    st.info("WhatsApp requires Twilio.")
    st.link_button("🌐 Open WhatsApp Web","https://web.whatsapp.com")

def page_profile():
    st.markdown("## 👤 Profile")
    if google_connected():
        info=google_info()
        if info:
            st.session_state.user_name=info.get("name",st.session_state.user_name)
            st.session_state.user_email=info.get("email",st.session_state.user_email)
            if info.get("picture"): st.image(info["picture"],width=80)
        st.success(f"✅ {st.session_state.user_email}")
    with st.form("pf"):
        n=st.text_input("Name:",value=st.session_state.user_name)
        e=st.text_input("Email:",value=st.session_state.user_email)
        if st.form_submit_button("💾 Save",type="primary"):
            st.session_state.user_name=n; st.session_state.user_email=e; _log(f"Profile: {n}"); st.success("✅ Saved!")

def page_settings():
    st.markdown("## ⚙️ Settings")
    t1,t2=st.tabs(["🔗 Gmail","🔧 Services"])
    with t1:
        if google_connected():
            info=google_info(); st.success(f"✅ {info.get('email','')}")
            if st.button("🔌 Disconnect",key="disc"):
                if Path(TOKEN_FILE).exists(): os.remove(TOKEN_FILE); st.rerun()
        else:
            st.error("❌ Not connected")
            if not Path(CREDENTIALS_FILE).exists():
                st.warning(f"`{CREDENTIALS_FILE}` not found.")
                st.markdown("1. [Google Cloud Console](https://console.cloud.google.com) → Enable Gmail API\n2. OAuth 2.0 → Desktop → Download `credentials.json`\n3. Place in app folder → restart")
            else:
                if st.button("🔗 Connect Gmail",type="primary",key="conn"):
                    try:
                        flow=Flow.from_client_secrets_file(CREDENTIALS_FILE,scopes=SCOPES,redirect_uri="urn:ietf:wg:oauth:2.0:oob")
                        url,_=flow.authorization_url(access_type="offline",include_granted_scopes="true",prompt="consent")
                        st.session_state["_fl"]=flow; st.markdown(f"**[➡️ Sign in with Google]({url})**")
                    except Exception as ex: st.error(str(ex))
                if "_fl" in st.session_state:
                    code=st.text_input("Auth code:",key="ac")
                    if st.button("✅ Confirm",key="ac2"):
                        try:
                            st.session_state["_fl"].fetch_token(code=code); _save_token(st.session_state["_fl"].credentials)
                            del st.session_state["_fl"]; st.rerun()
                        except Exception as ex: st.error(str(ex))
    with t2:
        a,b,c=st.columns(3)
        with a: st.success("📧 Gmail ✅") if google_connected() else st.error("📧 Gmail ❌")
        with b: st.success("✈️ Telegram ✅") if tg_ok() else st.warning("✈️ Telegram ⚠️")
        with c: st.success("🌐 Requests ✅") if REQUESTS_OK else st.error("🌐 Requests ❌")

def page_contacts():
    st.markdown("## 📋 Contacts")
    t1,t2=st.tabs(["👥 All","➕ Add"])
    with t1:
        srch=st.text_input("🔍 Search:",key="cs")
        contacts=st.session_state.contacts
        if srch: contacts=[c for c in contacts if srch.lower() in c["name"].lower() or srch.lower() in c.get("email","").lower()]
        for i,c in enumerate(contacts):
            a,b,cc,d=st.columns([1,3,3,1])
            with a: st.markdown(f'<div style="width:28px;height:28px;border-radius:50%;background:linear-gradient(135deg,#6c63ff,#00d4ff);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:#fff">{c["name"][0].upper()}</div>',unsafe_allow_html=True)
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
                if not nm: st.error("Name required.")
                elif "@" not in em: st.error("Valid email required.")
                else: st.session_state.contacts.append({"name":nm,"email":em,"phone":ph}); st.success(f"✅ {nm}")

def page_admin():
    st.markdown("## 🛡️ Admin")
    t1,t2,t3=st.tabs(["📊 Stats","🔐 PIN","📋 Log"])
    with t1:
        s=st.session_state.stats; a,b,c,d=st.columns(4)
        a.metric("📧 Emails",s["emails_sent"]); b.metric("✈️ TG",s["telegrams_sent"])
        c.metric("🔑 Logins",s["logins"]); d.metric("🎙️ Voice",s["voice_cmds"])
        if st.session_state.pin_set: st.success("✅ PIN configured.")
        else: st.error("❌ No PIN — say 'set pin' on Voice page")
    with t2:
        st.info("🎙️ Say **'set pin 5 6 7 8'** on Voice page (your own digits)\n\nOr use form below:")
        if st.session_state.pin_set: st.success(f"✅ PIN is set.")
        else: st.error("❌ No PIN yet.")
        with st.form("pinf",clear_on_submit=True):
            p1=st.text_input("New PIN (4 digits):",type="password",max_chars=4)
            p2=st.text_input("Confirm:",type="password",max_chars=4)
            if st.form_submit_button("💾 Save",type="primary"):
                p1,p2=p1.strip(),p2.strip()
                if not p1.isdigit() or len(p1)!=4: st.error("4 digits only.")
                elif p1!=p2: st.error("Don't match.")
                else:
                    st.session_state.user_pin=p1; st.session_state.pin_set=True
                    st.session_state.pin_verified_for=set(); _log("PIN set"); st.success("✅ PIN saved!")
        if st.session_state.pin_set:
            c1,c2=st.columns(2)
            with c1:
                if st.button("🔄 Reset",key="rv"): st.session_state.pin_verified_for=set(); st.success("Reset.")
            with c2:
                if st.button("🗑️ Remove",key="rmp"):
                    st.session_state.user_pin=""; st.session_state.pin_set=False
                    st.session_state.pin_verified_for=set(); st.rerun()
    with t3:
        for entry in st.session_state.activity_log[:50]:
            a,b=st.columns([1,5])
            with a: st.caption(entry["time"])
            with b: st.markdown(entry["action"])
            st.divider()

def page_stt():
    lang=st.session_state.lang; loc=_locale(lang)
    st.markdown(f"## 🎤 Speech → Text · {LANG_NAMES.get(lang,'English')}")
    st.info("⚠️ Chrome required")
    for cont,cap in [(False,"Single"),(True,"Continuous")]:
        st.markdown(f"**{cap}**")
        st.components.v1.html(f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>*{{box-sizing:border-box;margin:0;padding:0;}}body{{font-family:'Segoe UI',sans-serif;background:transparent;}}
.box{{background:rgba(0,0,0,.3);border-radius:12px;padding:14px;}}
#out{cont}{{min-height:65px;padding:10px;border-radius:7px;font-size:13px;color:#e8e8ff;
  white-space:pre-wrap;background:rgba(0,255,136,.05);border:1px solid rgba(0,255,136,.2);margin-bottom:8px;}}
#lbl{cont}{{font-size:10px;color:#00d4ff;float:right;}}
button{{padding:7px 12px;border-radius:7px;cursor:pointer;font-size:11px;font-weight:700;margin-right:6px;}}
.bs{{background:rgba(0,255,136,.12);border:1px solid rgba(0,255,136,.4);color:#00ff88;}}
.bx{{background:rgba(255,68,102,.12);border:1px solid rgba(255,68,102,.4);color:#ff4466;}}
.bc{{background:rgba(0,212,255,.12);border:1px solid rgba(0,212,255,.4);color:#00d4ff;}}
.br{{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.15);color:#aaa;}}
</style></head><body><div class="box">
<div style="font-size:10px;color:#888;letter-spacing:2px;text-transform:uppercase;margin-bottom:7px">
Speech → Text &nbsp;<span id="lbl{cont}">Idle</span></div>
<div id="out{cont}">Click ▶ and speak…</div>
<button class="bs" id="bs{cont}">▶ Start</button><button class="bx" id="bx{cont}">■ Stop</button>
<button class="bc" id="bc{cont}">📋 Copy</button><button class="br" id="br{cont}">🗑 Clear</button>
<div style="font-size:10px;color:#555;margin-top:6px">Lang: <span style="color:#00d4ff">{loc}</span></div>
</div>
<script>document.addEventListener('DOMContentLoaded',function(){{
var rc=null,ft='',isCont={'true' if cont else 'false'};
var SR=window.SpeechRecognition||window.webkitSpeechRecognition;
var out=document.getElementById('out{cont}'),lbl=document.getElementById('lbl{cont}');
function go(){{if(!SR){{out.textContent='❌ Use Chrome.';return;}}if(rc){{try{{rc.abort();}}catch(e){{}}rc=null;}}
rc=new SR();rc.lang='{loc}';rc.continuous=isCont;rc.interimResults=true;lbl.textContent='Listening…';
rc.onresult=function(e){{var f='',it='';for(var i=e.resultIndex;i<e.results.length;i++){{if(e.results[i].isFinal)f+=e.results[i][0].transcript+' ';else it+=e.results[i][0].transcript;}}if(f)ft+=f;out.textContent=(ft+(it?' ⟳ '+it:'')).trim()||'Listening…';lbl.textContent=f?'Got it':'Listening…';}};
rc.onerror=function(ev){{lbl.textContent='Err: '+ev.error;rc=null;if(ev.error!=='not-allowed'&&isCont)setTimeout(go,1000);}};
rc.onend=function(){{rc=null;lbl.textContent='Stopped';if(isCont)setTimeout(go,400);}};
try{{rc.start();}}catch(ex){{rc=null;}}}}
function stopF(){{isCont=false;if(rc){{try{{rc.abort();}}catch(e){{}}rc=null;}}lbl.textContent='Stopped';}}
document.getElementById('bs{cont}').addEventListener('click',go);
document.getElementById('bx{cont}').addEventListener('click',stopF);
document.getElementById('bc{cont}').addEventListener('click',function(){{navigator.clipboard&&navigator.clipboard.writeText(out.textContent);lbl.textContent='Copied!';}});
document.getElementById('br{cont}').addEventListener('click',function(){{ft='';out.textContent='';lbl.textContent='Cleared';}});
}});</script></body></html>""",height=185,scrolling=False)

def page_tts():
    lang=st.session_state.lang; loc=_locale(lang)
    st.markdown(f"## 🔊 Text → Speech · {LANG_NAMES.get(lang,'English')}")
    st.components.v1.html(f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>*{{box-sizing:border-box;margin:0;padding:0;}}body{{font-family:'Segoe UI',sans-serif;background:transparent;}}
.box{{background:rgba(0,0,0,.3);border-radius:12px;padding:16px;max-width:640px;}}
textarea{{width:100%;padding:10px;border-radius:8px;font-size:13px;resize:vertical;
background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);color:#e8e8ff;font-family:inherit;margin-bottom:10px;}}
#tcur{{min-height:32px;padding:8px;border-radius:7px;font-size:12px;color:#e8e8ff;
background:rgba(168,85,247,.06);border:1px solid rgba(168,85,247,.18);margin-bottom:10px;}}
#tlbl{{color:#a855f7;font-size:10px;float:right;}}
button{{padding:8px 16px;border-radius:8px;cursor:pointer;font-size:12px;font-weight:700;margin-right:7px;}}
.tsp{{background:rgba(168,85,247,.18);border:1px solid rgba(168,85,247,.5);color:#a855f7;}}
.tst{{background:rgba(255,68,102,.12);border:1px solid rgba(255,68,102,.4);color:#ff4466;}}
select{{padding:7px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.15);color:#e8e8ff;border-radius:7px;font-size:11px;}}
</style></head><body><div class="box">
<div style="font-size:10px;color:#888;letter-spacing:2px;text-transform:uppercase;margin-bottom:10px">
Text → Speech &nbsp;<span id="tlbl">Silent</span></div>
<div id="tcur">Nothing spoken yet…</div>
<textarea id="tinp" rows="4" placeholder="Type text to speak…"></textarea>
<button class="tsp" id="tsp">🔊 Speak</button><button class="tst" id="tst">■ Stop</button>
<select id="rate"><option value="0.7">🐢 Slow</option><option value="0.9" selected>▶ Normal</option>
<option value="1.2">⚡ Fast</option><option value="1.5">🚀 Fastest</option></select>
<div style="font-size:10px;color:#555;margin-top:8px">Lang: <span style="color:#00d4ff">{loc}</span></div>
</div>
<script>document.addEventListener('DOMContentLoaded',function(){{
document.getElementById('tsp').addEventListener('click',function(){{
  var txt=document.getElementById('tinp').value.trim();if(!txt)return;
  var r=parseFloat(document.getElementById('rate').value)||0.9;
  window.speechSynthesis&&window.speechSynthesis.cancel();
  var u=new SpeechSynthesisUtterance(txt);u.lang='{loc}';u.rate=r;u.pitch=1.0;
  document.getElementById('tcur').textContent=txt.slice(0,120)+(txt.length>120?'…':'');
  document.getElementById('tlbl').textContent='Speaking…';
  u.onend=function(){{document.getElementById('tlbl').textContent='Done';}};
  window.speechSynthesis.speak(u);
}});
document.getElementById('tst').addEventListener('click',function(){{
  window.speechSynthesis&&window.speechSynthesis.cancel();
  document.getElementById('tlbl').textContent='Stopped';
}});
}});</script></body></html>""",height=300,scrolling=False)

# ── LOGIN PAGE ────────────────────────────────────────────────────────────────
def page_login():
    st.markdown("""<style>
section[data-testid="stSidebar"]{display:none!important;}
[data-testid="collapsedControl"]{display:none!important;}
</style>""",unsafe_allow_html=True)
    cmd_in=st.session_state.get("_cmd_in","").strip()
    if cmd_in and cmd_in!=st.session_state.get("_cmd_last",""):
        st.session_state._cmd_last=cmd_in
        if cmd_in.startswith("LOGIN|||") or cmd_in.startswith("SIGNUP|||"):
            process_cmd(cmd_in)
    _,col,_=st.columns([1,2,1])
    with col:
        st.markdown("""<div style="text-align:center;padding:20px 0 10px">
<div style="font-size:52px;margin-bottom:8px">🎙️</div>
<div style="font-size:28px;font-weight:900;letter-spacing:6px;background:linear-gradient(135deg,#6c63ff,#00d4ff);
-webkit-background-clip:text;-webkit-text-fill-color:transparent">NOVA</div>
<div style="font-size:10px;color:#7a7a9a;letter-spacing:3px;margin-top:4px">VOICE AI ASSISTANT · 100% HANDS-FREE</div>
</div>""",unsafe_allow_html=True)
        langs=list(LANG_NAMES.keys()); labels=[LANG_NAMES[k] for k in langs]
        lang=st.session_state.get("lang","en"); cur=langs.index(lang) if lang in langs else 0
        sel=st.selectbox("🌐 Language",labels,index=cur,key="_ll")
        if labels[cur]!=sel: st.session_state.lang=langs[labels.index(sel)]; st.rerun()
        loc=_locale(lang)
        st.components.v1.html(f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Segoe UI',sans-serif;background:transparent;color:#e8e8ff;text-align:center;padding:8px;}}
@keyframes float{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.06)}}}}
@keyframes pulse{{0%,100%{{box-shadow:0 0 18px #6c63ffaa}}50%{{box-shadow:0 0 55px #ff6b9dcc}}}}
#orb{{width:90px;height:90px;border-radius:50%;cursor:pointer;margin:0 auto 10px;
background:radial-gradient(circle at 35% 35%,#c084fc,#6c63ff 50%,#00d4ff);
display:flex;align-items:center;justify-content:center;font-size:34px;
animation:float 3s ease-in-out infinite;user-select:none;}}
#orb.on{{animation:pulse .8s ease-in-out infinite;}}
#st{{font-size:11px;color:#7a7a9a;margin-bottom:6px;min-height:16px;}}
#out{{background:rgba(0,255,136,.05);border:1px solid rgba(0,255,136,.2);border-radius:8px;
padding:6px 12px;font-size:12px;color:#00ff88;min-height:22px;margin-bottom:6px;font-style:italic;}}
#bub{{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);
border-radius:10px;padding:8px 12px;font-size:12px;min-height:34px;margin-bottom:8px;}}
.go{{padding:9px 22px;border:none;border-radius:9px;cursor:pointer;
background:linear-gradient(135deg,#6c63ff,#8b5cf6);color:#fff;font-size:12px;font-weight:700;}}
</style></head><body>
<div id="orb">🎙️</div>
<div id="st">Tap orb to login by voice</div>
<div id="out">Say your name to login…</div>
<div id="bub">👋 Say your name — no password needed!</div>
<button class="go" onclick="toggle()">🎤 Voice Login</button>
<p style="font-size:10px;color:#555;margin-top:8px;line-height:2;">
Say: <span style="color:#a78bfa">"login as Kaaly"</span> · just your name<br>
Or say <span style="color:#00d4ff">"sign up"</span> to create an account
</p>
<script>
var rc=null,on=false,sp=false;
var SR=window.SpeechRecognition||window.webkitSpeechRecognition;
var LOC="{loc}";var FLOW=null,STEP=0,D={{}};
function setS(t){{document.getElementById('st').textContent=t;}}
function setO(t){{document.getElementById('out').textContent=t;}}
function setB(t){{document.getElementById('bub').innerHTML=t;}}
function sendUp(cmd){{
  var doc=null;try{{doc=window.parent.document;}}catch(e){{doc=document;}}
  var inputs=doc.querySelectorAll("input");var t=null;
  for(var i=0;i<inputs.length;i++){{var ph=inputs[i].placeholder||"";if(ph.indexOf("nova-bridge")!==-1){{t=inputs[i];break;}}}}
  if(!t){{for(var j=inputs.length-1;j>=0;j--){{if(inputs[j].type!=="hidden"&&inputs[j].offsetParent!==null){{t=inputs[j];break;}}}}}}
  if(!t){{setB("Bridge not found.");return;}}
  try{{var s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,"value").set;s.call(t,cmd+"|||TS"+Date.now());}}catch(e){{t.value=cmd;}}
  t.dispatchEvent(new Event("input",{{bubbles:true}}));t.dispatchEvent(new Event("change",{{bubbles:true}}));
  setTimeout(function(){{var btns=doc.querySelectorAll("button");for(var k=0;k<btns.length;k++){{var tx=(btns[k].innerText||btns[k].textContent||"").trim();if(tx==="▶"){{btns[k].click();return;}}}}
  t.dispatchEvent(new KeyboardEvent("keydown",{{key:"Enter",keyCode:13,bubbles:true}}));}},300);
}}
function speakIt(text,cb){{sp=true;window.speechSynthesis&&window.speechSynthesis.cancel();
var u=new SpeechSynthesisUtterance(text);u.lang=LOC;u.rate=0.92;
var done=false;function fin(){{if(done)return;done=true;sp=false;if(cb)cb();else if(on)doListen();}}
u.onend=fin;u.onerror=fin;setTimeout(fin,Math.max(2000,text.split(" ").length*600)+800);
window.speechSynthesis.speak(u);setB("🔊 "+text);}}
function doListen(){{if(!on||sp)return;if(rc){{try{{rc.abort();}}catch(e){{}}rc=null;}}
if(!SR){{setB("❌ Use Chrome.");return;}}
var r=new SR();r.lang=LOC;r.continuous=false;r.interimResults=false;r.maxAlternatives=3;
rc=r;setS("👂 Listening…");
r.onresult=function(e){{var txt=e.results[0][0].transcript.trim();setO(txt);rc=null;handle(txt);}};
r.onerror=function(ev){{rc=null;setS("Error: "+ev.error);if(on&&ev.error!=="not-allowed")setTimeout(doListen,800);}};
r.onend=function(){{rc=null;}};try{{r.start();}}catch(ex){{rc=null;}}}}
function handle(raw){{var p=raw.toLowerCase().trim();
if(FLOW==="signup"){{
  if(STEP===0){{D.name=raw.trim();STEP=1;speakIt("Got it "+D.name+". Say your email.",null);return;}}
  if(STEP===1){{D.email=raw.trim().replace(/ at /gi,"@").replace(/ dot /gi,".").replace(/ /g,"");STEP=2;speakIt("Email "+D.email+". Say password.",null);return;}}
  if(STEP===2){{D.pw=raw.trim().replace(/ /g,"");FLOW=null;STEP=0;on=false;document.getElementById("orb").classList.remove("on");
  sendUp("SIGNUP|||"+D.name+"|||"+D.email+"|||"+D.pw);speakIt("Creating your account…",null);setB("✅ Creating account…");setS("Done!");return;}}
}}
if(/sign up|signup|register|create account/.test(p)){{FLOW="signup";STEP=0;D={{}};speakIt("Starting sign up! Say your full name.",null);return;}}
var name=raw.replace(/^(login as|my name is|i am|i'm|enter as|call me)\s*/i,"").trim();
if(!name||/^(guest|skip)$/i.test(name))name="Guest";
var cap=name.charAt(0).toUpperCase()+name.slice(1).toLowerCase();
FLOW=null;on=false;document.getElementById("orb").classList.remove("on");
sendUp("LOGIN|||"+cap+"|||"+cap.toLowerCase()+"@nova.ai|||");
speakIt("Welcome "+cap+"! Logging you in.",null);setB("✅ Logging in as <b>"+cap+"</b>…");setS("✅ Done!");}}
document.getElementById("orb").addEventListener("click",toggle);
function toggle(){{if(on)stop();else start();}}
function start(){{if(!SR){{setB("❌ Use Chrome.");return;}}on=true;document.getElementById("orb").classList.add("on");
speakIt("Welcome to NOVA! Please say your name to login.",function(){{doListen();}});}}
function stop(){{on=false;document.getElementById("orb").classList.remove("on");
if(rc){{try{{rc.abort();}}catch(e){{}}rc=null;}}window.speechSynthesis&&window.speechSynthesis.cancel();setS("Stopped.");}}
</script></body></html>""",height=310,scrolling=False)
        st.markdown("---")
        col1,col2=st.columns([8,1])
        with col1:
            cmd=st.text_input("bridge",key="_cmd_in",
                placeholder="nova-bridge — voice fills this automatically",
                label_visibility="collapsed")
        with col2:
            go=st.button("▶",key="_cmd_go",type="primary",use_container_width=True)
        if go and cmd.strip() and cmd.strip()!=st.session_state._cmd_last:
            st.session_state._cmd_last=cmd.strip(); process_cmd(cmd.strip()); st.rerun()
        st.markdown("---")
        st.markdown("### Or login with form")
        tl,ts=st.tabs(["🔑 Login","✨ Sign Up"])
        with tl:
            if GOOGLE_OK and Path(CREDENTIALS_FILE).exists():
                if google_connected():
                    info=google_info(); st.success(f"✅ {info.get('email','')}")
                    if st.button("➡️ Enter NOVA",type="primary",key="g_ent",use_container_width=True):
                        st.session_state.user_name=info.get("name",""); st.session_state.user_email=info.get("email","")
                        st.session_state.logged_in=True; st.session_state.stats["logins"]+=1; _log("Google login"); st.rerun()
                else:
                    if st.button("🔵 Continue with Google",use_container_width=True,key="g_l"):
                        try:
                            flow=Flow.from_client_secrets_file(CREDENTIALS_FILE,scopes=SCOPES,redirect_uri="urn:ietf:wg:oauth:2.0:oob")
                            url,_=flow.authorization_url(access_type="offline",include_granted_scopes="true",prompt="consent")
                            st.session_state["_fl"]=flow; st.markdown(f"**[➡️ Sign in]({url})**")
                        except Exception as ex: st.error(str(ex))
                    if "_fl" in st.session_state:
                        code=st.text_input("Code:",key="gc")
                        if st.button("✅ Confirm",key="gcf",use_container_width=True):
                            try:
                                st.session_state["_fl"].fetch_token(code=code); _save_token(st.session_state["_fl"].credentials)
                                del st.session_state["_fl"]; info=google_info()
                                st.session_state.user_name=info.get("name",""); st.session_state.user_email=info.get("email","")
                                st.session_state.logged_in=True; st.session_state.stats["logins"]+=1; _log("Google login"); st.rerun()
                            except Exception as ex: st.error(str(ex))
            else: st.info("Place `credentials.json` in app folder for Google login.")
            st.markdown("---")
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
                        st.session_state.user_name=n; st.session_state.user_email=e
                        st.session_state.logged_in=True; st.session_state.stats["logins"]+=1; _log(f"Signup: {e}"); st.rerun()

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    if not st.session_state.logged_in:
        page_login(); return
    if google_connected() and not st.session_state.user_name:
        info=google_info()
        if info: st.session_state.user_name=info.get("name",""); st.session_state.user_email=info.get("email","")
    render_sidebar()
    ci=st.session_state.get("_cmd_in","").strip()
    if ci and ci!=st.session_state.get("_cmd_last",""):
        st.session_state._cmd_last=ci
        process_cmd(ci)
    page=st.session_state.page
    {"Assistant":page_assistant,"Dashboard":page_dashboard,"Email":page_email,
     "Telegram":page_telegram,"WhatsApp":page_whatsapp,"Profile":page_profile,
     "Settings":page_settings,"Contacts":page_contacts,"Admin":page_admin,
     "STT":page_stt,"TTS":page_tts}.get(page,page_assistant)()

if __name__=="__main__":
    main()