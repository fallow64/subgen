import os
import subprocess
import sys
from subgenx.util import Config


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
    
    cmd = options.base_cmd.copy()

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
    
    return output_file
