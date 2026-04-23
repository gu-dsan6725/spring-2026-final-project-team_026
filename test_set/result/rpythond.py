#!/usr/bin/env python3

import sys
import socket
import io
import traceback
from typing import Any

PORT = 4127
BUFSIZE = 1024

def main():
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = PORT
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', port))
        s.listen(1)
        while True:
            conn, (remotehost, remoteport) = s.accept()
            print(f'connected by {remotehost} {remoteport}')
            request = b''
            while True:
                data = conn.recv(BUFSIZE)
                if not data:
                    break
                request += data
            reply = execute(request.decode('utf-8'))
            conn.sendall(reply.encode('utf-8'))
            conn.close()

def execute(request: str) -> str:
    stdout = sys.stdout
    stderr = sys.stderr
    sys.stdout = sys.stderr = io.StringIO()
    try:
        try:
            exec(request, {}, {})
        except Exception as e:
            print()
            traceback.print_exc(100)
    finally:
        sys.stderr = stderr
        sys.stdout = stdout
    return sys.stdout.getvalue()

if __name__ == '__main__':
    main()