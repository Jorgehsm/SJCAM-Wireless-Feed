import socket
import threading
import subprocess
import time
import cv2
import numpy as np

CAMERA_IP = "192.168.100.1"
TCP_PORT = 6666
UDP_PORT = 6669
WIDTH, HEIGHT = 640, 480
FRAME_SIZE = WIDTH * HEIGHT * 3
WINDOW_NAME = "SJCAM Feed"

def send_keep_alive(tcp_socket):
    keep_alive_packet = bytes([0xAB, 0xCD, 0x00, 0x00, 0x00, 0x00, 0x01, 0x13])
    while True:
        try:
            tcp_socket.sendall(keep_alive_packet)
            print("KEEP-ALIVE sent")
        except Exception as e:
            print("Error sending KEEP-ALIVE:", e)
            break
        time.sleep(8)

def login_payload():
    username = b"admin"
    password = b"12345"
    payload = bytearray(128)
    payload[:len(username)] = username
    payload[64:64+len(password)] = password
    header = bytearray([0xAB, 0xCD, 0x00, 128, 0x00, 0x00, 0x01, 0x10])
    return header + payload

def rtsp_command():
    return bytearray([0xAB, 0xCD, 0x00, 8, 0x00, 0x00, 0x01, 0xFF] + [0x00]*8)

def main():
    # TCP login loop
    while True:
        try:
            print("Connecting to camera...")
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.connect((CAMERA_IP, TCP_PORT))
            tcp_socket.sendall(login_payload())
            response = tcp_socket.recv(8)
            if response == bytes([0xAB, 0xCD, 0x00, 129, 0x00, 0x00, 0x01, 0x11]):
                print("Login successful.")
                break
            else:
                print("Unexpected response:", response.hex())
                tcp_socket.close()
                time.sleep(1)
        except Exception as e:
            print("Connection error:", e)
            time.sleep(1)

    tcp_socket.sendall(rtsp_command())
    threading.Thread(target=send_keep_alive, args=(tcp_socket,), daemon=True).start()

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('', UDP_PORT))

    ffmpeg_process = subprocess.Popen(
        [
            "ffmpeg",
            "-loglevel", "quiet",
            "-i", "-",
            "-f", "rawvideo",
            "-pix_fmt", "bgr24",
            "-"
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE
    )

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

    try:
        while True:
            print(f"Listening for UDP packets on port {UDP_PORT}...")
            data, addr = udp_socket.recvfrom(65536)
            print(f"{len(data)} bytes received from {addr} - start of data: {data[:10].hex()}")

    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        cv2.destroyAllWindows()
        udp_socket.close()
        tcp_socket.close()
        ffmpeg_process.terminate()

if __name__ == "__main__":
    main()
