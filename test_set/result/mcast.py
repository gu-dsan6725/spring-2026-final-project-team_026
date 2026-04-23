# Send/receive UDP multicast packets.
# Requires that your OS kernel supports IP multicast.
# This is built-in on SGI, still optional for most other vendors.
#
# Usage:
#   mcast -s (sender)
#   mcast -b (sender, using broadcast instead multicast)
#   mcast    (receivers)

MYPORT = 8123
MYGROUP = '225.0.0.250'

import sys
import time
import struct
import re
import socket

# Main program
def main():
    flags = sys.argv[1:]
    #
    if flags:
        sender(flags[0])
    else:
        receiver()


# Sender subroutine (only one per local area network)
def sender(flag):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if flag == '-b':
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        mygroup = '<broadcast>'
    else:
        mygroup = MYGROUP
        ttl = struct.pack('b', 1)  # Time-to-live
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    while 1:
        data = str(time.time())
        s.sendto(data.encode(), (mygroup, MYPORT))
        time.sleep(1)


# Receiver subroutine (as many as you like)
def receiver():
    # Open and initialize the socket
    s = open_mcast_sock(MYGROUP, MYPORT)
    #
    # Loop, printing any data we receive
    while 1:
        data, sender = s.recvfrom(1500)
        while data[-1:] == '\0': data = data[:-1]  # Strip trailing \0's
        print(sender, ':', str(data))


# Open a UDP socket, bind it to a port and select a multicast group
def open_mcast_sock(group, port):
    # Create a socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #
    # Allow multiple copies of this program on one machine
    # (not strictly needed)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #
    # Bind it to the port
    s.bind(('', port))
    #
    # Look up multicast group address in name server
    # (doesn't hurt if it is already in ddd.ddd.ddd.ddd format)
    group = socket.gethostbyname(group)
    #
    # Construct binary group address
    bytes = [int(x) for x in group.split('.')]
    grpaddr = 0
    for byte in bytes: grpaddr = (grpaddr << 8) | byte
    #
    # Construct struct mreq from grpaddr and ifaddr
    ifaddr = socket.INADDR_ANY
    mreq = struct.pack('ll', socket.htonl(grpaddr), socket.htonl(ifaddr))
    #
    # Add group membership
    s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    #
    return s


main()