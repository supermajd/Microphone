# Microphone

A small command-line tool that turns audio recordings into clean, organized text transcripts using OpenAI. Drop in a file, get back a tidy transcript with a metadata header — interviews, meetings, voice notes, lectures.

## Features

- **Any common format** — `mp3`, `mp4`, `m4a`, `wav`, `webm`, `mpeg`, `mpga`.
- **Handles long recordings** — files over the API size limit are automatically split into chunks, transcribed, and stitched back together.
- **Clean output** — transcripts are grouped into readable paragraphs with a metadata header (speaker, subject, date, description).
- **Scriptable or interactive** — pass everything as flags for cron/CI, or run it bare and answer a few prompts.
- **Stays organized** — processed audio and previous transcripts are archived automatically, so nothing gets reprocessed by accident.

## Setup

Install [ffmpeg](https://ffmpeg.org/) (required for audio processing):

```bash
brew install ffmpeg
```

> On Linux, use `sudo apt install ffmpeg` instead.

Clone the repo and install the Python dependencies:

```bash
git clone https://github.com/YOUR_USERNAME/Microphone.git
cd Microphone
pip install -r requirements.txt
```

Create a `.env` file in the project root and add your OpenAI API key:

```bash
OPENAI_API_KEY=your-key-here
```

## Usage

Drop an audio file into `data/audio/`, then run:

```bash
# Interactive — prompts for metadata
python run.py

# Fully scripted — no prompts (cron / CI friendly)
python run.py --non-interactive \
    --speaker "Filippa" \
    --subject "Q3 review" \
    --description "Board meeting" \
    --date 2026-05-21
```

The finished transcript lands in `data/txt/`, named to match the source file.

### Options

| Flag | Description |
|------|-------------|
| `--speaker` | Name of the speaker |
| `--subject` | Subject of the recording |
| `--description` | Short description (also used as a context hint for the model) |
| `--date` | Recording date (`YYYY-MM-DD`). Defaults to today. |
| `--non-interactive` | Never prompt — use defaults for anything not passed |

## Project layout

```
data/
├── audio/        # drop a file here to transcribe
├── txt/          # finished transcript
├── chunks/       # scratch space for large files
└── history/      # processed audio + past transcripts
```

## License

MIT