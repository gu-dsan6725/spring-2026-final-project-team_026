#!/usr/bin/env python

# Remote python client.
# Execute Python commands remotely and send output back.

import sys
import socket
from typing import Optional

PORT: int = 4127
BUFSIZE: int = 1024

def main() -> None:
    """
    Execute Python commands remotely and send output back.

    Args:
        host (str): The host to connect to.
        command (str): The command to execute.

    Returns:
        None
    """
    if len(sys.argv) < 3:
        print("usage: rpython host command")
        sys.exit(2)
    host: str = sys.argv[1]
    port: int = PORT
    i: int = host.find(":")
    if i >= 0:
        port = int(host[i + 1:])
        host = host[:i]
    command: str = " ".join(sys.argv[2:])
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(command.encode())
        s.shutdown(socket.SHUT_WR)
        reply: bytes = b""
        while True:
            data: Optional[bytes] = s.recv(BUFSIZE)
            if not data:
                break
            reply += data
    print(reply.decode())

if __name__ == "__main__":
    main()