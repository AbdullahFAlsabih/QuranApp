# QuranApp

The application is for Quran memorization at the verse level.
Programming language python 
UI framework flet


it combines File I/O, JSON, GUI, Microphone, Speech Recognition, Text Processing, and Threading 

the libraries has been used :
import JSON
import OS
import threding
import speech_recognition as sr
import flet as ft

Activate the virtual environment:

Linux / macOS
source .venv/bin/activate
Windows
.venv\Scripts\activate

Install the required packages:

pip install -r requirements.txt
Running the Application

Run:

python app.py

The Flet application should start and display the Quran memorization interface.

How It Works

The application follows this general flow:

                 quran.json
                     │
                     ▼
              Load Quran Data
                     │
                     ▼
                Flet UI
                     │
          ┌──────────┼──────────┐
          │          │          │
          ▼          ▼          ▼
       Read       Hide/Show   Memorized
       Verse        Verse       Status
          │
          ▼
      Recitation
          │
          ▼
      Microphone
          │
          ▼
  Speech Recognition
          │
          ▼
    Arabic Text
          │
          ▼
  Arabic Normalization
          │
          ▼
      Text Comparison
          │
      ┌───┴────┐
      ▼        ▼
   Match    No Match
      │        │
      ▼        ▼
   Saved     Warning
Arabic Text Normalization
