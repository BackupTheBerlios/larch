#!/usr/bin/env python
# ldm_new_session.py

from socket import socket, AF_UNIX, SOCK_STREAM

def new_session():
    # Create an unbound and not-connected socket.
    sock = socket(AF_UNIX, SOCK_STREAM)

    # Connect to the peer registered as 'ldmd' in the abstract namespace.
    # Note the null-byte.
    sock.connect("\0ldmd")

    # Wait for message
    msg = sock.recv(64)
    print msg
    if msg and (msg.strip() == "ok"):
        # Send reply
        sock.send("NEW\n")
    else:
        print "failed to connect ..."

    # Block until new message arrives
    msg = sock.recv(64)
    if (not msg) or (msg.strip() != "done"):
        print "failed to start new session ..."

    # Close it
    sock.close()

if __name__ == "__main__":
    new_session()
