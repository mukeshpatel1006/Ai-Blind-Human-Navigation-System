# Ai-Blind-Human-Navigation-System

# 👁️ Agentic Navigation Assistant for the Visually Impaired

An end-to-end, 100% voice-operated AI navigation system designed to help visually impaired individuals understand their surroundings, find specific objects, and navigate safely using real-time computer vision and Large Language Models (LLMs).

## ✨ Key Features

* **🎙️ 100% Voice Operated:** Completely headless design. No text output or terminal reading required. Relies entirely on microphone input and speaker output.
* **👁️ Real-Time Computer Vision:** Powered by **YOLOv8** to instantly detect objects, calculate their distances, and determine their exact spatial orientation (left, right, center, upper, lower).
* **🧠 LLM-Powered Guidance:** Uses the **Groq API (Llama 3)** to translate complex visual data into natural, step-by-step spoken navigation commands (e.g., *"Turn left, walk 2 metres, the bottle is on your right"*).
* **🌐 Bilingual Support:** Understands voice commands and queries in both English and Hindi.
* **🛑 Automatic Obstacle Warnings:** Continuously monitors the path ahead and automatically interrupts to warn the user if a hazardous obstacle (e.g., person, chair, car) is too close.
* **🔌 Offline Fallback:** Includes local logic to ensure basic distance calculations, object finding, and safety warnings still work even if the internet or LLM API goes down.

## 🛠️ Technology Stack

* **Python 3.x**
* **Computer Vision:** OpenCV, Ultralytics YOLOv8
* **AI / LLM:** Groq API (`llama3-8b-8192`)
* **Voice Interface:** `SpeechRecognition` (Input), `pyttsx3` (Output)

* Output : <img width="1920" height="1080" alt="Screenshot 2026-03-22 072853" src="https://github.com/user-attachments/assets/cbabd052-3a96-496c-81ad-919f53cedd56" />
