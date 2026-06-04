#!/usr/bin/env python3
"""
ROI Bounding Box Tool for WhisperX SceneDetect
Allows users to draw resizable bounding boxes on video frames to identify ROI coordinates.
Features: Video scrubbing, frame navigation, multi-file support with filename-grouped JSON export
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import yaml
import argparse
import sys
from pathlib import Path
from typing import Optional, Tuple, Dict
import json
import traceback

class ROITool:
    def __init__(self, config_path: Optional[str] = None, video_path: Optional[str] = None):
        """Initialize the ROI tool."""
        self.config_path = Path(config_path) if config_path else Path(__file__).parent / "roi_config.yaml"
        self.load_config()

        if video_path:
            self.config['video_path'] = video_path

        self.root = tk.Tk()
        self.root.title(self.config['window']['title'])
        self.root.geometry(f"{self.config['window']['width']}x{self.config['window']['height']}")

        self.video_path = None
        self.current_video_filename = None
        self.cap = None
        self.current_frame = None
        self.frame_width = 0
        self.frame_height = 0
        self.total_frames = 0
        self.current_frame_num = 0
        self.fps = 30.0

        self.roi_box = None
        self.drawing = False
        self.start_point = None
        self.roi_history: Dict[int, Tuple[int, int, int, int]] = {}
        self.all_roi_data: Dict[str, Dict[int, Tuple[int, int, int, int]]] = {}

        self.zoom = float(self.config['display']['zoom'])
        self.pan_x = 0
        self.pan_y = 0

        self.is_playing = False
        self.play_speed = 1.0
        self.slider_updating = False
        self.photo_image = None

        self.setup_ui()
        self.bind_keyboard()
        self.load_roi_data_from_file()

        if self.config.get('video_path'):
            self.load_video(self.config['video_path'])

    def load_config(self):
        """Load configuration from YAML."""
        if not self.config_path.exists():
            messagebox.showerror("Error", f"Config file not found: {self.config_path}")
            sys.exit(1)

        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f) or {}

        self.config.setdefault('window', {})
        self.config['window'].setdefault('width', 1600)
        self.config['window'].setdefault('height', 900)
        self.config['window'].setdefault('title', 'ROI Bounding Box Tool - WhisperX SceneDetect')

        self.config.setdefault('display', {})
        self.config['display'].setdefault('zoom', 1.0)

        self.config.setdefault('output', {})
        self.config['output'].setdefault('output_file', 'roi_history.json')

    def load_roi_data_from_file(self):
        """Load existing ROI data from JSON file."""
        try:
            output_file = Path(__file__).parent / self.config['output']['output_file']
            if output_file.exists():
                with open(output_file, 'r') as f:
                    data = json.load(f)

                    if data and self._is_old_format(data):
                        generic_name = "imported_data.mp4"
                        self.all_roi_data[generic_name] = {}
                        for time_str, roi_info in data.items():
                            frame_num = roi_info.get("frame", 0)
                            self.all_roi_data[generic_name][frame_num] = self._parse_roi_string(roi_info.get("roi", ""))
                    else:
                        for filename, frame_data in data.items():
                            self.all_roi_data[filename] = {}
                            for time_str, roi_info in frame_data.items():
                                frame_num = roi_info.get("frame", 0)
                                self.all_roi_data[filename][frame_num] = self._parse_roi_string(roi_info.get("roi", ""))
        except Exception as e:
            pass

    def _is_old_format(self, data):
        """Check if data is in old flat timestamp format."""
        if not data:
            return False
        first_value = next(iter(data.values()))
        return isinstance(first_value, dict) and "frame" in first_value and "roi" in first_value

    def _parse_roi_string(self, roi_str):
        """Parse 'x1 y1 x2 y2' string to tuple."""
        try:
            coords = [int(x) for x in roi_str.split()]
            if len(coords) == 4:
                return tuple(coords)
        except:
            pass
        return (0, 0, 0, 0)

    def setup_ui(self):
        """Build the user interface."""
        main = tk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ctrl = tk.Frame(main)
        ctrl.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(ctrl, text="Load Video", command=self.load_video_dialog).pack(side=tk.LEFT, padx=3)
        tk.Button(ctrl, text="Reset", command=self.reset_memory, bg='#FFB6C1').pack(side=tk.LEFT, padx=3)
        tk.Button(ctrl, text="Save ROI", command=self.save_roi, bg='#90EE90').pack(side=tk.LEFT, padx=3)
        tk.Button(ctrl, text="Export", command=self.export_roi, bg='#87CEEB').pack(side=tk.LEFT, padx=3)

        tk.Label(ctrl, text="  Zoom:").pack(side=tk.LEFT, padx=5)
        tk.Button(ctrl, text="+", command=self.zoom_in, width=3).pack(side=tk.LEFT, padx=1)
        tk.Button(ctrl, text="-", command=self.zoom_out, width=3).pack(side=tk.LEFT, padx=1)

        self.status_label = tk.Label(ctrl, text="Ready", fg="blue")
        self.status_label.pack(side=tk.LEFT, padx=20)

        content = tk.Frame(main)
        content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        canvas_frame = tk.Frame(content)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg='gray20', cursor='crosshair')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind('<Button-1>', self.on_mouse_down)
        self.canvas.bind('<B1-Motion>', self.on_mouse_move)
        self.canvas.bind('<ButtonRelease-1>', self.on_mouse_up)
        self.canvas.bind('<MouseWheel>', self.on_scroll)
        self.canvas.bind('<Button-4>', self.on_scroll)
        self.canvas.bind('<Button-5>', self.on_scroll)

        right = tk.Frame(content)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10)

        tk.Label(right, text="ROI Info:", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        self.info_text = tk.Text(right, width=22, height=8, bg='lightgray', state=tk.DISABLED, font=("Courier", 8))
        self.info_text.pack(fill=tk.X, pady=3)

        tk.Label(right, text="History:", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        self.history_text = tk.Text(right, width=22, height=8, bg='lightyellow', state=tk.DISABLED, font=("Courier", 8))
        self.history_text.pack(fill=tk.BOTH, expand=True, pady=3)

        tk.Label(right, text="Preview:", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        self.preview_canvas = tk.Canvas(right, width=200, height=200, bg='black')
        self.preview_canvas.pack()

        play_ctrl = tk.Frame(main)
        play_ctrl.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(play_ctrl, text="<<", command=self.go_start, width=3).pack(side=tk.LEFT, padx=2)
        tk.Button(play_ctrl, text="-10s", command=self.back_10s, width=4).pack(side=tk.LEFT, padx=2)
        tk.Button(play_ctrl, text="-1s", command=self.back_1s, width=4).pack(side=tk.LEFT, padx=2)
        tk.Button(play_ctrl, text="<-", command=self.back_frame, width=3).pack(side=tk.LEFT, padx=2)
        tk.Button(play_ctrl, text="Play/Pause", command=self.toggle_play, bg='#FFFFE0', width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(play_ctrl, text="->", command=self.forward_frame, width=3).pack(side=tk.LEFT, padx=2)
        tk.Button(play_ctrl, text="+1s", command=self.forward_1s, width=4).pack(side=tk.LEFT, padx=2)
        tk.Button(play_ctrl, text="+10s", command=self.forward_10s, width=4).pack(side=tk.LEFT, padx=2)
        tk.Button(play_ctrl, text=">>", command=self.go_end, width=3).pack(side=tk.LEFT, padx=2)

        slider_frame = tk.Frame(main)
        slider_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(slider_frame, text="Frame:").pack(side=tk.LEFT, padx=5)
        self.slider = tk.Scale(slider_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.on_slider_move)
        self.slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.frame_label = tk.Label(slider_frame, text="0/0", width=12)
        self.frame_label.pack(side=tk.LEFT, padx=5)

    def bind_keyboard(self):
        """Bind keyboard shortcuts."""
        self.root.bind('s', lambda e: self.save_roi())
        self.root.bind('Space', lambda e: self.toggle_play())
        self.root.bind('Right', lambda e: self.forward_frame())
        self.root.bind('Left', lambda e: self.back_frame())
        self.root.bind('End', lambda e: self.go_end())
        self.root.bind('Home', lambda e: self.go_start())

    def load_video_dialog(self):
        """Open file browser to load video."""
        path = filedialog.askopenfilename(
            title="Select Video",
            filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv"), ("All", "*.*")]
        )
        if path:
            self.load_video(path)

    def load_video(self, path):
        """Load a video file."""
        try:
            self.video_path = path
            self.current_video_filename = Path(path).name
            self.cap = cv2.VideoCapture(str(path))

            if self.cap is None or not self.cap.isOpened():
                messagebox.showerror("Error", f"Cannot open: {path}")
                return

            w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            f = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
            fps = self.cap.get(cv2.CAP_PROP_FPS)

            self.frame_width = int(w) if w else 0
            self.frame_height = int(h) if h else 0
            self.total_frames = int(f) if f else 0
            self.fps = float(fps) if fps and float(fps) > 0 else 30.0

            self.slider.config(to=max(1, self.total_frames - 1))

            if self.current_video_filename in self.all_roi_data:
                self.roi_history = self.all_roi_data[self.current_video_filename].copy()
            else:
                self.roi_history = {}
                self.all_roi_data[self.current_video_filename] = self.roi_history

            self.go_start()
            self.update_history()
            self.status_label.config(text=f"Loaded: {self.current_video_filename} ({self.frame_width}x{self.frame_height})", fg="green")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load: {str(e)}\n\n{traceback.format_exc()}")

    def get_frame(self, frame_num):
        """Get frame at index."""
        if not self.cap:
            return None
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, float(frame_num))
        ret, frame = self.cap.read()
        if ret:
            self.current_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.current_frame_num = int(frame_num)
            return self.current_frame
        return None

    def draw_frame(self):
        """Draw frame and ROI on canvas."""
        if self.current_frame is None:
            return

        h = int(self.frame_height * self.zoom)
        w = int(self.frame_width * self.zoom)

        frame = cv2.resize(self.current_frame, (w, h))
        img = Image.fromarray(frame)
        self.photo_image = ImageTk.PhotoImage(img)

        self.canvas.delete("all")
        self.canvas.create_image(self.pan_x, self.pan_y, image=self.photo_image, anchor=tk.NW)

        if not self.drawing:
            self.load_nearest_roi()

        if self.roi_box:
            x1, y1, x2, y2 = self.roi_box
            x1d = x1 * self.zoom + self.pan_x
            y1d = y1 * self.zoom + self.pan_y
            x2d = x2 * self.zoom + self.pan_x
            y2d = y2 * self.zoom + self.pan_y

            self.canvas.create_rectangle(x1d, y1d, x2d, y2d, outline='red', width=2)
            for hx, hy in [(x1d, y1d), (x2d, y2d)]:
                self.canvas.create_rectangle(hx-4, hy-4, hx+4, hy+4, fill='red', outline='white', width=1)

        self.update_info()
        self.update_preview()

    def update_preview(self):
        """Update ROI preview."""
        if not self.roi_box or self.current_frame is None:
            self.preview_canvas.delete("all")
            return

        x1, y1, x2, y2 = self.roi_box
        if x2 <= x1 or y2 <= y1:
            self.preview_canvas.delete("all")
            return

        roi = self.current_frame[y1:y2, x1:x2]
        if roi.size == 0:
            self.preview_canvas.delete("all")
            return

        h, w = roi.shape[:2]
        scale = min(200.0/w, 200.0/h) if w and h else 1.0
        nw, nh = int(w*scale), int(h*scale)

        roi = cv2.resize(roi, (nw, nh))
        img = Image.fromarray(roi)
        self.preview_photo = ImageTk.PhotoImage(img)

        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(100, 100, image=self.preview_photo, anchor=tk.CENTER)

    def update_info(self):
        """Update info panel."""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)

        if self.roi_box:
            x1, y1, x2, y2 = self.roi_box
            time = self.format_time(self.current_frame_num / self.fps)
            info = f"Frame: {self.current_frame_num}\nTime: {time}\n\nx1: {x1} y1: {y1}\nx2: {x2} y2: {y2}\n\nSize: {x2-x1}x{y2-y1}\n\n{x1} {y1} {x2} {y2}"
        else:
            info = "No ROI.\nDrag to draw box."

        self.info_text.insert(1.0, info)
        self.info_text.config(state=tk.DISABLED)

    def update_history(self):
        """Update history panel."""
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete(1.0, tk.END)

        if self.current_video_filename:
            self.history_text.insert(1.0, f"File: {self.current_video_filename}\n\n")

        if not self.roi_history:
            self.history_text.insert(tk.END, "No ROIs")
        else:
            for fn in sorted(self.roi_history.keys()):
                x1, y1, x2, y2 = self.roi_history[fn]
                t = self.format_time(fn / self.fps) if self.fps > 0 else "00:00:00"
                self.history_text.insert(tk.END, f"{t}\n{x1} {y1} {x2} {y2}\n\n")

        self.history_text.config(state=tk.DISABLED)

    def load_nearest_roi(self):
        """Load ROI from history near current frame."""
        if not self.roi_history:
            self.roi_box = None
            return

        closest = min(self.roi_history.keys(), key=lambda f: abs(f - self.current_frame_num))
        if abs(closest - self.current_frame_num) <= 30:
            self.roi_box = self.roi_history[closest]
        else:
            self.roi_box = None

    def reset_memory(self):
        """Clear all ROI data from memory."""
        if messagebox.askyesno("Reset", "Clear all ROI data?"):
            self.all_roi_data.clear()
            self.roi_history.clear()
            self.update_history()
            self.status_label.config(text="All data cleared", fg="blue")

    def save_roi(self):
        """Save ROI for current frame."""
        if not self.roi_box:
            messagebox.showwarning("Warning", "No ROI drawn.")
            return
        if not self.current_video_filename:
            messagebox.showwarning("Warning", "No video loaded.")
            return

        self.roi_history[self.current_frame_num] = self.roi_box
        self.all_roi_data[self.current_video_filename] = self.roi_history

        self.update_history()
        t = self.format_time(self.current_frame_num / self.fps)
        self.status_label.config(text=f"ROI saved at {t}", fg="green")

    def export_roi(self):
        """Export all ROI data grouped by filename."""
        if not self.all_roi_data:
            messagebox.showwarning("Warning", "No ROIs to export.")
            return

        try:
            out_file = Path(__file__).parent / self.config['output']['output_file']

            export = {}
            for fname, roi_dict in self.all_roi_data.items():
                if roi_dict:
                    export[fname] = {}
                    for fn, (x1, y1, x2, y2) in roi_dict.items():
                        fps = self.fps if fname == self.current_video_filename else 30.0
                        t = self.format_time(fn / fps)
                        export[fname][t] = {
                            "frame": fn,
                            "roi": f"{x1} {y1} {x2} {y2}"
                        }

            with open(out_file, 'w') as f:
                json.dump(export, f, indent=2)

            messagebox.showinfo("Success", f"Exported to {out_file.name}")
            self.status_label.config(text=f"Exported to {out_file.name}", fg="green")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")

    def on_mouse_down(self, e):
        """Start drawing ROI."""
        self.drawing = True
        self.start_point = (e.x, e.y)

    def on_mouse_move(self, e):
        """Draw ROI while dragging."""
        if not self.drawing or not self.start_point:
            return

        h = int(self.frame_height * self.zoom)
        w = int(self.frame_width * self.zoom)

        x1c = max(0, min(e.x - self.pan_x, w))
        y1c = max(0, min(e.y - self.pan_y, h))
        x1f = int(x1c / self.zoom)
        y1f = int(y1c / self.zoom)

        x2c = max(0, min(self.start_point[0] - self.pan_x, w))
        y2c = max(0, min(self.start_point[1] - self.pan_y, h))
        x2f = int(x2c / self.zoom)
        y2f = int(y2c / self.zoom)

        x1 = min(x1f, x2f)
        y1 = min(y1f, y2f)
        x2 = max(x1f, x2f)
        y2 = max(y1f, y2f)

        self.roi_box = (x1, y1, x2, y2)
        self.draw_frame()

    def on_mouse_up(self, e):
        """Stop drawing ROI."""
        self.drawing = False

    def on_scroll(self, e):
        """Zoom on scroll."""
        if e.num == 5 or e.delta < 0:
            self.zoom_out()
        else:
            self.zoom_in()

    def zoom_in(self):
        """Increase zoom."""
        self.zoom = min(self.zoom + 0.1, 3.0)
        self.draw_frame()

    def zoom_out(self):
        """Decrease zoom."""
        self.zoom = max(self.zoom - 0.1, 0.5)
        self.draw_frame()

    def go_start(self):
        """Go to frame 0."""
        if self.cap:
            self.get_frame(0)
            self.update_slider()
            self.draw_frame()

    def go_end(self):
        """Go to last frame."""
        if self.cap:
            self.get_frame(self.total_frames - 1)
            self.update_slider()
            self.draw_frame()

    def back_frame(self):
        """Go back 1 frame."""
        if self.cap:
            self.get_frame(max(0, self.current_frame_num - 1))
            self.update_slider()
            self.draw_frame()

    def forward_frame(self):
        """Go forward 1 frame."""
        if self.cap:
            self.get_frame(min(self.total_frames - 1, self.current_frame_num + 1))
            self.update_slider()
            self.draw_frame()

    def back_1s(self):
        """Go back 1 second."""
        if self.cap:
            self.get_frame(max(0, int(self.current_frame_num - self.fps)))
            self.update_slider()
            self.draw_frame()

    def forward_1s(self):
        """Go forward 1 second."""
        if self.cap:
            self.get_frame(min(self.total_frames - 1, int(self.current_frame_num + self.fps)))
            self.update_slider()
            self.draw_frame()

    def back_10s(self):
        """Go back 10 seconds."""
        if self.cap:
            self.get_frame(max(0, int(self.current_frame_num - self.fps * 10)))
            self.update_slider()
            self.draw_frame()

    def forward_10s(self):
        """Go forward 10 seconds."""
        if self.cap:
            self.get_frame(min(self.total_frames - 1, int(self.current_frame_num + self.fps * 10)))
            self.update_slider()
            self.draw_frame()

    def on_slider_move(self, val):
        """Move to slider position."""
        if not self.slider_updating and self.cap:
            self.get_frame(int(float(val)))
            self.draw_frame()

    def update_slider(self):
        """Update slider to current frame."""
        self.slider_updating = True
        self.slider.set(self.current_frame_num)
        self.frame_label.config(text=f"{self.current_frame_num}/{self.total_frames}")
        self.slider_updating = False

    def toggle_play(self):
        """Toggle play/pause."""
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.play()

    def play(self):
        """Play video."""
        if self.is_playing and self.cap:
            self.forward_frame()
            delay = int(1000 / (self.fps * self.play_speed))
            self.root.after(delay, self.play)

    def format_time(self, seconds):
        """Format seconds to HH:MM:SS."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def run(self):
        """Start the app."""
        self.root.mainloop()


def main():
    parser = argparse.ArgumentParser(description="ROI Tool for WhisperX")
    parser.add_argument('--config', type=str, default=None, help='Config file path')
    parser.add_argument('--video', type=str, default=None, help='Video file path')

    args = parser.parse_args()
    app = ROITool(config_path=args.config, video_path=args.video)
    app.run()


if __name__ == "__main__":
    main()
