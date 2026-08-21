'''Desktop GUI version of the drowsiness/yawn detector, built with Tkinter.
Wraps the same EAR/MAR detection logic in a window with Start/Stop controls,
a live video feed, and live threshold readouts.'''

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import numpy as np
from scipy.spatial import distance
from imutils import face_utils
import dlib
import winsound

# ---------- Detection settings (same as drowsiness_detect.py) ----------
EYE_ASPECT_RATIO_THRESHOLD = 0.3
EYE_ASPECT_RATIO_CONSEC_FRAMES = 50
MOUTH_ASPECT_RATIO_THRESHOLD = 0.6
MOUTH_ASPECT_RATIO_CONSEC_FRAMES = 15
ALERT_SOUND = 'audio/alert.wav'
FACE_CASCADE_PATH = 'haarcascades/haarcascade_frontalface_default.xml'
PREDICTOR_PATH = 'shape_predictor_68_face_landmarks.dat'


def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    return (A + B) / (2 * C)


def mouth_aspect_ratio(mouth):
    A = distance.euclidean(mouth[13], mouth[19])
    B = distance.euclidean(mouth[14], mouth[18])
    C = distance.euclidean(mouth[15], mouth[17])
    D = distance.euclidean(mouth[12], mouth[16])
    return (A + B + C) / (3 * D)


class DrowsinessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Driver Drowsiness Detector")
        self.root.geometry("760x680")
        self.root.resizable(False, False)

        # ---------- State ----------
        self.running = False
        self.video_capture = None
        self.counter = 0
        self.yawn_counter = 0
        self.is_alarm_playing = False

        # ---------- Load models once at startup ----------
        self.face_cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(PREDICTOR_PATH)
        (self.lStart, self.lEnd) = face_utils.FACIAL_LANDMARKS_IDXS['left_eye']
        (self.rStart, self.rEnd) = face_utils.FACIAL_LANDMARKS_IDXS['right_eye']
        (self.mStart, self.mEnd) = face_utils.FACIAL_LANDMARKS_IDXS['mouth']

        # ---------- UI layout ----------
        title = tk.Label(root, text="Driver Drowsiness Detector",
                          font=("Segoe UI", 16, "bold"))
        title.pack(pady=(10, 5))

        self.video_label = tk.Label(root, bg="black")
        self.video_label.pack(pady=5)

        # Give the label a real blank image up front so it reserves proper
        # pixel space (700x480) from the start, instead of Tkinter treating
        # width/height as text-character units before any image is set.
        blank = Image.new("RGB", (700, 480), color="black")
        self._blank_imgtk = ImageTk.PhotoImage(blank)
        self.video_label.config(image=self._blank_imgtk)

        stats_frame = tk.Frame(root)
        stats_frame.pack(pady=5)

        self.ear_label = tk.Label(stats_frame, text="EAR: --", font=("Segoe UI", 12), width=20)
        self.ear_label.grid(row=0, column=0, padx=10)

        self.mar_label = tk.Label(stats_frame, text="MAR: --", font=("Segoe UI", 12), width=20)
        self.mar_label.grid(row=0, column=1, padx=10)

        self.status_label = tk.Label(root, text="Status: Stopped", font=("Segoe UI", 13, "bold"),
                                      fg="gray")
        self.status_label.pack(pady=5)

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        self.start_btn = ttk.Button(btn_frame, text="Start", command=self.start)
        self.start_btn.grid(row=0, column=0, padx=10)

        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self.stop, state="disabled")
        self.stop_btn.grid(row=0, column=1, padx=10)

        # Clean shutdown if window is closed while running
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- Controls ----------
    def start(self):
        if self.running:
            return
        self.video_capture = cv2.VideoCapture(0)
        if not self.video_capture.isOpened():
            self.status_label.config(text="Status: Could not open webcam", fg="red")
            return
        self.running = True
        self.counter = 0
        self.yawn_counter = 0
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_label.config(text="Status: Running", fg="green")
        self.update_frame()

    def stop(self):
        self.running = False
        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None
        self._stop_alarm()
        self.video_label.config(image=self._blank_imgtk)
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_label.config(text="Status: Stopped", fg="gray")

    def on_close(self):
        self.stop()
        self.root.destroy()

    def _play_alarm(self):
        if not self.is_alarm_playing:
            winsound.PlaySound(ALERT_SOUND, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
            self.is_alarm_playing = True

    def _stop_alarm(self):
        if self.is_alarm_playing:
            winsound.PlaySound(None, winsound.SND_PURGE)
            self.is_alarm_playing = False

    # ---------- Main detection loop, driven by Tkinter's event loop ----------
    def update_frame(self):
        if not self.running:
            return

        ret, frame = self.video_capture.read()
        if not ret:
            self.root.after(10, self.update_frame)
            return

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Draw face rectangle (cosmetic, haarcascade)
        for (x, y, w, h) in self.face_cascade.detectMultiScale(gray, 1.3, 5):
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        alarm_triggered = False
        ear_display, mar_display = None, None

        for face in self.detector(gray, 0):
            shape = self.predictor(gray, face)
            shape = face_utils.shape_to_np(shape)

            leftEye = shape[self.lStart:self.lEnd]
            rightEye = shape[self.rStart:self.rEnd]
            mouth = shape[self.mStart:self.mEnd]

            ear = (eye_aspect_ratio(leftEye) + eye_aspect_ratio(rightEye)) / 2
            mar = mouth_aspect_ratio(mouth)
            ear_display, mar_display = ear, mar

            for hull in (cv2.convexHull(leftEye), cv2.convexHull(rightEye)):
                cv2.drawContours(frame, [hull], -1, (0, 255, 0), 1)
            cv2.drawContours(frame, [cv2.convexHull(mouth)], -1, (0, 255, 255), 1)

            if ear < EYE_ASPECT_RATIO_THRESHOLD:
                self.counter += 1
                if self.counter >= EYE_ASPECT_RATIO_CONSEC_FRAMES:
                    alarm_triggered = True
                    cv2.putText(frame, "You are Drowsy", (150, 200),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 2)
            else:
                self.counter = 0

            if mar > MOUTH_ASPECT_RATIO_THRESHOLD:
                self.yawn_counter += 1
                if self.yawn_counter >= MOUTH_ASPECT_RATIO_CONSEC_FRAMES:
                    alarm_triggered = True
                    cv2.putText(frame, "You are Yawning", (150, 250),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 2)
            else:
                self.yawn_counter = 0

        if alarm_triggered:
            self._play_alarm()
        else:
            self._stop_alarm()

        # Update EAR/MAR labels
        self.ear_label.config(text="EAR: {:.2f}".format(ear_display) if ear_display else "EAR: --")
        self.mar_label.config(text="MAR: {:.2f}".format(mar_display) if mar_display else "MAR: --")

        # Convert frame (BGR->RGB) and push into the Tkinter label
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb).resize((700, 480))
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.imgtk = imgtk  # keep a reference, or it gets garbage collected
        self.video_label.config(image=imgtk)

        self.root.after(15, self.update_frame)


if __name__ == "__main__":
    root = tk.Tk()
    app = DrowsinessApp(root)
    root.mainloop()
