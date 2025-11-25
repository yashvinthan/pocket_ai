import socket
from pocket_ai.core.logger import logger

def check_internet(host="8.8.8.8", port=53, timeout=3):
    """
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        logger.debug(f"Internet check failed: {ex}")
        return False

class InternetChecker:
    def is_connected(self) -> bool:
        return check_internet()

internet_checker = InternetChecker()
