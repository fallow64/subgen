import argparse
import sys

from subgenx.sorcerer import Sorcerer
from subgenx.transcribe import transcribe_with_whisperx
from subgenx.util import Config


def main():
    # fmt: off
    parser = argparse.ArgumentParser(description="Transcribe audio and video files to subtitles using WhisperX.", add_help=False)
    parser.add_argument("locations", nargs="+", help="The locations of audio or video files. Can also be a folder containing audio/video files.")
    
    general = parser.add_argument_group("General Options")
    general.add_argument("-h", "--help", action="help", help="Show this help message and exit")
    general.add_argument("-f", "--force", action="store_true", help="Force transcription even if output subtitles already exist and is up-to-date")
    general.add_argument("-d", "--download_dir", type=str, default=None, help="Directory to download YouTube videos to (default: current directory)")
    general.add_argument("-o", "--output_dir", type=str, default=".", help="Directory to save output subtitles to (default: alongside the audio files)")
    
    whisper = parser.add_argument_group("WhisperX Options")
    whisper.add_argument("--model", type=str, default="small", help="WhisperX model to use (default: small)")
    whisper.add_argument("--output_format", type=str, default="srt", help="Output subtitle format (default: srt)")
    whisper.add_argument("--language", type=str, default=None, help="Language of the audio (default: auto-detect, slower and error-prone)")
    whisper.add_argument("--device", type=str, default=None, help="Device to use for transcription (default: cuda if available, otherwise cpu)")
    whisper.add_argument("--compute_type", type=str, default=None, help="Compute type for transcription (default: float16 if cuda is available, otherwise int8)")
    
    sourcing = parser.add_argument_group("Sourcing Options")
    sourcing.add_argument("--audio_track", type=int, default=0, help="Audio track to use for video files (default: 0, the first audio track)")
    sourcing.add_argument("--include_video", action="store_true", help="Include the video of a YouTube download (default: false)")

    # Parse the arguments, provide default values if not specified
    args = parser.parse_args()
    if args.device is None:
        # Note: importing torch here to avoid unnecessary dependency if not using GPU
        # although technically whisperx already depends on torch
        import torch
        args.device = "cuda" if torch.cuda.is_available() else "cpu"
    if args.compute_type is None:
        import torch
        args.compute_type = "float16" if torch.cuda.is_available() else "int8"

    # Create Config from parsed arguments
    config = Config(
        base_cmd=["whisperx"],
        locations=args.locations,
        force=args.force,
        download_dir=args.download_dir,
        output_dir=args.output_dir,
        include_video=args.include_video,
        model=args.model,
        output_format=args.output_format,
        device=args.device,
        language=args.language,
        audio_track=args.audio_track,
        compute_type=args.compute_type,
    )

    # The list holding the paths to the *audio* files to be processed
    file_paths = []

    sorcerer = Sorcerer(config)
    # Files/directories/locations provided
    for file in config.locations:
        result = sorcerer.handle_location(file)

        if result is not None:
            file_paths.extend(result)
        else:
            print(f"Could not handle location: {file}. Please ensure it is a valid audio/video file or directory containing such files.")

    if len(file_paths) == 0:
        # While the user can't provide no files, they can provide a folder with no valid files (or fake files)
        print("No valid audio or video files found. Please provide valid files or directories containing audio/video files.")
        sys.exit(1)

    for file_path in file_paths:
        transcribe_with_whisperx(file_path, config)


if __name__ == "__main__":
    main()
