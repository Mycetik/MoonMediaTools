import socket
import concurrent.futures
from logger.logger import log

def _check_socket(host: str, port: int, timeout: float) -> bool:
    try:
        socket.create_connection((host, port), timeout=timeout)
        return True
    except OSError:
        return False


def is_internet_available(timeout: float = 1.0) -> bool:
    servers = [
        ("1.1.1.1", 53),
        ("8.8.8.8", 53),
        ("9.9.9.9", 53)
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(servers)) as executor:
        futures = [executor.submit(_check_socket, host, port, timeout) for host, port in servers]

        for future in concurrent.futures.as_completed(futures):
            if future.result():
                return True

    log.warn("Internet check failed. No connection.")
    return False