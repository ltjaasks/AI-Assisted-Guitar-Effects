# AI-Assisted Guitar Effects Processor

A real-time guitar effects processor with an AI-assisted tone control. Describe the sound you want in plain English and the AI will configure the effects chain for you.

## Demo

Type a description like *"heavy metal distortion with no reverb"* or *"warm bluesy tone with lots of reverb"* and the AI sets all effect parameters automatically. You can then fine-tune the result manually using the sliders.

## Features

- Real-time audio processing with low latency
- Effects chain: Noise Gate → Compressor → Distortion → Chorus → Phaser → Delay → Reverb → Volume
- AI-assisted tone control powered by a local LLM via Ollama — no API keys, no cloud, no usage limits
- Manual slider controls for every effect parameter
- Sliders update visually when AI applies a tone

## Requirements

- A guitar audio interface (developed with Steinberg UR22mkII)
- [Ollama](https://ollama.com) installed and running locally
- Python 3.11+

## Setup

**1. Clone the repository**
```
git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name
```

**2. Create and activate a virtual environment**
```
python -m venv venv
venv\Scripts\activate
```

**3. Install dependencies**
```
pip install -r requirements.txt
```

**4. Install Ollama and pull the model**

Download and install Ollama from https://ollama.com, then pull the model:
```
ollama pull llama3.2
```

**5. Make sure Ollama is running**
```
ollama serve
```

**6. Run the app**
```
python app.py
```

## Usage

- Plug your guitar into input 1 of your audio interface
- Plug your headphones or monitors into the audio interface output
- Launch the app — audio passes through immediately
- Type a tone description in the text box at the top and press Apply
- Fine-tune the result using the sliders

## Tech Stack

- [pedalboard](https://github.com/spotify/pedalboard) — audio effects processing
- [sounddevice](https://python-sounddevice.readthedocs.io) — audio I/O
- [PyQt6](https://pypi.org/project/PyQt6/) — desktop UI
- [Ollama](https://ollama.com) — local LLM inference
- [llama3.2](https://ollama.com/library/llama3.2) — language model for tone interpretation

## Notes

- Audio device names are currently hardcoded for the Steinberg UR22mkII. If you use a different interface, update the `input_device_name` and `output_device_name` in `app.py`.
- AI tone accuracy depends on the model. `mistral` tends to follow instructions more precisely than `llama3.2` if you want to experiment.
- This is a prototype and a practice project. The AI supplied effects are not very accurate
