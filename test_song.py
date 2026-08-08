import yt_dlp
ydl_opts = {
    'format': 'bestaudio/best', 
    'outtmpl': 'song.%(ext)s',
    'quiet': False,
}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download(["ytsearch:blinding lights"])
