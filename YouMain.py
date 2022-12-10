import os
import shutil
import sys
import time
import traceback
from os import system, name
import logging
import yt_dlp

logger = logging.getLogger(__name__)

# File extensions to move to the "thumbnail" directory
FILE_EXTENSIONS = ['.webp', '.png', 'jpg']

# Prompt the user for the path to save files, and print a message indicating
# where the thumbnails will be moved to
with open("location.txt", 'w+t') as s:
    s.write(input("path to save files: "))
    s.seek(0)
    data = s.read()
    print("thumbnails will be moved to " + data + "\\thumbnail")


def run():
    # Loop indefinitely to download multiple videos
    while True:
        # Get the URL of the YouTube video from the user
        video_url = input("\nplease enter youtube video url: ")
        # noinspection SpellCheckingInspection
        # Set the options for the yt_dlp library
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best',
            'download_archive': 'downloaded_songs.txt',
            'windowsfilenames': True,
            'outtmpl': data + '/%(title)s.%(ext)s',
            'writesubtitles': True,
            'subtitleslangs': ['en', '-live_chat'],
            'writethumbnail': True,
            'embedthumbnail': True,
            'postprocessors': [
                {'key': 'FFmpegMetadata',
                 'add_metadata': True, },
                {'key': 'FFmpegEmbedSubtitle'},
                {'key': 'EmbedThumbnail',
                 'already_have_thumbnail': True,
                 },
            ],
        }

        # Error message to log if an error occurs while downloading the video
        url_error = 'Error. Moving to next URL.'
        try:
            # Use the yt_dlp library to download the video and its thumbnail
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                error_code = ydl.download([video_url])

                # Check if any videos failed to download, and log an error if so
                if error_code:
                    print('Some videos failed to download ')
                else:
                    print("\nDownload complete... ")
                    # Move the thumbnail to the appropriate directory
                    thumbnail_path(FILE_EXTENSIONS)
                    # Clear the screen and ask the user if they want to download another video
                    clear()
        except yt_dlp.utils.DownloadError:
            logger.error(url_error)
            return False


def thumbnail_path(file_extensions):
    # Set the source and destination paths for the thumbnails
    source_path = data
    source_files = os.listdir(source_path)
    destination_path = data + '/thumbnail'

    # Check if the "thumbnail" directory exists, and create it if it doesn't
    if not os.path.exists(destination_path):
        os.makedirs(destination_path)

    # Loop through the files in the source directory
    for file in source_files:
        # Loop through the specified file extensions
        for extension in file_extensions:
            # If the file has one of the specified extensions, move it to the destination directory
            if file.endswith(extension):
                shutil.move(os.path.join(source_path, file), os.path.join(destination_path, file))


def close():
    # Wait for one second before closing the program
    time.sleep(0)
    print('\nBye')
    time.sleep(1)
    sys.exit()


def clear():
    # Loop indefinitely until the user provides a valid response
    while True:
        # Ask the user if they want to download another video
        ans = input("\nDo you want to start again? (y/n) ")
        # If the user responds with "y", clear the screen and start the download process again
        if ans.lower() == "y":
            system('cls' if name == 'nt' else 'clear')
            time.sleep(0)
            run()
        # If the user responds with "n", clear the screen and close the program
        elif ans.lower() == 'n':
            system('cls' if name == 'nt' else 'clear')
            close()
        # If the user provides any other response, ask them to try again
        else:
            print("Please respond with 'Yes' or 'No'\n")


# If the script is run directly (i.e. not imported as a module), run the main download process
if __name__ == '__main__':
    try:
        # Start the download process
        run()
    except KeyboardInterrupt:
        # If the user interrupts the process (e.g. with Ctrl+C), log an error and ask if they want to try again
        print('\nInterrupted')
        while True:
            clear()
    except Exception:
        # If any other error occurs, log it to a file and print a message to the user
        with open("log.txt", "w") as log:
            traceback.print_exc(file=log)
            print('\nError is printed to log.txt')
            close()
