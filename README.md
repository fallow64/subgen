# subgen.py

A very simple Python script to transcribe audio/video files into a .srt file.

There are no CLI args. Instead, you are encouraged to directly modify the script yourself.

## Requirements

- `torch` (package)
    - Note: `torch` is only used for checking CUDA availability, and is only used within the first few lines of `subgen.py`. Feel free to remove and manually change the options.
- `ffmpeg` (system)
- `whisperx` (system)
    - Note: this does not use the python package, but instead it's CLI.
    - Install via `pip install whisperx`, and ensure that it's added to your system PATH.
