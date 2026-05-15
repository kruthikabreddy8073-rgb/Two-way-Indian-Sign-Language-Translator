import tkinter as tk
from tkinter import simpledialog, messagebox
import cv2
import os
import time
import glob

# Updated dict: map input words to local image directories (match Image/ folders)
word_to_dir = {
    "BIG": "Image/Big",
    "CINEMA": "Image/Cinema",
    "COFFEE": "Image/Coffee",
    # Add more matching Image/ dirs as needed, e.g.
    "HELLO": "Image/Hello",
    "THANK YOU": "Image/Thank you",
    "SORRY": "Image/Sorry",
    "PLEASE": "Image/Please",
    # ... full list from actions in function.py
    "DEFAULT": "Image/Neutral"  # fallback
}

def play_local_slideshow(image_dir, word):
    image_paths = sorted(glob.glob(os.path.join(image_dir, "*.png")) + glob.glob(os.path.join(image_dir, "*.jpg")))
    if not image_paths:
        messagebox.showerror("Error", f"No images in {image_dir}")
        return
    
    cap_time = time.time()
    frame_idx = 0
    while time.time() - cap_time < 5:  # 5s slideshow
        frame = cv2.imread(image_paths[frame_idx % len(image_paths)])
        if frame is None:
            break
        
        h, w = frame.shape[:2]
        # Overlay word (scale to fit)
        cv2.putText(frame, word, (50, 50), cv2.FONT_HERSHEY_TRIPLEX, 1.2, (0, 0, 0), 3)
        cv2.putText(frame, word, (52, 52), cv2.FONT_HERSHEY_TRIPLEX, 1.2, (255, 255, 255), 2)
        
        cv2.imshow("Sign Language Video", frame)
        if cv2.waitKey(100) & 0xFF == ord('q'):  # 10fps
            break
        
        frame_idx += 1
    
    cv2.destroyAllWindows()

def display_video():
    user_input = simpledialog.askstring("Input", "Enter a word (e.g. BIG, HELLO):")
    if user_input is None:
        return
    user_input = user_input.upper()
    if not user_input:
        return
    
    image_dir = word_to_dir.get(user_input, word_to_dir["DEFAULT"])
    play_local_slideshow(image_dir, user_input)

def main():
    root = tk.Tk()
    root.withdraw()
    try:
        display_video()
    except tk.TclError:
        pass
    finally:
        root.destroy()

if __name__ == "__main__":
    main()

