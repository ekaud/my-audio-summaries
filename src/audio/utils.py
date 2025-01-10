import os
import time
from pathlib import Path
from typing import Optional, Tuple

def save_audio(audio: bytes, title: str, directory: str = "output/audio") -> str:
    """
    Save audio bytes to a file with a sanitized name
    
    Args:
        audio: Audio data as bytes
        title: Original title to base filename on
        directory: Output directory (default: output/audio)
        
    Returns:
        str: Path to saved audio file
    """
    # Create a sanitized version of the filename
    safe_title = "".join(
        c if c.isalnum() or c in ('-', '_') 
        else '-' if c.isspace() 
        else '' 
        for c in title
    ).rstrip('-')
    
    # Create output directory if it doesn't exist
    output_dir = Path(directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create output filepath with timestamp
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    output_path = output_dir / f"{safe_title}_{timestamp}.mp3"
    
    # Write the audio to file
    with open(output_path, "wb") as f:
        f.write(audio)
    
    return str(output_path)

def cleanup_old_files(directory: str = "output/audio", max_age_hours: int = 24):
    """
    Remove audio files older than specified age
    
    Args:
        directory: Directory to clean (default: output/audio)
        max_age_hours: Maximum age in hours (default: 24)
    """
    output_dir = Path(directory)
    if not output_dir.exists():
        return
        
    max_age_seconds = max_age_hours * 60 * 60
    current_time = time.time()
    
    for file in output_dir.glob("*.mp3"):
        if file.is_file() and (current_time - file.stat().st_mtime) > max_age_seconds:
            file.unlink() 

def save_transcript(transcript: str, title: str, directory: str = "output/transcripts") -> str:
    """
    Save transcript text to a file
    
    Args:
        transcript: The transcript text to save
        title: Original title to base filename on
        directory: Output directory (default: output/transcripts)
        
    Returns:
        str: Path to saved transcript file
    """
    # Create a sanitized version of the filename
    safe_title = "".join(
        c if c.isalnum() or c in ('-', '_') 
        else '-' if c.isspace() 
        else '' 
        for c in title
    ).rstrip('-')
    
    # Create output directory if it doesn't exist
    output_dir = Path(directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create output filepath with timestamp
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    output_path = output_dir / f"{safe_title}_{timestamp}.txt"
    
    # Write the transcript to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(transcript)
    
    return str(output_path)

def save_audio_and_transcript(
    audio: bytes, 
    transcript: str, 
    title: str, 
    audio_dir: str = "output/audio",
    transcript_dir: str = "output/transcripts"
) -> Tuple[str, str]:
    """
    Save both audio and transcript files
    
    Args:
        audio: Audio data as bytes
        transcript: Transcript text
        title: Original title to base filename on
        audio_dir: Audio output directory (default: output/audio)
        transcript_dir: Transcript output directory (default: output/transcripts)
        
    Returns:
        Tuple[str, str]: Paths to saved (audio_file, transcript_file)
    """
    # Save both files with same timestamp for easy matching
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    
    # Create a sanitized version of the filename
    safe_title = "".join(
        c if c.isalnum() or c in ('-', '_') 
        else '-' if c.isspace() 
        else '' 
        for c in title
    ).rstrip('-')
    
    # Create output directories
    audio_dir = Path(audio_dir)
    transcript_dir = Path(transcript_dir)
    audio_dir.mkdir(parents=True, exist_ok=True)
    transcript_dir.mkdir(parents=True, exist_ok=True)
    
    # Create output filepaths
    audio_path = audio_dir / f"{safe_title}_{timestamp}.mp3"
    transcript_path = transcript_dir / f"{safe_title}_{timestamp}.txt"
    
    # Save files
    with open(audio_path, "wb") as f:
        f.write(audio)
    
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(transcript)
    
    return str(audio_path), str(transcript_path) 