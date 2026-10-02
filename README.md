# ClipForge Desktop

ClipForge Desktop is an ongoing Windows desktop project for finding short video clips from longer recordings. The current development build uses local Vosk speech recognition, FFmpeg media processing, and optional Ollama scoring.

## Development status

**Experimental / ongoing development.** This is not a finished release. The application has not yet been fully tested on a clean Windows machine. Exported clips and scores must be reviewed manually.

The current build can:

- Run as a native Windows executable.
- Transcribe Greek, English, or both using the installed Vosk models.
- Show transcription progress.
- Save an SRT transcript.
- Generate speech-based candidate clips.
- Configure maximum clips, clip length, padding, and output folder.
- Export MP4 clips with FFmpeg.
- Optionally score transcript candidates with local Ollama `llama3.2:3b`.
- Save candidate metadata in `scores.json`.

The Greek Vosk model has limited accuracy on some old, noisy, compressed, or multi-speaker recordings. This is a known limitation of the current development build. The alternative Greek model tests were not good enough to replace Vosk, so the project currently keeps the original Vosk pipeline.

## Current limitations

- Mixed Greek-English recognition is experimental.
- Speech-based candidates are not guaranteed to be highlights.
- Ollama scores transcript text; it does not watch or understand the full video.
- Poor transcription produces poor AI scoring.
- No review table or video preview yet.
- No burned-in or karaoke captions yet.
- No vertical-video presets yet.
- No installer or published release yet.

## Requirements

- Windows 10 or newer.
- Python 3.12 64-bit with the `py` launcher for building.
- FFmpeg on PATH.
- Vosk English and Greek models.
- Ollama and `llama3.2:3b` only when AI scoring is enabled.

Check the tools in a new Command Prompt:

```bat
py -3.12 --version
ffmpeg -version
ollama list
```

## Models

Download Vosk speech models from the [official Vosk models page](https://alphacephei.com/vosk/models). Put the extracted model contents directly in:

```text
models\english\
models\greek\
```

Each selected folder must directly contain model directories such as `am`, `conf`, `graph`, and any other files supplied by the model. Do not leave a ZIP file or an extra nested model folder.

## Ollama

Install [Ollama for Windows](https://ollama.com/download/windows), then run:

```bat
ollama pull llama3.2:3b
ollama list
```

The app uses Ollama locally at `http://localhost:11434/api/generate`. Disable the AI-scoring checkbox if Ollama is not running.

## Project layout

```text
ClipForge-Desktop\
├── clipforge_desktop.py
├── requirements.txt
├── build-windows.cmd
├── README.md
└── models\
    ├── english\
    └── greek\
```

Do not commit models, videos, generated clips, WAV files, SRT files, `venv`, `build`, or `dist`.

## Build on Windows

Open Command Prompt in the project folder:

```bat
cd /d "E:\editing tools\ClipForge-Desktop"
build-windows.cmd
```

The executable is created at:

```text
dist\ClipForgeDesktop\ClipForgeDesktop.exe
```

Keep the entire `dist\ClipForgeDesktop` folder together. This is currently a portable development build, not an installer.

## Use the app

1. Start `ClipForgeDesktop.exe`.
2. Choose a source video.
3. Select Greek, English, or Greek + English.
4. Configure clip count, length, padding, and output folder.
5. Enable or disable Ollama scoring.
6. Click **Start**.
7. Review the MP4 files manually.

Typical output:

```text
ClipForge_Output\
├── clip_001.mp4
├── clip_002.mp4
├── transcript.srt
└── scores.json
```

## GitHub workflow

This repository is for ongoing development. Keep source code and documentation in Git; keep generated and large files out of Git.

First, inspect the files before staging:

```bat
git status
git diff -- README.md .gitignore clipforge_desktop.py build-windows.cmd requirements.txt
```

Stage only the intended project files:

```bat
git add clipforge_desktop.py build-windows.cmd requirements.txt README.md .gitignore
git status
```

Create the first commit:

```bat
git commit -m "Start ClipForge Desktop development"
```

If the GitHub repository is empty and no remote exists:

```bat
git remote add origin https://github.com/Intzevidis7/ClipForge-Desktop.git
git push -u origin main
```

If `origin` already exists:

```bat
git remote -v
git push -u origin main
```

For future changes:

```bat
git add .
git status
git commit -m "Describe the change"
git push
```

Do not publish a GitHub Release until the exact Windows executable has been tested.

## Roadmap

1. Stabilize Greek and mixed-language recognition.
2. Improve candidate grouping and remove duplicates.
3. Improve and validate Ollama scoring.
4. Add audio and scene-change signals.
5. Add clip preview and review before export.
6. Add captions and vertical-video presets.
7. Build and test an installer.
8. Publish a versioned Windows release.

## Licensing

Before distributing a public binary, check the licenses and redistribution terms for Vosk, the Vosk models, FFmpeg, Ollama/model components, and all Python dependencies.
