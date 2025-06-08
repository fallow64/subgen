# subgenx

A CLI utility to transcribe audio/video using [WhisperX](https://github.com/m-bain/whisperX/).

## Features

- Transcribe audio and video files to text.
- Download YouTube audio (and video) and transcribe it.
- Transcribe all files in a directory.

## Installation

To install `subgenx`:

1. Clone the repository: (`git` must be installed)
   ```bash
   git clone https://github.com/fallow64/subgenx.git
   ```

2. Navigate to the cloned directory:
   ```bash
   cd subgenx
   ```

3. Install `subgenx` using `pip`.
   ```bash
   pip install .
   ```
   Now, you can use the `subgenx` command in your terminal.
   Alternatively, you can run it without installing it via `python subgenx`.


## Usage

To transcribe an audio or video file, use the following command:

```bash
subgenx <path_to_file>
```

To view a list of all available commands and options, run `subgenx --help`.

Here are some examples:

```bash
# Transcribe using the medium model
# (default: small, bigger models may yield better accuracy but require more resources)
subgenx Pre-Parade.mp3 --model=medium

# Transcribe a local audio file using CUDA
# (default: CUDA if detected, else CPU)
subgenx Pre-Parade.mp3 --device=cuda

# Transcribe and specify the language
# (for example: anime openings may mess with auto-detection)
subgenx Toradora01.mkv --language=de

# Specify the audio track
# (some videos have multiple audio tracks)
subgenx D:\Content\Toradora --audio_track=1

# Transcribe a YouTube video by providing the URL
subgenx https://youtu.be/CzOEMJSQRZU

# Transcribe a YouTube video, as well as download the video itself
subgenx https://youtu.be/CzOEMJSQRZU --include_video
```
