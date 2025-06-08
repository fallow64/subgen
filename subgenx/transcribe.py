import gc
import os
import subprocess
import torch
import whisperx
import numpy as np
from whisperx import utils as wx_utils

from subgenx.util import Config


def load_audio(audio_path: str, audio_track: int) -> np.ndarray:
    """
    Load an audio file and return it as a normalized NumPy array. This is used by Whisper for transcription.
    
    whisperx.utils.load_audio is not used because it does not support selecting an audio track.
    """
    
    sr = 16000 # sample rate
    try:
        # Launches a subprocess to decode audio while down-mixing and resampling as necessary.
        # Requires the ffmpeg CLI to be installed.
        cmd = [
            "ffmpeg",
            "-nostdin",
            "-threads", "0",
            "-i", audio_path,
            "-map", f"0:a:{audio_track}",  # Select the specified audio track
            "-f", "s16le",
            "-ac", "1",
            "-acodec", "pcm_s16le",
            "-ar", str(sr),
            "-",
        ]
        out = subprocess.run(cmd, capture_output=True, check=True).stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to load audio: {e.stderr.decode()}") from e

    return np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0


def get_writer(output_format: str, output_dir: str) -> wx_utils.ResultWriter:
    """
    Get the appropriate writer based on the output format.
    
    Does not use whisperx.utils.get_writer because it is not typed correctly. (instead of a path, it's typed as a TextIO)
    """
    
    writers = {
        "txt": wx_utils.WriteTXT,
        "vtt": wx_utils.WriteVTT,
        "srt": wx_utils.WriteSRT,
        "tsv": wx_utils.WriteTSV,
        "json": wx_utils.WriteJSON,
        "aud": wx_utils.WriteAudacity,
    }

    return writers[output_format](output_dir)


def transcribe_with_whisperx(audio_path: str, options: Config):
    """Transcribe the given audio file using WhisperX."""

    output_dir = options.output_dir or os.path.dirname(audio_path)
    base_name, _ = os.path.splitext(os.path.basename(audio_path))
    output_file = os.path.join(output_dir, base_name + "." + options.output_format)

    up_to_date = os.path.exists(output_file) and (os.path.getmtime(output_file) > os.path.getmtime(audio_path))
    if up_to_date and (not options.force):
        print(f"Skipping {output_file}, up-to-date.")
        return output_file

    print("Output Directory: " + output_dir)
    
    # 1. Transcribe with original whisper (batched)
    model_dir = os.path.join(os.path.expanduser("~"), ".cache", "whisper")
    model = whisperx.load_model(
        options.model,
        options.device,
        compute_type=options.compute_type,
        download_root=model_dir,
        vad_options={
            "chunk_size": 30,
            "vad_onset": 0.500,
            "vad_offset": 0.363,
        },
        threads=4,
    )
    
    audio = load_audio(audio_path, options.audio_track or 0)
    result = model.transcribe(
        audio,
        language=options.language,
        verbose=options.verbose,
        batch_size=8,
        chunk_size=30,
    )
    
    # delete model
    gc.collect()
    torch.cuda.empty_cache()
    del model
    
    # 2. Align whisper output
    model_a, metadata = whisperx.load_align_model(
        language_code=result["language"] or options.language,
        device=options.device,
    )
    result_aligned = whisperx.align(
        result["segments"],
        model_a,
        metadata,
        audio,
        options.device,
        return_char_alignments=False,
        interpolate_method="nearest",
    )
    
    # delete model
    gc.collect()
    torch.cuda.empty_cache()
    del model_a
    
    # WhisperX align for some reason doesn't include langauge tag which is needed for get_writer in return for result
    if "language" not in result_aligned:
        result_aligned["language"] = result["language"] or options.language
    
    # 3. Save the result
    writer_opts = {
        # todo: make sure these are sane defaults
        "highlight_words": False,
        "max_line_count": None,
        "max_line_width": None,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        writer = get_writer(options.output_format, output_dir)
        writer.write_result(result_aligned, f, writer_opts)
        f.write("Transcription complete. Output saved to: " + output_file + "\n")
