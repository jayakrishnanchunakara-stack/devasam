import streamlit as st
import yt_dlp
import google.generativeai as genai
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import json
import os
from datetime import datetime

# ==========================================
# 1. PAGE CONFIGURATION & FILES
# ==========================================
st.set_page_config(page_title="PSC Smart Study Analyzer", page_icon="📚", layout="wide")
CONFIG_FILE = "api_keys.json"
NOTES_FILE = "saved_notes.json"

# ==========================================
# 2. SYLLABUS DATABASE
# ==========================================
SYLLABUS_DATA = {
    "1. ആനുകാലിക വിഷയങ്ങളും പൊതുവിവരങ്ങളും": {
        "അന്തർദേശീയ തലം": ["രാഷ്ട്രീയ മേഖല", "സാമ്പത്തിക മേഖല", "സാമൂഹിക മേഖല", "ശാസ്ത്ര സാങ്കേതിക മേഖല", "കായിക മേഖല", "കലാ വിനോദ മേഖല", "സാഹിത്യ മേഖല"],
        "ദേശീയ തലം": ["രാഷ്ട്രീയ മേഖല", "സാമ്പത്തിക മേഖല", "സാമൂഹിക മേഖല", "ശാസ്ത്ര സാങ്കേതിക മേഖല", "കായിക മേഖല", "കലാ വിനോദ മേഖല", "സാഹിത്യ മേഖല"],
        "പ്രാദേശിക തലം": ["രാഷ്ട്രീയ മേഖല", "സാമ്പത്തിക മേഖല", "സാമൂഹിക മേഖല", "ശാസ്ത്ര സാങ്കേതിക മേഖല", "കായിക മേഖല", "കലാ വിനോദ മേഖല", "സാഹിത്യ മേഖല"],
        "ബഹിരാകാശ പര്യവേഷണ മേഖല (ഇന്ത്യ)": ["ഇന്ത്യ കൈവരിച്ച പ്രധാനനേട്ടങ്ങൾ", "പ്രമുഖ ദേശീയ/അന്തർദേശീയ ബഹിരാകാശ ഗവേഷണ സ്ഥാപനങ്ങൾ, സാരഥികൾ"],
        "സ്വാതന്ത്ര്യാനന്തര ഇന്ത്യ": ["സാമൂഹ്യ മേഖലയിലെ നേട്ടങ്ങൾ", "സാമ്പത്തിക മേഖലയിലെ നേട്ടങ്ങൾ", "വ്യാവസായിക മേഖലയിലെ നേട്ടങ്ങൾ", "വിവരവിനിമയ മേഖലയിലെ നേട്ടങ്ങൾ"]
    },
    "2. സാമ്പത്തിക രംഗം": {
        "ഇന്ത്യയുടെ സാമ്പത്തിക ആസൂത്രണം": ["പഞ്ചവത്സര പദ്ധതികൾ", "പ്ലാനിംഗ് കമ്മീഷൻ", "നീതി ആയോഗ്"],
        "സാമ്പത്തിക പരിഷ്കാരങ്ങളും സ്ഥാപനങ്ങളും": ["നവസാമ്പത്തിക പരിഷ്കാരങ്ങൾ", "ധനകാര്യ സ്ഥാപനങ്ങൾ"]
    },
    "3. കായിക രംഗം": {
        "പ്രധാന കായികതാരങ്ങളും നേട്ടങ്ങളും": ["കേരളത്തിലെ പ്രധാന കായികതാരങ്ങൾ", "ഇന്ത്യയിലെ പ്രധാന കായികതാരങ്ങൾ", "ലോകത്തിലെ പ്രധാന കായികതാരങ്ങൾ"],
        "കായിക രംഗത്തെ ഇന്ത്യൻ കുതിപ്പ്": ["അന്തർദേശീയ മത്സരങ്ങളിലെ മലയാളി സാന്നിദ്ധ്യം", "ദേശീയ മത്സരങ്ങളിലെ മലയാളി സാന്നിദ്ധ്യം"],
        "അവാർഡുകളും ട്രോഫികളും": ["പ്രധാന അവാർഡുകൾ, ജേതാക്കൾ", "പ്രധാന ട്രോഫികൾ, ബന്ധപ്പെട്ട മത്സരങ്ങൾ"],
        "പ്രധാന കായിക മേളകൾ": ["ഒളിമ്പിക്സ്", "കോമൺവെൽത്ത് ഗെയിംസ്", "ഏഷ്യൻ ഗെയിംസ്"],
        "ദേശീയ കായിക ഇനങ്ങൾ": ["ഓരോ രാജ്യത്തിന്റെയും ദേശീയ കായിക ഇനങ്ങൾ / വിനോദങ്ങൾ"]
    },
    "4. ഗതാഗതം": {
        
        "റോഡ് ഗതാഗതം": ["ദേശീയ പാതകൾ", "സംസ്ഥാന പാതകൾ"],
        "റെയിൽവേ ഗതാഗതം": ["ഇൻഡ്യൻ റെയിൽവേ", "അന്താരാഷ്ട്ര തീവണ്ടികൾ", "വിവിധ റെയിൽവേ സോണുകൾ", "മെട്രോ റെയിലുകൾ"],
        "വ്യോമയാനം & ജലപാതകൾ": ["അന്താരാഷ്ട്ര വിമാനത്താവളങ്ങൾ", "ദേശീയ ജലപാതകൾ", "കപ്പൽ നിർമ്മാണ ശാലകൾ"]
    },
    "5. കല, സാഹിത്യം, സംസ്കാരം": {
        "സാഹിത്യം": ["പ്രമുഖ സാഹിത്യകാരൻമാരും രചനകളും", "പ്രശസ്തമായ വരികൾ, തൂലികാ നാമങ്ങൾ", "പ്രധാനപ്പെട്ട അവാർഡുകൾ", "സംസ്ഥാന സർക്കാർ സ്ഥാപനങ്ങൾ, സാരഥികൾ"],
        "കല": ["കേരളത്തിലെ പ്രധാന ദൃശ്യ-ശ്രാവ്യകലകൾ", "കേരളീയ കലാ പാരമ്പര്യം", "നാടൻകലകൾ, അനുഷ്ഠാനകലകൾ"],
        "സംസ്കാരം": ["പ്രധാന ആഘോഷങ്ങൾ, ഉത്സവങ്ങൾ", "സാംസ്കാരിക കേന്ദ്രങ്ങൾ, സ്മാരകങ്ങൾ", "സാംസ്കാരിക നായകർ, സംഭാവനകൾ", "കേരളത്തിൻ്റെ സാംസ്കാരിക വൈവിധ്യം"]
    },
    "6. ഭരണവും രാഷ്ട്രീയവും": {
        "അധികാര വികേന്ദ്രീകരണം": ["ജനാധിപത്യ അധികാര വികേന്ദ്രീകരണം ലക്ഷ്യവും പ്രയോജനവും", "ഗ്രാമീണ/നഗര സ്വയംഭരണ സ്ഥാപനങ്ങൾ", "കോർപ്പറേഷനുകൾ, മുൻസിപ്പാലിറ്റികൾ, പഞ്ചായത്തുകൾ", "ദേശീയ ഗ്രാമീണ തൊഴിൽ പദ്ധതികൾ"],
        "സംസ്ഥാന ഭരണ സംവിധാനങ്ങൾ": ["സംസ്ഥാന ഭരണവും ഭരണ സംവിധാനങ്ങളും", "മന്ത്രിസഭ, വകുപ്പുകൾ, ചീഫ് സെക്രട്ടറി", "ഭരണഘടനാ സ്ഥാപനങ്ങൾ, ബോർഡുകൾ, കമ്മീഷനുകൾ"],
        "ജില്ലാ ഭരണം": ["കളക്ടർമാർ: പ്രധാന ചുമതലകൾ, അധികാരങ്ങൾ"],
        "തെരഞ്ഞെടുപ്പ്": ["കേന്ദ്ര/സംസ്ഥാന തെരഞ്ഞെടുപ്പ് കമ്മിഷനുകൾ", "ലോകസഭാ/നിയമസഭാ തെരഞ്ഞെടുപ്പുകൾ, ഇലക്ഷൻ പരിഷ്കാരങ്ങൾ"]
    },
    "7. ഇന്ത്യൻ ഭരണഘടന": {
        "ഭരണഘടനയുടെ അടിസ്ഥാനം": ["ഭരണഘടന നിർമ്മാണ സമിതി", "ആമുഖം, പൗരത്വം", "മൗലികാവകാശങ്ങൾ, മൗലിക കർത്തവ്യങ്ങൾ, നിർദ്ദേശക തത്ത്വങ്ങൾ"],
        "ഭരണ സംവിധാനവും ഭേദഗതികളും": ["ഗവൺമെന്റിന്റെ ഘടകങ്ങൾ", "പ്രധാനപ്പെട്ട ഭരണഘടനാ ഭേദഗതികൾ", "യൂണിയൻ ലിസ്റ്റ്, സ്റ്റേറ്റ് ലിസ്റ്റ്, കൺകറൻ്റ് ലിസ്റ്റ്", "ഭരണഘടനാ സ്ഥാപനങ്ങൾ"],
        "ദേശീയ ചിഹ്നങ്ങൾ": ["ദേശീയഗാനം, ദേശീയഗീതം, ദേശീയപതാക"]
    },
    "8. സഹകരണ മേഖല": {
        "കേരളത്തിലെ സഹകരണ പ്രസ്ഥാനം": ["വിദ്യാഭ്യാസ, ആരോഗ്യ, സാമ്പത്തിക മേഖലകളിലെ സഹകരണ സ്ഥാപനങ്ങൾ", "ഉദ്ദേശ്യ ലക്ഷ്യങ്ങൾ, ഘടന, സാരഥികൾ"],
        "കോ-ഓപ്പറേറ്റീവ് യൂണിയൻ": ["സംസ്ഥാന കോ-ഓപ്പറേറ്റീവ് യൂണിയൻ - ഉദ്ദേശ ലക്ഷ്യങ്ങൾ"]
    },
    "9. ഭൂമിശാസ്ത്രം (Geography)": {
        "പൊതു ഭൂമിശാസ്ത്രം": ["ഭൂമിശാസ്ത്രത്തിന്റെ അടിസ്ഥാന തത്വങ്ങൾ", "അന്തരീക്ഷം, ഭൗമോപരിതലം", "മഹാസമുദ്രങ്ങൾ, ഭുഖണ്ഡങ്ങൾ", "ലോകരാഷ്ട്രങ്ങളും അവയുടെ സവിശേഷതകളും"],
        "ഇന്ത്യയുടെ ഭൂപ്രകൃതി": ["സംസ്ഥാനങ്ങൾ, അവയുടെ സവിശേഷതകൾ", "ഉത്തരപർവ്വത മേഖല, ഉത്തരമഹാസമതലം, തീരദേശം", "നദികൾ, ഊർജ്ജസ്രോതസ്സുകൾ, കൃഷി"],
        "കേരളത്തിന്റെ ഭുപ്രകൃതി": ["ജില്ലകൾ, കാലാവസ്ഥ", "നദികൾ, കായലുകൾ", "മണ്ണിനങ്ങൾ, സസ്യജന്തു ജാലങ്ങൾ", "കൃഷിയും ഗവേഷണ സ്ഥാപനങ്ങളും", "വാർത്താവിനിമയം, വ്യവസായം"]
    },
    "10. പരിസ്ഥിതിയും വനവും": {
        "പരിസ്ഥിതി സംരക്ഷണവും പ്രശ്നങ്ങളും": ["സംരക്ഷിത പ്രദേശങ്ങൾ (ദേശീയോദ്യാനങ്ങൾ, വന്യജീവി സങ്കേതങ്ങൾ)", "പരിസ്ഥിതി സംഘടനകൾ, നിയമങ്ങൾ, സ്ഥാപനങ്ങൾ", "പ്രമുഖ ദേശീയ പരിസ്ഥിതി പ്രവർത്തകർ", "ആഗോളപ്രശ്നങ്ങൾ, മലിനീകരണങ്ങൾ", "ആഗോളതാപനം, ഓസോൺ പാളികളുടെ ശോഷണം", "കാലാവസ്ഥാ വ്യതിയാനങ്ങൾ (ഗ്രീൻ ഹൗസ് ഗ്യാസസ്)", "പ്രകൃതി ദുരന്തങ്ങൾ, ദുരന്തലഘൂകരണ പ്രവർത്തനങ്ങൾ"],
        "വനങ്ങളും ജലസ്രോതസ്സുകളും": ["വനങ്ങളുടെ പ്രാധാന്യം", "ജൈവ വൈവിധ്യവും സംരക്ഷണവും, ഇക്കോ ടൂറിസം", "വനസംരക്ഷണ നിയമങ്ങൾ, വനം കുറ്റകൃത്യങ്ങൾക്കുള്ള ശിക്ഷകൾ", "വിവിധ ജലസ്രോതസ്സുകൾ, പ്രമുഖ ജലവൈദ്യുത പദ്ധതികൾ"]
    },
    "11. ചരിത്രം (History)": {
        "കേരള ചരിത്രം": ["പ്രാചീനകേരളം, മധ്യകാല കേരളം", "യൂറോപ്യൻമാരുടെ വരവ്, ചെറുത്തുനിൽപുകൾ", "തിരുവിതാംകൂറിന്റെ ചരിത്രം", "സാമൂഹ്യ-മത നവോത്ഥാന പ്രസ്ഥാനങ്ങൾ", "ഐക്യകേരള പ്രസ്ഥാനം, സംസ്ഥാന രൂപീകരണം", "സാമൂഹ്യരാഷട്രീയ ചരിത്രം", "വിദ്യാഭ്യാസ-ആരോഗ്യ-വ്യാവസായിക മേഖലകളിലെ നേട്ടങ്ങൾ"],
        "ഇന്ത്യൻ ചരിത്രം": ["ബ്രിട്ടീഷ് ആധിപത്യം, ഒന്നാം സ്വാതന്ത്ര്യസമരം, സ്വദേശി പ്രസ്ഥാനം", "സാമൂഹ്യപരിഷ്കരണ പ്രസ്ഥാനങ്ങൾ, വർത്തമാനപത്രങ്ങൾ", "സ്വാതന്ത്യ സമരവും മഹാത്മാഗാന്ധിയും", "സ്വാതന്ത്ര്യാനന്തര കാലഘട്ടം, സംസ്ഥാനങ്ങളുടെ പുനഃസംഘടന", "ശാസത്ര വിദ്യാഭ്യാസ മേഖലയിലെ പുരോഗതി, വിദേശ നയം"],
        "ലോക ചരിത്രം": ["ഇംഗ്ലണ്ടിലെ, അമേരിക്കൻ, ഫ്രഞ്ച്, റഷ്യൻ, ചൈനീസ് വിപ്ലവങ്ങൾ", "രണ്ടാം ലോക മഹായുദ്ധാനന്തര രാഷ്ട്രീയ ചരിത്രം"]
    },
    "12. അന്താരാഷ്ട്ര സംഘടനകൾ": {
        "ഐക്യരാഷ്ട്രസഭ (UN)": ["പിറവിയും ലക്ഷ്യങ്ങളും, അടിസ്ഥാനതത്വങ്ങൾ", "അംഗരാജ്യങ്ങൾ, പ്രധാന ഘടകങ്ങൾ", "അനുബന്ധ സംഘടനകൾ, ആസ്ഥാനങ്ങൾ"],
        "മറ്റ് അന്താരാഷ്ട്ര കൂട്ടായ്മകൾ": ["കോമൺവെൽത്ത്, ചേരിചേരാ പ്രസ്ഥാനം", "സാർക്ക്, ആസിയാൻ, ബ്രിക്സ്"]
    },
    "13. നിയമങ്ങളും പദ്ധതികളും": {
        "വികസന-സുരക്ഷാ നിയമങ്ങളും പദ്ധതികളും": ["സാമൂഹിക സാമ്പത്തിക വികസനത്തിനായുള്ള നിയമങ്ങൾ", "സാമൂഹ്യ സുരക്ഷാ പദ്ധതികൾ, സ്ഥാപനങ്ങൾ"],
        "അഴിമതി നിരോധനം": ["അഴിമതി നിരോധന നിയമങ്ങൾ, ലോക്‌പാൽ, CBI", "അഴിമതി നിർമ്മാർജന സ്ഥാപനങ്ങൾ, ബ്യൂറോകൾ"],
        "റോഡ് സുരക്ഷ": ["റോഡ് സുരക്ഷാ നിയമങ്ങൾ, ട്രാഫിക് നിയമ ലംഘനങ്ങൾ", "ട്രാഫിക് നിയമം നടപ്പിലാക്കൽ അധികാരികൾ"]
    }
}

# ==========================================
# 3. API KEY & DATA MANAGEMENT 
# ==========================================
def load_keys():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_keys(g_key, y_key):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"GEMINI_KEY": g_key, "YOUTUBE_KEY": y_key}, f)

def load_notes():
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_new_note(main, cat, sub, content):
    notes = load_notes()
    note_key = f"{main} | {cat} | {sub}"
    notes[note_key] = {
        "main_topic": main,
        "category": cat,
        "sub_topic": sub,
        "content": content,
        "date_saved": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=4)

def delete_note(note_key):
    notes = load_notes()
    if note_key in notes:
        del notes[note_key]
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump(notes, f, ensure_ascii=False, indent=4)

saved_keys = load_keys()

if not saved_keys:
    st.title("🔑 API Configuration")
    st.info("ആദ്യമായി ഉപയോഗിക്കുമ്പോൾ API കീകൾ നൽകുക.")
    gemini_input = st.text_input("Gemini API Key", type="password")
    youtube_input = st.text_input("YouTube API Key", type="password")
    
    if st.button("💾 Save Keys & Start App"):
        if gemini_input and youtube_input:
            save_keys(gemini_input, youtube_input)
            st.rerun()
        else:
            st.error("Please enter both keys to continue.")
    st.stop()

genai.configure(api_key=saved_keys["GEMINI_KEY"])
youtube = build('youtube', 'v3', developerKey=saved_keys["YOUTUBE_KEY"])

# ==========================================
# 4. YOUTUBE API & GEMINI FUNCTIONS
# ==========================================
def get_youtube_videos(query, max_results, start_year, end_year):
    try:
        start_date = f"{start_year}-01-01T00:00:00Z"
        end_date = f"{end_year}-12-31T23:59:59Z"
        search_request = youtube.search().list(part="id,snippet", q=query, type="video", publishedAfter=start_date, publishedBefore=end_date, maxResults=max_results)
        search_response = search_request.execute()
        
        videos = []
        for item in search_response.get("items", []):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            stats = youtube.videos().list(part="statistics", id=video_id).execute()["items"][0]["statistics"]
            
            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))
            comments = int(stats.get("commentCount", 0))
            score = round(((likes + comments) / views) * 100, 2) if views > 0 else 0
                
            videos.append({"id": video_id, "title": title, "views": views, "likes": likes, "comments": comments, "score": score})
        return videos
    except Exception as e:
        return []

def generate_note_from_video(video_id, exam_name):
    try:
        # 1. ആദ്യം സബ്‌ടൈറ്റിൽ ഉണ്ടോ എന്ന് നോക്കുന്നു (Fastest Way)
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'ml', 'hi'])
        transcript_text = " ".join([t['text'] for t in transcript_list])
        
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"താഴെ നൽകിയിട്ടുള്ളത് ഒരു പഠന വീഡിയോയുടെ ട്രാൻസ്ക്രിപ്റ്റ് ആണ്. ഇതിൽ നിന്നും {exam_name} പരീക്ഷയ്ക്ക് പഠിക്കുന്ന വിദ്യാർത്ഥിക്ക് വേണ്ട കൃത്യമായ വിവരങ്ങൾ മാത്രം പോയിന്റ് അടിസ്ഥാനത്തിൽ മലയാളത്തിൽ ഒരു നോട്സ് ആയി തയ്യാറാക്കുക.\n\nVideo Transcript:\n{transcript_text[:100000]}"
        return model.generate_content(prompt).text
        
    except:
        # 2. സബ്‌ടൈറ്റിൽ ഇല്ലെങ്കിൽ നേരിട്ട് ഓഡിയോ കേൾക്കുന്നു! (Super Power)
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            audio_file = f"audio_{video_id}.m4a"
            
            # എ. ഓഡിയോ മാത്രം ഡൗൺലോഡ് ചെയ്യുന്നു (403 Error Bypass ഉൾപ്പെടെ)
            ydl_opts = {
                'format': 'm4a/bestaudio/best', 
                'outtmpl': audio_file, 
                'quiet': True,
                'extractor_args': {'youtube': {'player_client': ['android', 'web']}} # യൂട്യൂബിനെ പറ്റിക്കാനുള്ള വരി
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            # ബി. ഓഡിയോ ഫയൽ Gemini-ലേക്ക് നൽകുന്നു
            sample_file = genai.upload_file(path=audio_file)
            model = genai.GenerativeModel("gemini-2.5-flash")
            prompt = f"ഈ ഓഡിയോ ക്ലാസ്സിൽ നിന്നും {exam_name} പരീക്ഷയ്ക്ക് പഠിക്കുന്ന വിദ്യാർത്ഥിക്ക് വേണ്ട കൃത്യമായ വിവരങ്ങൾ മാത്രം പോയിന്റ് അടിസ്ഥാനത്തിൽ മലയാളത്തിൽ ഒരു നോട്സ് ആയി തയ്യാറാക്കുക. പ്രധാനപ്പെട്ടവ ബോൾഡ് ചെയ്യുക."
            
            response = model.generate_content([prompt, sample_file])
            
            # സി. ഫയലുകൾ ഡിലീറ്റ് ചെയ്യുന്നു (To save space)
            genai.delete_file(sample_file.name)
            if os.path.exists(audio_file):
                os.remove(audio_file)
                
            return response.text
            
        except Exception as e:
            return f"ക്ഷമിക്കണം, ഈ വീഡിയോയുടെ ഓഡിയോ എടുക്കാൻ സാധിച്ചില്ല. Error: {e}"

# ==========================================
# 5. SIDEBAR CONTROLS (തിരികെ കൊണ്ടുവന്നത്!)
# ==========================================
st.sidebar.header("⚙️ Search Filters")

years = list(range(2016, 2027))
col1, col2 = st.sidebar.columns(2)
with col1:
    start_year = st.sidebar.selectbox("From Year", options=years, index=5)
with col2:
    end_year = st.sidebar.selectbox("To Year", options=years, index=10)

max_vids = st.sidebar.slider("Max Videos to Fetch", 5, 20, 10)
sort_option = st.sidebar.selectbox("Sort Videos By:", ["Engagement Score", "Views", "Likes", "Comments"])
target_exam = st.sidebar.selectbox("Target Exam", ["Devaswom Board", "Kerala PSC", "General"])

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Reset API Keys"):
    os.remove(CONFIG_FILE)
    st.rerun()

# ==========================================
# 6. MAIN UI & DROPDOWNS
# ==========================================
st.title("📚 Smart Study Analyzer")
st.markdown("##### AI-Powered Video & Notes Discovery Dashboard for PSC")
st.markdown("---")

st.subheader("🎯 വിഷയം കൃത്യമായി തിരഞ്ഞെടുക്കുക")
col_a, col_b, col_c = st.columns(3)

with col_a:
    main_topic = st.selectbox("1. പ്രധാന വിഷയം", options=list(SYLLABUS_DATA.keys()))
with col_b:
    sub_category = st.selectbox("2. വിഭാഗം", options=list(SYLLABUS_DATA[main_topic].keys()))
with col_c:
    sub_topic = st.selectbox("3. ഉപവിഷയം", options=SYLLABUS_DATA[main_topic][sub_category])

search_query = f"{sub_topic} {target_exam} Malayalam"

# ==========================================
# 7. TABS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📺 യൂട്യൂബ് ക്ലാസുകൾ", "🚀 AI Deep Search", "🌐 ഇന്റർനെറ്റ് / AI നോട്സ്", "📂 സേവ് ചെയ്ത നോട്സുകൾ"])

# --- TAB 1 ---
with tab1:
    if "searched_videos" not in st.session_state: st.session_state.searched_videos = None
    if st.button("🔍 വീഡിയോകൾ തിരയുക", type="primary"):
        with st.spinner(f"യൂട്യൂബിൽ തിരയുന്നു..."):
            videos = get_youtube_videos(search_query, max_vids, start_year, end_year)
            if videos:
                if sort_option == "Views":
                    st.session_state.searched_videos = sorted(videos, key=lambda x: x['views'], reverse=True)
                elif sort_option == "Likes":
                    st.session_state.searched_videos = sorted(videos, key=lambda x: x['likes'], reverse=True)
                elif sort_option == "Comments":
                    st.session_state.searched_videos = sorted(videos, key=lambda x: x['comments'], reverse=True)
                else:
                    st.session_state.searched_videos = sorted(videos, key=lambda x: x['score'], reverse=True)
            else:
                st.session_state.searched_videos = None
                st.warning("വീഡിയോകൾ ഒന്നും കണ്ടെത്താനായില്ല.")

    if st.session_state.searched_videos:
        for i, vid in enumerate(st.session_state.searched_videos):
            with st.expander(f"#{i+1}: {vid['title']} ⭐ Score: {vid['score']}"):
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.image(f"https://img.youtube.com/vi/{vid['id']}/hqdefault.jpg", use_container_width=True)
                    st.markdown(f"**👁️ Views:** {vid['views']} | **👍 Likes:** {vid['likes']}")
                    st.markdown(f"[🔗 വീഡിയോ കാണുക](https://www.youtube.com/watch?v={vid['id']})")
                with col2:
                    if st.button("📝 Video ➔ PSC Notes ആക്കുക", key=f"note_{vid['id']}"):
                        with st.spinner("നോട്സ് തയ്യാറാക്കുന്നു..."):
                            st.session_state[f"vid_note_{vid['id']}"] = generate_note_from_video(vid['id'], target_exam)
                
                if f"vid_note_{vid['id']}" in st.session_state:
                    vid_edited = st.text_area("Video Notes (തിരുത്താം):", value=st.session_state[f"vid_note_{vid['id']}"], height=300, key=f"ta_{vid['id']}")
                    if st.button("💾 സേവ് ചെയ്യുക", key=f"save_{vid['id']}"):
                        save_new_note(main_topic, sub_category, sub_topic, vid_edited)
                        st.success("സേവ് ചെയ്തു!")

# --- TAB 2 ---
with tab2:
    st.markdown("### 🚀 പുതിയ വാക്കുകൾ വച്ചുള്ള തിരച്ചിൽ")
    if "deep_searched_videos" not in st.session_state:
        st.session_state.deep_searched_videos = None

    deep_query = st.text_input("AI കണ്ടെത്തിയ പുതിയ കീവേഡ് ഇവിടെ നൽകുക:")
    if st.button("Search YouTube with New Keyword", type="primary"):
        if deep_query:
            with st.spinner("തിരയുന്നു..."):
                st.session_state.deep_searched_videos = get_youtube_videos(deep_query, max_vids, start_year, end_year)
        else:
            st.warning("കീവേഡ് നൽകുക!")

    if st.session_state.deep_searched_videos:
        for i, vid in enumerate(st.session_state.deep_searched_videos):
            with st.expander(f"#{i+1}: {vid['title']}"):
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.image(f"https://img.youtube.com/vi/{vid['id']}/hqdefault.jpg", use_container_width=True)
                    st.markdown(f"[🔗 വീഡിയോ കാണുക](https://www.youtube.com/watch?v={vid['id']})")
                with col2:
                    if st.button("📝 Video ➔ Notes ആക്കുക", key=f"deep_note_{vid['id']}"):
                        with st.spinner("നോട്സ് തയ്യാറാക്കുന്നു..."):
                            st.session_state[f"deep_vid_note_{vid['id']}"] = generate_note_from_video(vid['id'], target_exam)
                
                if f"deep_vid_note_{vid['id']}" in st.session_state:
                    deep_edited = st.text_area("Notes:", value=st.session_state[f"deep_vid_note_{vid['id']}"], height=300, key=f"dta_{vid['id']}")
                    if st.button("💾 സേവ് ചെയ്യുക", key=f"dsave_{vid['id']}"):
                        save_new_note(main_topic, sub_category, sub_topic, deep_edited)
                        st.success("സേവ് ചെയ്തു!")

# --- TAB 3 ---
with tab3:
    st.info(f"തിരഞ്ഞെടുത്ത വിഷയം: **{sub_topic}**")
    if "ai_note" not in st.session_state: st.session_state.ai_note = ""

    if st.button(f"🌐 1. Generate Precise PSC Notes", type="primary"):
        with st.spinner("AI നോട്സ് തയ്യാറാക്കുന്നു..."):
            model = genai.GenerativeModel("gemini-2.5-flash")
            prompt = f"താങ്കൾ ഒരു കേരള PSC / {target_exam} പരീക്ഷാ വിദഗ്ദ്ധനാണ്. '{sub_topic}' എന്ന വിഷയത്തെക്കുറിച്ച് പഠിക്കാൻ എളുപ്പത്തിനായി വിവരങ്ങൾ പട്ടികകളായും (Tables) പോയിന്റുകളായും മലയാളത്തിൽ തയ്യാറാക്കുക."
            st.session_state.ai_note = model.generate_content(prompt).text
            st.rerun()

    if st.session_state.ai_note:
        edited_notes = st.text_area("📚 Study Notes (തിരുത്താം):", value=st.session_state.ai_note, height=400)
        
        st.markdown("#### 🔍 കൂടുതൽ വിവരങ്ങൾ വേണമെങ്കിൽ:")
        deep_word = st.text_input("കൂടുതൽ അറിയേണ്ട വാക്ക് നൽകുക:")
        if deep_word:
            web_prompt = f"'{deep_word}' എന്ന വിഷയത്തെക്കുറിച്ച് കേരള PSC പരീക്ഷയ്ക്ക് പഠിക്കുന്ന ഒരാൾക്ക് വേണ്ട കൃത്യമായ വിവരങ്ങൾ പോയിന്റുകളായി മലയാളത്തിൽ നൽകുക."
            st.code(web_prompt, language="markdown")
            st.markdown("👉 **[Click Here to Open Gemini Website](https://gemini.google.com/app)**", unsafe_allow_html=True)
            
        if st.button("💾 2. സിലബസിലേക്ക് സേവ് ചെയ്യുക", type="primary"):
            save_new_note(main_topic, sub_category, sub_topic, edited_notes)
            st.success("സേവ് ചെയ്തു!")

# --- TAB 4 ---
with tab4:
    saved_all_notes = load_notes()
    if not saved_all_notes:
        st.info("നോട്സുകൾ ഒന്നും സേവ് ചെയ്തിട്ടില്ല.")
    else:
        for key, note_data in saved_all_notes.items():
            with st.expander(f"📖 {note_data['main_topic']} ➔ {note_data['sub_topic']}"):
                st.caption(f"Category: {note_data['category']} | Saved on: {note_data['date_saved']}")
                st.markdown(note_data['content'])
                if st.button(f"🗑️ Delete", key=f"del_{key}"):
                    delete_note(key)
                    st.rerun()
