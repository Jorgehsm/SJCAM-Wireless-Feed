import socket
import threading
import time
import cv2

CAMERA_IP = "192.168.100.1"
TCP_PORT = 6666
UDP_PORT = 6669

def login_payload():
    username = b"admin"
    password = b"12345"
    payload = bytearray(128)
    payload[:len(username)] = username
    payload[64:64+len(password)] = password
    header = bytearray([0xAB, 0xCD, 0x00, 0x80, 0x00, 0x00, 0x01, 0x10])
    return header + payload

def rtsp_command():
    return bytearray([0xAB, 0xCD, 0x00, 0x08, 0x00, 0x00, 0x01, 0xFF] + [0x00]*8)

def send_keep_alive(tcp_socket):
    keep_alive_packet = bytes([0xAB, 0xCD, 0x00, 0x00, 0x00, 0x00, 0x01, 0x13])
    while True:
        try:
            tcp_socket.sendall(keep_alive_packet)
        except:
            break
        time.sleep(8)

def activate_stream():
    while True:
        try:
            print("Connecting to camera...")
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.connect((CAMERA_IP, TCP_PORT))

            tcp_socket.sendall(login_payload())
            response = tcp_socket.recv(8)

            if response == bytes([0xAB, 0xCD, 0x00, 0x81, 0x00, 0x00, 0x01, 0x11]):
                print("Login successful, activating stream")
                tcp_socket.sendall(rtsp_command())
                threading.Thread(target=send_keep_alive, args=(tcp_socket,), daemon=True).start()
                return tcp_socket
            else:
                print("Login failed or unexpected response:", response.hex())
                tcp_socket.close()
                time.sleep(1)
        except Exception as e:
            print("Login attempt error:", e)
            time.sleep(1)

def main():
    tcp_socket = activate_stream()
    
    print("Waiting for UDP stream (H264)...")

    udp_url = f"udp://@:{UDP_PORT}?fifo_size=1000000&overrun_nonfatal=1"
    video_capture = cv2.VideoCapture(udp_url, cv2.CAP_FFMPEG)

    if not video_capture.isOpened():
        print("Failed to open UDP stream with OpenCV + FFmpeg.")
        return

    cv2.namedWindow("Live Feed", cv2.WINDOW_NORMAL)

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("Frame not received.")
            continue

        cv2.imshow("Live Feed", frame)

        if cv2.waitKey(1) == 27:  # ESC key to exit
            break

    video_capture.release()
    cv2.destroyAllWindows()
    tcp_socket.close()

if __name__ == "__main__":
    main()
