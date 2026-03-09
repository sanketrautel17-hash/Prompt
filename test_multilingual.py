# -*- coding: utf-8 -*-
"""
test_multilingual.py
--------------------
Tests the VoicePrompt AI pipeline with Hindi and Marathi audio.
Uses gTTS (Google Text-to-Speech) to generate synthetic speech files,
then uploads them to the /voice/process endpoint.
"""
import os
import sys
import httpx
from gtts import gTTS

BASE_URL = "http://127.0.0.1:8000"

# Hindi test: "Write a python function that connects to a REST API"
# Hindi translation of intent keywords (coding -> 'python', 'function')
HINDI_TEXT = "मुझे एक पाइथन फंक्शन चाहिए जो रेस्ट एपीआई से कनेक्ट हो और जेसन डेटा लाए"

# Marathi test: "Draft an email to my boss about the new project proposal"
# Marathi translation of intent keywords (writing -> 'email', 'proposal') 
MARATHI_TEXT = "माझ्या बॉसला नवीन प्रोजेक्ट प्रपोजल बद्दल एक ईमेल ड्राफ्ट कर"

def test_language(lang_code: str, tts_lang: str, text: str, name: str):
    print(f"\n===========================================")
    print(f"  Testing {name} ({lang_code})")
    print(f"===========================================")
    print(f"Input text: {text}")
    
    mp3_file = f"test_{lang_code}.mp3"
    
    print("1. Generating synthesized speech using gTTS...")
    try:
        tts = gTTS(text=text, lang=tts_lang)
        tts.save(mp3_file)
        print(f"   -> Saved to {mp3_file} ({os.path.getsize(mp3_file)} bytes)")
    except Exception as e:
        print(f"   [FAIL] Could not generate TTS: {e}")
        return False
        
    print("\n2. Calling /voice/process pipeline...")
    try:
        with open(mp3_file, "rb") as f:
            audio_bytes = f.read()
            
        r = httpx.post(
            f"{BASE_URL}/voice/process",
            files={"file": (mp3_file, audio_bytes, "audio/mp3")},
            data={"language": lang_code},
            timeout=60.0
        )
    except Exception as e:
        print(f"   [FAIL] Request failed: {e}")
        return False
        
    print(f"3. Response status: {r.status_code}")
    if r.status_code == 200:
        resp = r.json()
        print(f"   OK  id         : {resp.get('id')}")
        print(f"   OK  transcript : {repr(resp.get('transcript'))}")
        print(f"   OK  intent     : {resp.get('intent')}")
        print(f"   OK  framework  : {resp.get('framework')}")
        print(f"   OK  prompt_len : {len(resp.get('generated_prompt', ''))} chars")
        print(f"   OK  elapsed_ms : {resp.get('processing_time_ms')} ms")
        
        print("\n------- Generated Prompt (first 300 chars) -------")
        prompt_text = resp.get("generated_prompt", "")
        print(prompt_text[:300] + ("..." if len(prompt_text) > 300 else ""))
        print("--------------------------------------------------\n")
        print(f"   [PASS] {name} test successful!")
        return True
    elif r.status_code == 422:
        print(f"   [WARN] Deepgram couldn't transcribe the synthesized audio. This happens sometimes with robot voices.")
        print(r.json())
        return False
    else:
        print(f"   [FAIL] Error {r.status_code}: {r.text}")
        return False

def run_tests():
    print("VoicePrompt AI - Phase 5 Multilingual tests\n")
    
    # Run Hindi
    hi_pass = test_language(lang_code="hi", tts_lang="hi", text=HINDI_TEXT, name="Hindi")
    
    # Run Marathi
    mr_pass = test_language(lang_code="mr", tts_lang="mr", text=MARATHI_TEXT, name="Marathi")
    
    print("\n===========================================")
    if hi_pass and mr_pass:
        print("  ALL MULTILINGUAL TESTS PASSED!")
    else:
        print("  SOME TESTS FAILED/WARN - Check output.")
        
    # Cleanup
    if os.path.exists("test_hi.mp3"): os.remove("test_hi.mp3")
    if os.path.exists("test_mr.mp3"): os.remove("test_mr.mp3")

if __name__ == "__main__":
    run_tests()
