import os
import time
import datetime
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import numpy as np
import cv2
from pynput import keyboard
from PIL import ImageGrab
import pyaudio
import wave
import subprocess
import tempfile

class HalfRecorder:
    def __init__(self, root):
        self.root = root
        self.root.title("HalfRecorder")
        self.root.geometry("400x340")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f0f0")
        
        # Variables
        self.recording = False
        self.output_path = os.path.join(os.path.expanduser("~"), "Videos", "HalfRecorder")
        self.video_writer = None
        self.recording_thread = None
        self.audio_thread = None
        self.fps = 20
        self.countdown = 0
        
        # Audio settings
        self.audio_format = pyaudio.paInt16
        self.channels = 2
        self.sample_rate = 44100
        self.chunk = 1024
        self.audio_frames = []
        self.audio = pyaudio.PyAudio()
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)
        
        # Initialize keyboard listener
        self.keyboard_listener = keyboard.GlobalHotKeys({
            '<alt>+<f10>': self.toggle_recording
        })
        self.keyboard_listener.start()
        
        self.create_widgets()
    
    def create_widgets(self):
        # Main frame
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(
            main_frame, 
            text="HalfRecorder",
            font=("Arial", 20, "bold"),
            bg="#f0f0f0",
            fg="#333333"
        )
        title_label.pack(pady=(0, 20))
        
        # Status frame
        status_frame = tk.Frame(main_frame, bg="#f0f0f0")
        status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = tk.Label(
            status_frame,
            text="Status: Ready",
            font=("Arial", 12),
            bg="#f0f0f0"
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Audio option
        audio_frame = tk.Frame(main_frame, bg="#f0f0f0")
        audio_frame.pack(fill=tk.X, pady=5)
        
        self.audio_var = tk.BooleanVar()
        self.audio_var.set(True)
        
        audio_check = tk.Checkbutton(
            audio_frame,
            text="Record Audio",
            variable=self.audio_var,
            bg="#f0f0f0",
            font=("Arial", 10)
        )
        audio_check.pack(side=tk.LEFT)
        
        # Record button
        self.record_button = tk.Button(
            main_frame,
            text="Start Recording",
            command=self.toggle_recording,
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white",
            activebackground="#45a049",
            activeforeground="white",
            relief=tk.FLAT,
            width=15,
            height=2
        )
        self.record_button.pack(pady=15)
        
        # Shortcut info
        shortcut_frame = tk.Frame(main_frame, bg="#f0f0f0")
        shortcut_frame.pack(fill=tk.X, pady=5)
        
        shortcut_label = tk.Label(
            shortcut_frame,
            text="Keyboard Shortcut: Alt + F10",
            font=("Arial", 10),
            bg="#f0f0f0"
        )
        shortcut_label.pack()
        
        # Recordings path info
        path_frame = tk.Frame(main_frame, bg="#f0f0f0")
        path_frame.pack(fill=tk.X, pady=5)
        
        path_label = tk.Label(
            path_frame,
            text=f"Recordings saved to: {self.output_path}",
            font=("Arial", 9),
            bg="#f0f0f0",
            fg="#666666"
        )
        path_label.pack()
        
        # Footer
        footer_frame = tk.Frame(main_frame, bg="#f0f0f0")
        footer_frame.pack(fill=tk.X, pady=(20, 0))
        
        version_label = tk.Label(
            footer_frame,
            text="v1.1.0",
            font=("Arial", 8),
            bg="#f0f0f0",
            fg="#999999"
        )
        version_label.pack(side=tk.RIGHT)
    
    def toggle_recording(self):
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def start_recording(self):
        if self.recording:
            return
        
        self.recording = True
        self.record_button.config(text="Stop Recording", bg="#f44336", activebackground="#e53935")
        self.status_label.config(text="Status: Recording...")
        
        self.recording_thread = threading.Thread(target=self.record_screen)
        self.recording_thread.daemon = True
        
        if self.audio_var.get():
            self.audio_thread = threading.Thread(target=self.record_audio)
            self.audio_thread.daemon = True
            self.audio_thread.start()
        
        self.recording_thread.start()
    
    def stop_recording(self):
        if not self.recording:
            return
        
        self.recording = False
        self.record_button.config(text="Start Recording", bg="#4CAF50", activebackground="#45a049")
        self.status_label.config(text="Status: Processing...")
        
        if self.recording_thread:
            self.recording_thread.join()
            self.recording_thread = None
        
        if self.audio_thread and self.audio_var.get():
            self.audio_thread.join()
            self.audio_thread = None
            
        self.status_label.config(text="Status: Ready")
    
    def get_screen_size(self):
        # Get screen size using PIL
        img = ImageGrab.grab()
        return img.size
    
    def record_audio(self):
        try:
            # Start audio stream
            audio_stream = self.audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            self.audio_frames = []
            
            # Record audio while recording flag is True
            while self.recording:
                data = audio_stream.read(self.chunk)
                self.audio_frames.append(data)
            
            # Stop and close the audio stream
            audio_stream.stop_stream()
            audio_stream.close()
            
        except Exception as e:
            messagebox.showerror("Error", f"Audio recording failed: {str(e)}")
    
    def save_audio(self, audio_file):
        # Save recorded audio to a WAV file
        try:
            wf = wave.open(audio_file, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.audio_format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.audio_frames))
            wf.close()
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save audio: {str(e)}")
            return False
    
    def merge_audio_video(self, video_file, audio_file, output_file):
        try:
            # Use ffmpeg to merge audio and video
            command = [
                'ffmpeg',
                '-i', video_file,
                '-i', audio_file,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-strict', 'experimental',
                output_file
            ]
            
            subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Remove temporary files
            os.remove(video_file)
            os.remove(audio_file)
            
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to merge audio and video: {str(e)}")
            return False
    
    def record_screen(self):
        try:
            # Countdown before recording
            for i in range(3, 0, -1):
                self.status_label.config(text=f"Status: Starting in {i}...")
                time.sleep(1)
            
            # Generate file name with timestamp
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            # If recording audio, use temp files then merge
            if self.audio_var.get():
                temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False).name
                temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
                final_output = os.path.join(self.output_path, f"recording_{timestamp}.mp4")
                video_path = temp_video
            else:
                video_path = os.path.join(self.output_path, f"recording_{timestamp}.mp4")
            
            # Get screen size using PIL
            screen_width, screen_height = self.get_screen_size()
            
            # Define the codec and create VideoWriter object
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(
                video_path, 
                fourcc, 
                self.fps, 
                (screen_width, screen_height)
            )
            
            self.status_label.config(text="Status: Recording...")
            
            # Record frames while recording flag is True
            start_time = time.time()
            frame_count = 0
            
            while self.recording:
                # Take screenshot using PIL
                screenshot = ImageGrab.grab()
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Write the frame
                self.video_writer.write(frame)
                
                # Calculate actual FPS and sleep to maintain target FPS
                frame_count += 1
                elapsed = time.time() - start_time
                sleep_time = max(0, (frame_count / self.fps) - elapsed)
                time.sleep(sleep_time)
            
            # Release resources
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
            
            # If audio was recorded, merge audio and video
            if self.audio_var.get() and len(self.audio_frames) > 0:
                self.status_label.config(text="Status: Processing audio...")
                if self.save_audio(temp_audio):
                    self.status_label.config(text="Status: Merging audio and video...")
                    if self.merge_audio_video(temp_video, temp_audio, final_output):
                        messagebox.showinfo("HalfRecorder", f"Recording with audio saved to:\n{final_output}")
                    else:
                        messagebox.showinfo("HalfRecorder", f"Video saved without audio to:\n{video_path}")
            else:
                messagebox.showinfo("HalfRecorder", f"Recording saved to:\n{video_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Recording failed: {str(e)}")
            self.recording = False
            self.record_button.config(text="Start Recording", bg="#4CAF50", activebackground="#45a049")
            self.status_label.config(text="Status: Ready")
    
    def on_closing(self):
        if self.recording:
            if messagebox.askyesno("Exit", "Recording in progress. Stop and exit?"):
                self.stop_recording()
                self.root.destroy()
        else:
            self.root.destroy()
        
        # Clean up audio
        self.audio.terminate()
        
        # Stop keyboard listener
        self.keyboard_listener.stop()

if __name__ == "__main__":
    root = tk.Tk()
    app = HalfRecorder(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()