import os

def find_music_files(directory):
    """
    Recursively scans a directory and returns a sorted list
    of all .mp3 and .mp4 files.
    """
    valid_extensions = ('.mp3', '.mp4')
    songs = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(valid_extensions):
                songs.append(os.path.join(root, file))

    # Sort alphabetically by filename
    return sorted(songs, key=lambda x: os.path.basename(x).lower())
