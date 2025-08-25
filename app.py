import streamlit as st
from deep_translator import GoogleTranslator
from openai import OpenAI
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration, AutoProcessor, AutoModelForVision2Seq
import torch
from gtts import gTTS
import tempfile
import os
from yt_dlp import YoutubeDL
import speech_recognition as sr
import urllib.parse
from streamlit_js_eval import streamlit_js_eval

# ------------------------ CONFIG ------------------------
st.set_page_config(page_title="🤖 AI Search Assistant", layout="wide")
st.title("🤖 AI Search Assistant")

# Initialize OpenAI client

OpenAi_KEY = "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"


client = OpenAI(api_key=OpenAi_KEY)

# ------------------------ SESSION STATE ------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_song" not in st.session_state:
    st.session_state.current_song = ""

# ------------------------ SIDEBAR ------------------------
st.sidebar.title("Modules")
module = st.sidebar.radio("Select Module:", ["DATABOT", "Music Player", "Live Navigation"])

# ------------------------ DATABOT ------------------------
if module == "DATABOT":
    st.header("DATABOT")

    target_lang = st.selectbox(
        "Choose output language:",
        ["en", "hi", "mr", "fr", "es", "ja", "zh-CN", "de"],
        format_func=lambda x: {"en": "English","hi": "Hindi","mr": "Marathi",
                              "fr": "French","es": "Spanish","ja": "Japanese",
                              "zh-CN": "Chinese","de": "German"}[x]
    )

    input_mode = st.radio("🎙 Input Mode:", ["Text", "Voice"])
    user_query = ""

    if input_mode == "Text":
        user_query = st.text_input("Ask me anything:")

    if input_mode == "Voice":
        if st.button("🎤 Record Voice"):
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                st.info("🎙 Listening...")
                audio = recognizer.listen(source, phrase_time_limit=15)
            try:
                user_query = recognizer.recognize_google(audio)
                st.success(f"✅ You said: {user_query}")
            except sr.UnknownValueError:
                st.error("Could not understand audio, please try again.")
            except sr.RequestError:
                st.error("😴 Could not connect to the speech recognition service.")

    if user_query:
        with st.spinner("🧐Thinking..."):
            # OpenAI response
            try:
                st.session_state.messages.append({"role": "user", "content": user_query})
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=st.session_state.messages
                )
                answer = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": answer})

                # Translate
                translated_answer = GoogleTranslator(source="auto", target=target_lang).translate(answer) if target_lang != "en" else answer
                st.subheader("✅ Answer")
                st.write(translated_answer)

                # Audio output
                if st.checkbox("🔊 Play Answer as Audio"):
                    tts = gTTS(text=translated_answer, lang=target_lang, slow=False)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                        tts.save(temp_file.name)
                        st.audio(temp_file.name, format="audio/mp3")
            except Exception as e:
                st.error(f"OpenAI API Error: {e}")

# ------------------------ MUSIC PLAYER ------------------------
elif module == "Music Player":
    st.header("🎵 Spotify-Like Music Player")

    # Local music
    music_folder = "music"
    if not os.path.exists(music_folder):
        os.makedirs(music_folder)
    local_songs = [f for f in os.listdir(music_folder) if f.endswith(".mp3")]

    if local_songs:
        song_choice = st.selectbox("Select a local song:", local_songs)
        if st.button("▶ Play Local Song"):
            st.session_state.current_song = song_choice
            st.audio(os.path.join(music_folder, song_choice), format="audio/mp3")
    else:
        st.info("No local songs found in 'music/' folder.")

    # YouTube music
    st.subheader("Search & Play YouTube Music")
    search_mode = st.radio("How do you want to search?", ["Type Song Name", "Voice Command"])
    song_name = ""

    if search_mode == "Type Song Name":
        song_name = st.text_input("Enter song name:")
    elif search_mode == "Voice Command":
        if st.button("🎤 Speak Song Name"):
            r = sr.Recognizer()
            with sr.Microphone() as source:
                st.info("🎤 Listening...")
                audio = r.listen(source, phrase_time_limit=6)
            try:
                song_name = r.recognize_google(audio)
                st.success(f"You said: {song_name}")
            except sr.UnknownValueError:
                st.error("😴 Could not understand your voice, speak again")
            except sr.RequestError:
                st.error("😴 Speech recognition error, try again later")

    if song_name and st.button("▶ Play YouTube Song"):
        try:
            ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'noplaylist': True}
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch:{song_name}", download=False)['entries'][0]
                audio_url = info['url']
            st.session_state.current_song = info['title']
            st.audio(audio_url, format="audio/mp3")
            st.success(f"Now Playing: {st.session_state.current_song}")
        except Exception as e:
            st.error(f"Error: {e}")

# ------------------------ LIVE NAVIGATION ------------------------
elif module == "Live Navigation":
    st.header("Live Navigation (Google Maps)")

    GOOGLE_KEY = st.secrets.get("GOOGLE_MAPS_KEY", "YOUR_KEY_HERE")
    if not GOOGLE_KEY:
        st.error("Add GOOGLE_MAPS_KEY to .streamlit/secrets.toml first.")
        st.stop()

    dest = st.text_input("Destination", placeholder="e.g., anything you want")
    col1, col2 = st.columns([1,1])
    with col1:
        use_gps = st.checkbox("Use my current GPS location", value=True)
    with col2:
        travel_mode = st.selectbox("Mode", ["Driving", "Walking", "Bicycling", "Bike"])

    origin_lat = origin_lng = None
    origin_text = st.text_input("Or manually enter origin (optional)")

    if use_gps:
        loc = streamlit_js_eval(
            js_expressions="""
            await new Promise((resolve) => {
              if (!navigator.geolocation) { resolve(null); return; }
              navigator.geolocation.getCurrentPosition(
                (pos) => resolve({lat: pos.coords.latitude, lng: pos.coords.longitude}),
                () => resolve(null),
                {enableHighAccuracy: true, timeout: 10000, maximumAge: 0}
              );
            });
            """,
            key="get_gps_once",
        )
        if loc and isinstance(loc, dict) and "lat" in loc and "lng" in loc:
            origin_lat, origin_lng = loc["lat"], loc["lng"]
            st.success(f"📍 GPS locked: {origin_lat:.6f}, {origin_lng:.6f}")
        else:
            st.warning("Enable Location services on your device")

    origin_param = ""
    if use_gps and origin_lat is not None and origin_lng is not None:
        origin_param = f"{origin_lat},{origin_lng}"
    elif origin_text.strip():
        origin_param = origin_text.strip()

    if st.button("🚀 Show Directions Map"):
        if not dest.strip():
            st.error("Enter a destination.")
            st.stop()
        dest_enc = urllib.parse.quote_plus(dest.strip())
        mode_enc = urllib.parse.quote_plus(travel_mode)
        if origin_param:
            origin_enc = urllib.parse.quote_plus(origin_param)
            embed_src = f"https://www.google.com/maps/embed/v1/directions?key={GOOGLE_KEY}&origin={origin_enc}&destination={dest_enc}&mode={mode_enc}"
            open_nav = f"https://www.google.com/maps/dir/?api=1&origin={origin_enc}&destination={dest_enc}&travelmode={mode_enc}"
        else:
            embed_src = f"https://www.google.com/maps/embed/v1/directions?key={GOOGLE_KEY}&destination={dest_enc}&mode={mode_enc}"
            open_nav = f"https://www.google.com/maps/dir/?api=1&destination={dest_enc}&travelmode={mode_enc}"
        iframe_html = f"""
            <div style="width:100%;border-radius:16px;overflow:hidden;">
                <iframe width="100%" height="520" frameborder="0" style="border:0"
                referrerpolicy="no-referrer-when-downgrade" src="{embed_src}" allowfullscreen></iframe>
            </div>
            <div style="margin-top:12px;">
                <a href="{open_nav}" target="_blank" style="
                    display:inline-block;padding:10px 16px;border-radius:10px;
                    background:#1a73e8;color:white;text-decoration:none;font-weight:600;">
                    Open in Google Maps (Live Navigation)
                </a>
            </div>
        """
        st.components.v1.html(iframe_html, height=580, scrolling=False)
        st.caption("On mobile, the button opens Google Maps app for turn-by-turn navigation.")