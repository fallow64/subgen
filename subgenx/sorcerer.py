import os
import subprocess
from abc import ABC, abstractmethod

from subgenx.util import Config, is_audio_file, is_video_file, is_youtube_url


class Source(ABC):
    @abstractmethod
    def can_handle(self, location: str, config: Config) -> bool:
        """Check if the source can handle the given location."""
        pass

    @abstractmethod
    def handle(self, location: str, config: Config) -> str | list[str] | None:
        """
        Handle the location and return the path to the audio file.
        
        If the source returns a string, it is a single audio file.
        
        If it returns a list, it a list of further locations to source.
        
        If it returns None, it means the source could not handle the location.
        """
        pass


class AudioSource(Source):
    def can_handle(self, location: str, config: Config) -> bool:
        return is_audio_file(location)

    def handle(self, location: str, config: Config) -> str:
        # If the location is an audio file, return it as is
        return location


class VideoSource(Source):
    def can_handle(self, location: str, config: Config) -> bool:
        return is_video_file(location)

    def handle(self, location: str, config: Config) -> str | None:
        base, _ = os.path.splitext(location)
        
        # Convert video file to mp3
        mp3_path = base + ".mp3"

        if os.path.exists(mp3_path) and os.path.getmtime(mp3_path) > os.path.getmtime(location):
            # If the mp3 was last updated after the mp4, it's up-to-date so use that
            # todo: this could be the wrong audio track or something? better handling needed
            print(f"Existing associated audio file: {mp3_path}")
            return mp3_path

        # Convert video to audio using ffmpeg
        print(f"Converting {location} to mp3...")

        cmd = ["ffmpeg", "-y"]  # -y to overwrite existing files
        cmd.extend(["-i", location])  # input file
        if config.audio_track is not None:
            # select the specified audio track
            cmd.extend(["-map", f"0:a:{config.audio_track}"])
        cmd.extend(["-acodec", "libmp3lame"])  # use the mp3 codec
        cmd.extend(["-ab", "192k"])  # set bitrate to 192kbps
        cmd.append("-vn")  # no video
        cmd.append(mp3_path)  # output file

        subprocess.run(cmd, check=True)

        return mp3_path


class YoutubeSource(Source):
    def can_handle(self, location: str, config: Config) -> bool:
        return is_youtube_url(location)

    def handle(self, location: str, config: Config) -> str | None:
        # Use youtube-dl to download the audio from the YouTube link
        import yt_dlp
        
        #todo: option to download video instead of audio
        
        print(f"Downloading audio from YouTube: {location}")
        ydl_opts = {
            "format": "bestaudio/best",
            "extractaudio": True,
            "audioformat": "mp3",
            "outtmpl": "%(title)s.%(ext)s",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(location, download=True)
            audio_file = ydl.prepare_filename(info)
            return audio_file


class DirectorySource(Source):
    def can_handle(self, location: str, config: Config) -> bool:
        return os.path.isdir(location)

    def handle(self, location: str, config: Config) -> str | list[str] | None:
        # Recursively find all audio files in the directory
        audio_files = []
        for root, _, files in os.walk(location):
            for file in files:
                full_path = os.path.join(root, file)
                if is_audio_file(full_path) or is_video_file(full_path):
                    audio_files.append(full_path)
        
        # If there is only one audio file, return it as a string
        # Otherwise return the list of audio files (empty list if none found)
        return audio_files[0] if len(audio_files) == 1 else audio_files


class Sorcerer:
    def __init__(self, config: Config):
        self.config = config
        self.sources = [AudioSource(), VideoSource(), YoutubeSource(), DirectorySource()]

    def handle_location(self, location: str) -> list[str] | None:
        results = []
        location_queue = [location]
        
        while len(location_queue) > 0:
            current_location = location_queue.pop(0)
            result = self._handle_single_location(current_location)
            
            if result is not None:
                if isinstance(result, str):
                    results.append(result)
                elif isinstance(result, list):
                    location_queue.extend(result)

        return results if results else None
                    
    def _handle_single_location(self, location: str) -> str | list[str] | None:
        for source in self.sources:
            if source.can_handle(location, self.config):
                # location_result can be a single audio file path, a list of further locations, or None
                location_result = source.handle(location, self.config)
                
                if location_result is None:
                    continue
                
                # location_result can be a string (single file) or a list (multiple loations to check further)
                return location_result

        # No source could handle the location
        return None                
        