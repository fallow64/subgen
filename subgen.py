import os
import subprocess
import torch
import sys


model: str                  = "medium"
compute_type: str           = "int8"
device: str                 = "cuda" if torch.cuda.is_available() else "cpu"
output_format: str          = "srt"
language: str | None        = "de"


def is_audio_ext(ext):
    audio_extensions = [".mp3", ".m4a", ".wav", ".flac", ".aac", ".ogg"]
    return ext.lower() in audio_extensions


def is_video_ext(ext):
    video_extensions = [".mp4", ".mkv", ".avi", ".mov"]
    return ext.lower() in video_extensions


def convert_to_mp3(input_path):
    base, ext = os.path.splitext(input_path)
    
    if is_audio_ext(ext):
        # File is already an mp3, continue
        return input_path
    elif is_video_ext(ext):
        # Convert video file to mp3
        mp3_path = base + ".mp3"

        if os.path.exists(mp3_path):
            if os.path.getmtime(mp3_path) > os.path.getmtime(input_path):
                # If the mp3 was last updated after the mp4, it's up-to-date so use that
                print(f"Using existing audio file: {mp3_path}")
                return mp3_path
        
        # Convert mp4 or mkv to mp3 using ffmpeg
        print(f"Converting {input_path} to mp3...")
        cmd = ["ffmpeg", "-y", "-i", input_path, "-vn", "-acodec", "libmp3lame", mp3_path]
        subprocess.run(cmd, check=True)

        return mp3_path
    else:
        raise ValueError("Unsupported file type. Only video and audio files are supported.")


def transcribe_with_whisperx(audio_path):
    output_dir = os.path.dirname(os.path.abspath(audio_path))
    base_name, _ = os.path.splitext(os.path.basename(audio_path))
    output_file = os.path.join(output_dir, base_name + "." + output_format)

    if os.path.exists(output_file) and (os.path.getmtime(output_file) > os.path.getmtime(audio_path)):
        print(f"Output file {output_file} already exists and is up-to-date. Skipping transcription.")
        return

    print("Output Directory: " + output_dir)
    
    cmd = ["whisperx", audio_path, "--model", model, "--compute_type", compute_type, "--output_dir", output_dir, "--device", device]
    if output_format:
        cmd.extend(["--output_format", output_format])
    if language:
        cmd.extend(["--language", language])
    
    res = subprocess.run(cmd, check=False)
    if res.returncode != 0 and res.returncode == 127:
        print("Error: 'whisperx' command not found. Please ensure WhisperX is installed and available in your PATH.")
        sys.exit(1)
    elif res.returncode != 0:
        print(f"Error: WhisperX transcription failed with return code {res.returncode}. Please check the input file and stderr.")
        sys.exit(1)
    else:
        print(f"Transcription completed successfully for {audio_path}. Output saved in {output_dir}.")


def main():
    file_paths = []

    if len(sys.argv) != 1:
        # If command line arguments are provided, use them as file paths
        file_paths.extend(sys.argv[1:])
    else:
        # No command line arguments, prompt the user for input
        input_paths = input("Enter the paths of the video/audio files to transcribe (separated by spaces, or leave empty for current directory): ").strip().split()

        if len(input_paths) == 0:
            # Use the current working directory
            print("No input paths provided. Using the current working directory.")
            cwd = os.getcwd()
            for file in os.listdir(cwd):
                full_path = os.path.join(cwd, file)
                _, ext = os.path.splitext(file)
                if os.path.isfile(full_path) and (is_audio_ext(ext) or is_video_ext(ext)):
                    file_paths.append(full_path)
        else:
            # User provided paths
            for input_path in input_paths:
                # Check if the input path is a file or directory
                if os.path.isfile(input_path):
                    file_paths.append(input_path)
                elif os.path.isdir(input_path):
                    # If it's a directory, list all files in it
                    for file in os.listdir(input_path):
                        full_path = os.path.join(input_path, file)
                        _, ext = os.path.splitext(file)
                        if os.path.isfile(full_path) and (is_audio_ext(ext) or is_video_ext(ext)):
                            file_paths.append(full_path)

    
    for file_path in file_paths:
        try:
            mp3_path = convert_to_mp3(file_path)
            transcribe_with_whisperx(mp3_path)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
