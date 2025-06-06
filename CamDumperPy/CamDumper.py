import socket
import subprocess
import threading
import time

CAMERA_IP = "192.168.100.1"
TCP_PORT = 6666
UDP_PORT = 6669

def send_keep_alive(tcp_socket):
    keep_alive_packet = bytes([0xAB, 0xCD, 0x00, 0x00, 0x00, 0x00, 0x01, 0x13])
    while True:
        try:
            tcp_socket.sendall(keep_alive_packet)
            print("KEEP-ALIVE sent")
        except Exception as e:
            print("Error sending keep-alive:", e)
            break
        time.sleep(8)

def login_payload():
    username = b"admin"
    password = b"12345"
    payload = bytearray(128)
    payload[:len(username)] = username
    payload[64:64+len(password)] = password
    header = bytearray([0xAB, 0xCD, 0x00, 0x80, 0x00, 0x00, 0x01, 0x10])
    return header + payload

def rtsp_command():
    return bytearray([0xAB, 0xCD, 0x00, 0x08, 0x00, 0x00, 0x01, 0xFF] + [0x00] * 8)

def main():
    tcp_socket = None
    while True:
        try:
            print("Trying to connect to camera...")
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.connect((CAMERA_IP, TCP_PORT))
            tcp_socket.sendall(login_payload())
            print("Login sent")

            response = tcp_socket.recv(8)
            if response == bytes([0xAB, 0xCD, 0x00, 0x81, 0x00, 0x00, 0x01, 0x11]):
                print("Login accepted")
                break
            else:
                print("Login failed or unexpected response:", response.hex())
                tcp_socket.close()
                time.sleep(1)
        except Exception as e:
            print("Login attempt error:", e)
            if tcp_socket:
                tcp_socket.close()
            time.sleep(1)

    tcp_socket.sendall(rtsp_command())

    threading.Thread(target=send_keep_alive, args=(tcp_socket,), daemon=True).start()

    ffplay_process = subprocess.Popen(
        ['ffplay', '-loglevel', 'quiet', '-i', '-', '-fflags', 'nobuffer', '-flags', 'low_delay', '-framedrop'],
        stdin=subprocess.PIPE
    )

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('', UDP_PORT))

    try:
        while True:
            data, _ = udp_socket.recvfrom(65536)
            if len(data) < 8:
                continue

            if data[0:2] != bytes([188, 222]):
                continue

            if data[7] == 1:
                video_payload = data[8:]
                ffplay_process.stdin.write(video_payload)

    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        ffplay_process.terminate()
        udp_socket.close()
        tcp_socket.close()

if __name__ == "__main__":
    main()
