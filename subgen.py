import argparse
import os
import subprocess
import sys
from dataclasses import dataclass


# The base command to run WhisperX. For example, you could change this to `["uvx whisperx"]`.
base_cmd = ["whisperx"]

# Configuration from the CLI.
@dataclass
class Config:
    files: list[str]
    force: bool

    model: str
    output_format: str
    device: str | None
    language: str | None
    compute_type: str | None


def is_audio_ext(ext: str):
    """Check if the file extension is a common audio format."""
    audio_extensions = [".mp3", ".m4a", ".wav", ".flac", ".aac", ".ogg"]
    return ext.lower() in audio_extensions


def is_video_ext(ext: str):
    """Check if the file extension is a common video format."""
    video_extensions = [".mp4", ".mkv", ".avi", ".mov"]
    return ext.lower() in video_extensions


def convert_to_mp3(input_path: str):
    """Convert the input file to mp3 if it is a video file, or return the path if it is already an audio file."""

    base, ext = os.path.splitext(input_path)
    if is_audio_ext(ext):
        # File is already an mp3, continue
        print(f"Existing audio file: {input_path}")
        return input_path
    elif is_video_ext(ext):
        # Convert video file to mp3
        mp3_path = base + ".mp3"

        if os.path.exists(mp3_path) and os.path.getmtime(mp3_path) > os.path.getmtime(input_path):
                # If the mp3 was last updated after the mp4, it's up-to-date so use that
                print(f"Existing associated audio file: {mp3_path}")
                return mp3_path
        
        # Convert video to audio using ffmpeg
        print(f"Converting {input_path} to mp3...")
        cmd = ["ffmpeg", "-y", "-i", input_path, "-vn", "-acodec", "libmp3lame", mp3_path]
        subprocess.run(cmd, check=True)

        return mp3_path
    else:
        raise ValueError("Unsupported file type. Only video and audio files are supported.")


def transcribe_with_whisperx(audio_path: str, options: Config):
    """Transcribe the given audio file using WhisperX."""

    output_dir = os.path.dirname(os.path.abspath(audio_path))
    base_name, _ = os.path.splitext(os.path.basename(audio_path))
    output_file = os.path.join(output_dir, base_name + "." + options.output_format)

    up_to_date = os.path.exists(output_file) and (os.path.getmtime(output_file) > os.path.getmtime(audio_path))
    if up_to_date and (not options.force):
        print(f"Skipping {output_file}, up-to-date.")
        return output_file

    print("Output Directory: " + output_dir)
    
    cmd = base_cmd.copy()

    # For each field in WhisperXConfig, add the corresponding command line argument
    cmd.extend(["--model", options.model])
    cmd.extend(["--output_format", options.output_format])
    if options.language:
        cmd.extend(["--language", options.language])
    if options.device:
        cmd.extend(["--device", options.device])
    if options.compute_type:
        cmd.extend(["--compute_type", options.compute_type])

    cmd.extend(["--output_dir", output_dir])
    cmd.append(audio_path)
    
    print(f"Running command: {' '.join(cmd)}")
    res = subprocess.run(cmd, check=False)
    if res.returncode == 127:
        print("Error: Command not found. Please ensure WhisperX is installed and available in your PATH.")
        sys.exit(1)
    elif res.returncode != 0:
        print(f"Error: WhisperX transcription failed with return code {res.returncode}. Please check the input file and stderr.")
        sys.exit(1)
    else:
        print(f"Transcription successful. Output saved to {output_file}.")


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio and video files to subtitles using WhisperX.")
    parser.add_argument("--model", type=str, default=None, help="WhisperX model to use (default: small)")
    parser.add_argument("--output_format", type=str, default=None, help="Output subtitle format (default: srt)")
    parser.add_argument("--language", type=str, default=None, help="Language of the audio (default: auto-detect, slower and error-prone)")
    parser.add_argument("--device", type=str, default=None, help="Device to use for transcription (default: cuda if available, otherwise cpu)")
    parser.add_argument("--compute_type", type=str, default=None, help="Compute type for transcription (default: float16 if cuda is available, otherwise int8)")
    parser.add_argument("--force", action="store_true", help="Force transcription even if output file already exists and is up-to-date")
    parser.add_argument("files", nargs="+", help="Audio or video files, or directories containing such files")
    
    # Parse the arguments, provide default values if not specified
    args = parser.parse_args()
    if args.model is None:
        args.model = "small"
    if args.output_format is None:
        args.output_format = "srt"
    if args.device is None:
        # Note: importing torch here to avoid unnecessary dependency if not using GPU
        # although technically whisperx already depends on torch
        import torch
        args.device = "cuda" if torch.cuda.is_available() else "cpu"
    if args.compute_type is None:
        import torch
        args.compute_type = "float16" if torch.cuda.is_available() else "int8"

    # Create WhisperXConfig from parsed arguments
    options: Config = Config(
        files=args.files,
        force=args.force,
        model=args.model,
        output_format=args.output_format,
        device=args.device,
        language=args.language,
        compute_type=args.compute_type
    )

    # The list holding all file paths to video/audio files
    file_paths = []

    def add_folder_files(folder: str):
        """Recursively add files from a folder."""
        for root, _, files in os.walk(folder):
            for file in files:
                full_path = os.path.join(root, file)
                _, ext = os.path.splitext(file)
                if is_audio_ext(ext) or is_video_ext(ext):
                    file_paths.append(full_path)
    
    def add_file(file: str):
        """Add a single file if it is an audio or video file."""
        _, ext = os.path.splitext(file)
        if is_audio_ext(ext) or is_video_ext(ext):
            file_paths.append(file)

    # Files/directories provided
    for file in options.files:
        if os.path.isfile(file):
            add_file(file)
        elif os.path.isdir(file):
            add_folder_files(file)
        else:
            print(f"Invalid path: {file} is not a valid file or directory.")

    if len(file_paths) == 0:
        # While the user can't provide no files, they can provide a folder with no valid files (or fake files)
        print("No valid audio or video files found. Please provide valid files or directories containing audio/video files.")
        sys.exit(1)

    for file_path in file_paths:
        mp3_path = convert_to_mp3(file_path)
        transcribe_with_whisperx(mp3_path, options)


if __name__ == "__main__":
    main()
