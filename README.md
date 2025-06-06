# subgen.py

A very simple Python CLI utility to transcribe audio/video files into a .srt file.

## Requirements

- `torch` (package)
    - Note: only for automatic detection of CUDA. If CLI args are specified, torch is not imported.
- `ffmpeg` (system)
- `whisperx` (system)
    - Note: this does not use the python package, but instead it's CLI.
    - Install via `pip install whisperx`, and ensure that it's added to your system PATH.

## Notes

On AMD GPUs, transcribing via the GPU (i.e. using ROCm) is very *very* shakey. Unless you know exactly what you're doing, I would advise you set the `--device=cpu`.