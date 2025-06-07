import os
from dataclasses import dataclass


@dataclass
class Config:
    """Configuration for SubgenX transcription."""
    
    # General config
    base_cmd: list[str]
    locations: list[str]
    force: bool
    
    # Local vidoe config
    audio_track: int | None
    
    # Youtube config
    yt_download_video: bool
    yt_download_subtitles: bool

    model: str
    output_format: str
    device: str | None
    language: str | None
    compute_type: str | None


def is_audio_file(path: str):
    """Check if the file is a common audio format."""
    
    if os.path.isfile(path):
        _, ext = os.path.splitext(path)
        audio_extensions = [".mp3", ".m4a", ".wav", ".flac", ".aac", ".ogg", ".opus"]
        return ext.lower() in audio_extensions
    return False



def is_video_file(path: str):
    """Check if the file is a common video format."""
    
    if os.path.isfile(path):
        _, ext = os.path.splitext(path)
        video_extensions = [".mp4", ".mkv", ".avi", ".mov", ".flv", ".webm"]
        return ext.lower() in video_extensions
    return False


def is_youtube_url(url: str):
    """Check if the URL is a YouTube URL."""
    return "youtube.com/watch" in url or "youtu.be" in url or "youtube.com/shorts" in url
