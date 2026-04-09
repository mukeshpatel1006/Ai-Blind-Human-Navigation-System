"""
AGENTIC NAVIGATION - FULLY OFFLINE (WHISPER AI + YOLOv8)
OPTIMIZED FOR BLIND NAVIGATION: Real-time, fast feedback, no wake-word delay.
"""

import cv2, os, time, threading, numpy as np
import win32com.client
from ultralytics import YOLO
import pyaudio
import whisper # 100% OFFLINE SPEECH RECOGNITION
import logging, warnings

# Suppress YOLO & Whisper logs
logging.getLogger("ultralytics").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore")
os.environ["YOLO_VERBOSE"] = "False"

YOLO_MODEL  = "yolov8n.pt" # Nano model for fast CPU speed
CONF        = 0.30
FOCAL       = 520
SCAN_FRAMES = 10 # Reduced for faster scene understanding

stop_event = threading.Event()
det_lock   = threading.Lock()
live_dets  = []

# ══════════════════════════════════════════════════════════════
# VOICE OUTPUT - Windows SAPI5
# ══════════════════════════════════════════════════════════════
print("Initializing Async Voice Engine...")
speaker = win32com.client.Dispatch("SAPI.SpVoice")
speaker.Volume = 100
speaker.Rate = -1 

def say(text, interrupt=False):
    """Speaks text out loud directly to earbuds."""
    if not text or not text.strip():
        return
    print(f"🔊 [VOICE] {text}")
    flag = 3 if interrupt else 1 
    speaker.Speak(text, flag)

# ══════════════════════════════════════════════════════════════
# BOOT AI MODELS
# ══════════════════════════════════════════════════════════════
print("Loading YOLO AI (Vision)...")
yolo = YOLO(YOLO_MODEL, verbose=False)

print("Loading Whisper AI (Offline Listening)...")
# UPGRADED TO tiny.en FOR MASSIVE SPEED INCREASE ON CPU
stt_model = whisper.load_model("tiny.en") 

print("Opening camera...")
cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
if not cam.isOpened():
    raise RuntimeError("Camera not found.")

print("Setting up offline microphone...")
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=16000, 
                input=True,
                frames_per_buffer=4096)
stream.start_stream()

print("System Ready.\n")

# ══════════════════════════════════════════════════════════════
# DISTANCE & CAMERA THREAD 
# ══════════════════════════════════════════════════════════════
OBJ_H = {
    "person":170,"chair":90,"table":75,"door":200,
    "bottle":25,"cup":12,"laptop":30,"cell phone":14,
    "car":150,"bicycle":100,"dog":55,"cat":30,
    "bag":40,"book":25,"tv":60,"sofa":85,"couch":85,
    "bed":60,"backpack":50,"bowl":12,"remote":12,
}
dbuf = {}

def get_dist(label, bh):
    rh = OBJ_H.get(label, 50)
    if bh < 5: return 999
    d  = (rh * FOCAL) / bh
    dbuf.setdefault(label, []).append(d)
    if len(dbuf[label]) > 5: dbuf[label].pop(0)
    return round(float(sum(dbuf[label])/len(dbuf[label])), 1)

def fmt(cm):
    if cm < 100: return f"{int(cm)} centimeters"
    return f"{round(cm/100,1)} meters"

def camera_thread():
    while not stop_event.is_set():
        ok, frame = cam.read()
        if not ok:
            time.sleep(0.05)
            continue

        H, W, _ = frame.shape
        res  = yolo.track(frame, persist=True, verbose=False, conf=CONF)
        dets = []

        for r in res:
            for box in r.boxes:
                lbl         = yolo.names[int(box.cls)]
                x1,y1,x2,y2 = box.xyxy[0]
                bx = int((x1+x2)/2)
                by = int((y1+y2)/2)
                bh = float(y2-y1)
                dc = get_dist(lbl, bh)

                if   bx < W*0.35: hd = "left"
                elif bx > W*0.65: hd = "right"
                else:             hd = "center"

                if   by < H*0.33: vd = "upper"
                elif by > H*0.66: vd = "lower"
                else:             vd = "middle"

                dets.append({"label":lbl,"hd":hd,"vd":vd,"dist":dc})

                col = (0,255,80) if hd=="center" else (255,180,0)
                cv2.rectangle(frame,(int(x1),int(y1)),(int(x2),int(y2)),col,2)
                cv2.putText(frame, f"{lbl} {int(dc)}cm", (int(x1), max(int(y1)-6,12)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 2)

        with det_lock:
            live_dets.clear()
            live_dets.extend(dets)

        cv2.imshow("Agentic Navigation", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            stop_event.set()
            break

    cam.release()
    cv2.destroyAllWindows()

def get_scene():
    tally = {}
    for _ in range(SCAN_FRAMES):
        time.sleep(0.03) # Faster scan
        with det_lock:
            snap = list(live_dets)
        for d in snap:
            k = f"{d['label']}_{d['hd']}_{d['vd']}"
            tally.setdefault(k, {**d,"n":0})["n"] += 1
    stable = [v for v in tally.values() if v["n"] >= SCAN_FRAMES*0.25]
    stable.sort(key=lambda x: x["dist"])
    return stable

def continuous_navigation(target):
    say(f"Navigating to {target}. Walk forward slowly.", interrupt=True)
    search_attempts = 0
    
    while not stop_event.is_set():
        objs = get_scene()
        target_objs = [o for o in objs if o["label"] == target]
        
        if not target_objs:
            search_attempts += 1
            if search_attempts > 3:
                say(f"Lost the {target}. Stop and turn slowly to scan.", interrupt=True)
                search_attempts = 0 
            time.sleep(1.0)
            continue
            
        search_attempts = 0
        best_target = target_objs[0] 
        dist = best_target["dist"]
        hd = best_target["hd"]
        
        # Check if we arrived
        if dist < 65:
            say(f"Stop. The {target} is right in front of you.", interrupt=True)
            time.sleep(2)
            say("Awaiting next command.")
            return 
            
        # FAST REAL-TIME FEEDBACK
        if hd == "left":
            say(f"Slight left. {fmt(dist)}.", interrupt=True)
        elif hd == "right":
            say(f"Slight right. {fmt(dist)}.", interrupt=True)
        else:
            say(f"Straight ahead. {fmt(dist)}.")
            
        # Drastically reduced sleep so the blind user gets constant updates
        time.sleep(1.5) 

# ══════════════════════════════════════════════════════════════
# FAST OFFLINE LISTENING & INTENT
# ══════════════════════════════════════════════════════════════
def listen():
    audio_frames = []
    is_recording = False
    silence_frames = 0
    
    stream.stop_stream()
    time.sleep(0.05) 
    stream.start_stream()

    while not stop_event.is_set():
        try:
            data = stream.read(4096, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
            rms = np.sqrt(np.mean(np.square(audio_data, dtype=np.float32)))
            
            # Volume gate
            if rms > 450:  
                is_recording = True
                silence_frames = 0
                audio_frames.append(audio_data)
            elif is_recording:
                silence_frames += 1
                audio_frames.append(audio_data)
                
                # Cut off quickly when user stops speaking (8 frames instead of 15)
                if silence_frames > 8: 
                    break 
        except Exception:
            continue

    if not audio_frames:
        return ""

    audio_np = np.concatenate(audio_frames).astype(np.float32) / 32768.0
    
    # Force English for faster processing
    result = stt_model.transcribe(audio_np, fp16=False, language="en") 
    text = result["text"].strip().lower()

    if text in ["thank you.", "thanks for watching.", "you", "thanks.", ""]:
        return ""
        
    return text

def interpret_goal(query):
    query = query.lower()
    
    if any(w in query for w in ["what", "see", "around", "kya", "dikh", "batao"]): 
        return None, "Describe"
    if any(w in query for w in ["door", "darwaza", "exit", "leave", "bahar"]): 
        return "door", "Navigation"
    if any(w in query for w in ["sit", "chair", "kursi", "sofa", "baith"]): 
        return "chair", "Navigation"
    if any(w in query for w in ["bed", "bistar", "palang", "sleep", "sona"]): 
        return "bed", "Navigation"
    if any(w in query for w in ["table", "desk", "mez"]): 
        return "dining table", "Navigation"
    if any(w in query for w in ["water", "pani", "bottle", "drink", "pyas"]): 
        return "bottle", "Navigation"
    if any(w in query for w in ["cup", "glass", "mug", "chai", "coffee"]): 
        return "cup", "Navigation"
    if any(w in query for w in ["person", "human", "insaan", "aadmi", "aurat"]): 
        return "person", "Navigation"
        
    for lbl in list(yolo.names.values()):
        if lbl in query: return lbl, "Navigation"
        
    return None, "Unknown"

# ══════════════════════════════════════════════════════════════
# MAIN ROUTINE
# ══════════════════════════════════════════════════════════════
def main():
    say("System offline. Tell me what you want to find.")

    while not stop_event.is_set():
        raw = listen()
        if not raw: continue
        print(f"🎤 [HEARD]: {raw}")
        
        if any(w in raw for w in ["shut down", "exit system"]):
            say("Shutting down completely.", interrupt=True)
            stop_event.set()
            break

        if any(w in raw for w in ["stop", "ruko", "ruk jao", "cancel"]):
            say("Navigation cancelled. Standing by.", interrupt=True)
            continue

        target, action = interpret_goal(raw)

        if action == "Describe":
            say("Scanning.", interrupt=True)
            objs = get_scene()
            if not objs:
                say("The path is clear.")
            else:
                o = objs[0] 
                say(f"Closest object is a {o['label']}, {fmt(o['dist'])} away, slightly to your {o['hd']}.")
                
        elif action == "Navigation" and target:
            continuous_navigation(target)
            
        else:
            # Removed the "I did not understand" voice prompt so it doesn't 
            # spam the user if it accidentally hears background noise.
            pass

# ══════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    threading.Thread(target=camera_thread, daemon=True, name="CAM").start()
    
    try:
        time.sleep(2.0) 
        main()
    except KeyboardInterrupt:
        print("\n🛑 [SYSTEM] Force quit (Ctrl+C) detected. Shutting down safely...")
    finally:
        stop_event.set()
        # Wrapping the final sleep in a try-except so it doesn't print an error
        # if you press Ctrl+C multiple times.
        try:
            time.sleep(0.5) 
        except KeyboardInterrupt:
            pass
        print("System offline.")