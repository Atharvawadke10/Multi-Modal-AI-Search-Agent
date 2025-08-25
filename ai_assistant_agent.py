import streamlit as st
from deep_translator import GoogleTranslator
from openai import OpenAI
import speech_recognition as sr
from gtts import gTTS
import tempfile
import os

# Initialize OpenAI client
client = OpenAI(api_key="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")

st.set_page_config(page_title="🌍 Multilingual AI Assistant", layout="centered")
st.title("🌍 Multilingual AI Assistant")

# Select target language
target_lang = st.selectbox(
    "Choose output language:",
    ["en", "hi", "mr", "fr", "es", "ja", "zh-CN", "de"],  # Language codes
    format_func=lambda x: {
        "en": "English", "hi": "Hindi", "mr": "Marathi",
        "fr": "French", "es": "Spanish", "ja": "Japanese",
        "zh-CN": "Chinese", "de": "German"
    }[x]
)

# Option to choose input mode
input_mode = st.radio("🎙 Select Input Mode:", ["Text", "Voice"])

user_query = ""

# --- TEXT INPUT ---
if input_mode == "Text":
    user_query = st.text_input("Ask me anything:")

# --- VOICE INPUT ---
if input_mode == "Voice":
    if st.button("🎤 Record Voice"):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("🎙 Listening... Speak now.")
            audio = recognizer.listen(source, phrase_time_limit=15)

        try:
            user_query = recognizer.recognize_google(audio)
            st.success(f"✅ You said: {user_query}")
        except sr.UnknownValueError:
            st.error("❌ Could not understand audio.")
        except sr.RequestError:
            st.error("⚠ Could not request results from Google STT service.")

if user_query:
    with st.spinner("🤔 Thinking..."):
        # Step 1: Get AI response in English
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": user_query}]
        )
        english_answer = response.choices[0].message.content

        # Step 2: Translate output
        translated_answer = GoogleTranslator(source="auto", target=target_lang).translate(english_answer)

    # Display results
    st.subheader("✅ Answer")
    st.write(translated_answer)

    # --- AUDIO OUTPUT OPTION ---
    if st.checkbox("🔊 Play Answer as Audio"):
        try:
            # Generate speech
            tts = gTTS(text=translated_answer, lang=target_lang, slow=False)

            # Save properly in a temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                tts.save(temp_file.name)
                st.audio(temp_file.name, format="audio/mp3")

        except Exception as e:
            st.error(f"⚠ Error generating audio: {e}")