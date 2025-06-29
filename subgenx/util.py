import os
import urllib
import urllib.parse
from dataclasses import dataclass


@dataclass
class Config:
    """Configuration for SubgenX transcription."""
    
    # General config
    force: bool
    verbose: bool
    download_dir: str
    output_dir: str | None
    
    # Local video config
    audio_track: int
    
    # Youtube config
    include_video: bool

    # WhisperX config
    model: str
    output_format: str
    device: str
    compute_type: str
    language: str | None


def is_file_whisper_compatible(path: str):
    """Check if the file is an audio/video format supported by Whisper natively."""
    
    if os.path.isfile(path):
        # todo: probably restrict this, or have a comprehensive list of actual supported formats instead of guessing
        _, ext = os.path.splitext(path)
        whisper_extensions = [".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm", ".flac", ".aac", ".ogg", ".opus", ".mkv", ".avi", ".mov", ".flv"]
        return ext.lower() in whisper_extensions
    return False


def is_youtube_url(url: str):
    """Check if the URL is a YouTube URL."""
    youtube_domains = ["youtube.com", "youtu.be"]
    
    parsed = urllib.parse.urlparse(url)
    netloc = parsed.netloc.lower()
    return any((domain in netloc) for domain in youtube_domains)
