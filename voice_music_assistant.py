import streamlit as st
from yt_dlp import YoutubeDL
import os
import speech_recognition as sr

st.set_page_config(page_title="🎵 Spotify-Like Music Player", layout="wide")
st.title("🎵 Spotify-Like Music Player")

# ----------------- LOCAL MUSIC -----------------
st.header("Local Music")
music_folder = "music"
local_songs = [f for f in os.listdir(music_folder) if f.endswith(".mp3")] if os.path.exists(music_folder) else []

if local_songs:
    song_choice = st.selectbox("Select a local song:", local_songs)
    if st.button("▶ Play Local Song"):
        st.audio(os.path.join(music_folder, song_choice), format="audio/mp3")
else:
    st.info("No local songs found in 'music/' folder.")

# ----------------- YOUTUBE SEARCH -----------------
st.header("Search & Play YouTube Music")
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
            st.error("Could not understand your voice")
        except sr.RequestError:
            st.error("Speech recognition service error")

# Play from YouTube
if song_name and st.button("▶ Play YouTube Song"):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'noplaylist': True
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{song_name}", download=False)['entries'][0]
            audio_url = info['url']
        st.audio(audio_url, format="audio/mp3")
        st.success(f"Now Playing: {info['title']}")
    except Exception as e:
        st.error(f"Error: {e}")