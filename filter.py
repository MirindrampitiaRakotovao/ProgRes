from datetime import datetime

def load_blacklist():
    try:
        with open("blacklist.txt", "r") as f:
            return set(line.strip().lower() for line in f if line.strip())
    except FileNotFoundError:
        return set()

blacklist = load_blacklist()

blocked_extensions = {'.exe', '.zip', '.torrent', '.mp4'}
blocked_hours = range(8, 17)  

def is_blocked(host, url):
    now = datetime.now()
    host = host.lower()
    url = url.lower()


    for site in blacklist:
        if site in host or site in url:
            return True


    for ext in blocked_extensions:
        if url.endswith(ext):
            return True


    if now.hour in blocked_hours:
        if 'facebook' in host or 'tiktok' in host:
            return True

    return False
