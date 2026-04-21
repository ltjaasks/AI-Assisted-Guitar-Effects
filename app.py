import sounddevice as sd
import threading
from pedalboard import *
from pedalboard.io import AudioStream

from PyQt6.QtWidgets import QApplication, QMainWindow, QSlider, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QGroupBox, QLineEdit, QPushButton
from PyQt6.QtCore import Qt
import sys

import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

changed = True

system_prompt = """
You are an assistant that controls a guitar effects processor.
Given a description of a desired guitar tone, respond with ONLY a valid JSON object — no explanation, no markdown, no backticks.
The JSON must match this exact structure with these exact keys:

{
    "noise_gate": {
        "threshold_db": <float, -100 to 0, higher means gate kicks in more>,
        "attack_ms": <float, 1 to 100>,
        "release_ms": <float, 1 to 500>
    },
    "compressor": {
        "threshold_db": <float, -60 to 0>,
        "ratio": <float, 1 to 20, higher means more compression>,
        "attack_ms": <float, 1 to 100>,
        "release_ms": <float, 1 to 500>
    },
    "distortion": {
        "drive_db": <float, 0 to 100, 0 means clean, higher means more distortion>
    },
    "chorus": {
        "depth": <float, 0 to 1>,
        "centre_delay_ms": <float, 0 to 10>,
        "feedback": <float, 0 to 1>,
        "mix": <float, 0 to 1, 0 means no chorus>
    },
    "phaser": {
        "rate_hz": <float, 0 to 10>,
        "depth": <float, 0 to 1>,
        "feedback": <float, -1 to 1>,
        "mix": <float, 0 to 1, 0 means no phaser>
    },
    "delay": {
        "delay_seconds": <float, 0 to 2>,
        "feedback": <float, 0 to 1>,
        "mix": <float, 0 to 1, 0 means no delay>
    },
    "reverb": {
        "room_size": <float, 0 to 1>,
        "damping": <float, 0 to 1>,
        "wet_level": <float, 0 to 1>,
        "dry_level": <float, 0 to 1>,
        "width": <float, 0 to 1>,
        "freeze_mode": <float, 0 or 1>
    },
    "gain": {
        "gain_db": <float, -80 to 20>
    }
}

Always return all effects and all parameters. Set mix/wet_level to 0 to effectively disable an effect.
"""

noise_gate_params = {
    "threshold_db": -50.0,
    "attack_ms": 1.0,
    "release_ms": 100.0
}

compressor_params = {
    "threshold_db": -20.0,
    "ratio": 4.0,
    "attack_ms": 1.0,
    "release_ms": 100.0
}

distortion_params = {
    "drive_db": 0.0
}

chorus_params = {
    "depth": 0.25,
    "centre_delay_ms": 7.0,
    "feedback": 0.0,
    "mix": 0.0
}

phaser_params = {
    "rate_hz": 1.0,
    "depth": 0.5,
    "feedback": 0.0,
    "mix": 0.0
}

delay_params = {
    "delay_seconds": 0.3,
    "feedback": 0.2,
    "mix": 0.0
}

reverb_params = {
    "room_size": 0.25,
    "damping": 0.5,
    "wet_level": 0.33,
    "dry_level": 0.4,
    "width": 1.0,
    "freeze_mode": 0.0
}

gain_params = {
    "gain_db": 0.0
}

effect_map = {
    "noise_gate": noise_gate_params,
    "compressor": compressor_params,
    "distortion": distortion_params,
    "chorus": chorus_params,
    "phaser": phaser_params,
    "delay": delay_params,
    "reverb": reverb_params,
    "gain": gain_params
}

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Guitar Effects")
        self.sliders = {}  # stores sliders as {(effect, param): (slider, scale)}

        root_layout = QVBoxLayout()

        ai_layout = QHBoxLayout()
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("Describe your tone... e.g. 'warm bluesy sound with lots of reverb'")
        self.ai_button = QPushButton("Apply")
        self.ai_button.clicked.connect(self.apply_ai)
        ai_layout.addWidget(self.ai_input)
        ai_layout.addWidget(self.ai_button)
        root_layout.addLayout(ai_layout)

        main_layout = QHBoxLayout()

        main_layout.addWidget(self.build_group("Noise Gate", "noise_gate", [
            ("Threshold (dB)", "threshold_db", -100, 0,   -50,  1),
            ("Attack (ms)",    "attack_ms",    1,    100, 1,    1),
            ("Release (ms)",   "release_ms",   1,    500, 100,  1),
        ]))

        main_layout.addWidget(self.build_group("Compressor", "compressor", [
            ("Threshold (dB)", "threshold_db", -60, 0,   -20, 1),
            ("Ratio",          "ratio",         1,   20,  4,   1),
            ("Attack (ms)",    "attack_ms",     1,   100, 1,   1),
            ("Release (ms)",   "release_ms",    1,   500, 100, 1),
        ]))

        main_layout.addWidget(self.build_group("Distortion", "distortion", [
            ("Drive (dB)", "drive_db", 0, 100, 0, 1),
        ]))

        main_layout.addWidget(self.build_group("Chorus", "chorus", [
            ("Depth",           "depth",          0, 100, 25, 100),
            ("Centre Delay ms", "centre_delay_ms", 0, 100, 70, 10),
            ("Feedback",        "feedback",        0, 100, 0,  100),
            ("Mix",             "mix",             0, 100, 0,  100),
        ]))

        main_layout.addWidget(self.build_group("Phaser", "phaser", [
            ("Rate (hz)",  "rate_hz",  0,  100, 10,  10),
            ("Depth",      "depth",    0,  100, 50,  100),
            ("Feedback",   "feedback", -100, 100, 0, 100),
            ("Mix",        "mix",      0,  100, 0,   100),
        ]))

        main_layout.addWidget(self.build_group("Delay", "delay", [
            ("Delay (s)",  "delay_seconds", 0, 200, 30, 100),
            ("Feedback",   "feedback",      0, 100, 20, 100),
            ("Mix",        "mix",           0, 100, 0,  100),
        ]))

        main_layout.addWidget(self.build_group("Reverb", "reverb", [
            ("Room Size", "room_size", 0, 100, 25,  100),
            ("Damping",   "damping",   0, 100, 50,  100),
            ("Wet Level", "wet_level", 0, 100, 33,  100),
            ("Dry Level", "dry_level", 0, 100, 40,  100),
            ("Width",     "width",     0, 100, 100, 100),
            ("Freeze",    "freeze_mode", 0, 1, 0,    1),
        ]))

        main_layout.addWidget(self.build_group("Volume", "gain", [
            ("Volume", "gain_db", 0, 100, 80, None),  # special case
        ]))

        root_layout.addLayout(main_layout)

        container = QWidget()
        container.setLayout(root_layout)
        self.setCentralWidget(container)

    def build_group(self, title, effect_key, sliders):
        group = QGroupBox(title)
        layout = QVBoxLayout()
        for (label, param, min_val, max_val, default, scale) in sliders:
            if scale is None:
                # special case for volume
                on_change = lambda v, e=effect_key, p=param: self.update(e, p, float(v - 80))
            else:
                on_change = lambda v, e=effect_key, p=param, s=scale: self.update(e, p, v / s)
            slider = self.add_slider(layout, label, min_val, max_val, default, on_change)
            self.sliders[(effect_key, param)] = (slider, scale)
        group.setLayout(layout)
        return group

    def add_slider(self, layout, label, min_val, max_val, default, on_change):
        lbl = QLabel(label)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(default)
        slider.valueChanged.connect(on_change)
        layout.addWidget(lbl)
        layout.addWidget(slider)
        return slider

    def update(self, effect, parameter, value):
        global changed
        effect_map[effect][parameter] = value
        changed = True

    def apply_ai(self):
        user_input = self.ai_input.text()
        if not user_input:
            return
        self.ai_button.setText("Thinking...")
        self.ai_button.setEnabled(False)
        threading.Thread(target=self.call_api, args=(user_input,), daemon=True).start()

    def call_api(self, user_input):
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "llama3.2",
            "system": system_prompt,
            "prompt": user_input,
            "stream": False
        })
        response_text = response.json()["response"].strip()
        new_params = json.loads(response_text)

        for effect, params in new_params.items():
            if effect in effect_map:
                for param, value in params.items():
                    if param in effect_map[effect]:
                        effect_map[effect][param] = value
                        self.update_slider(effect, param, value)

        global changed
        changed = True

        self.ai_button.setText("Apply")
        self.ai_button.setEnabled(True)

    def update_slider(self, effect, param, value):
        key = (effect, param)
        if key not in self.sliders:
            return
        slider, scale = self.sliders[key]
        if scale is None:
            slider_value = int(value + 80)  # reverse of volume mapping
        else:
            slider_value = int(value * scale)
        slider.setValue(max(slider.minimum(), min(slider.maximum(), slider_value)))

app = QApplication(sys.argv)
window = MainWindow()
window.show()

with AudioStream(
    input_device_name="Line (Steinberg UR22mkII )",
    output_device_name="Line (Steinberg UR22mkII )",
    num_input_channels=1,
    num_output_channels=2
) as stream:
    while True:
        app.processEvents()
        if not window.isVisible():
            break
        if changed:
            changed = False
            stream.plugins = Pedalboard([
                NoiseGate(**noise_gate_params),
                Compressor(**compressor_params),
                Distortion(**distortion_params),
                Chorus(**chorus_params),
                Phaser(**phaser_params),
                Delay(**delay_params),
                Reverb(**reverb_params),
                Gain(**gain_params)
            ])
        time.sleep(0.05)