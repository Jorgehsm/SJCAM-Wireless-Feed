import socket
import struct
import subprocess
import threading
import time

CAMERA_IP = "192.168.100.1"
TCP_PORT = 6666
UDP_PORT = 6669

def send_keep_alive(sock):
    alive_packet = bytes({0xAB, 0xCD, 0x00, 0x00, 0x00, 0x00, 0x01, 0x13})
    while True:
        try:
            sock.sendall(alive_packet)
            print("KEEP-ALIVE")
        except Exception as e:
            print("Erro ao enviar keep-alive", e)
            break
        time.sleep(8)

def login_payload():
    username = b"admin"
    password = b"12345"
    payload = bytearray(128)
    payload[:len(username)] = username
    payload[64:64+len(password)] = password
    header = bytearray([171, 205, 0, 128, 0, 0, 1, 16])
    return header + payload

def rtsp_command():
    return bytearray([171, 205, 0, 8, 0, 0, 1, 255] + [0] * 8)

def main():
    # Inicia TCP para login
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.connect((CAMERA_IP, TCP_PORT))
    tcp.sendall(login_payload())

    print("Login enviado")

    # Espera confirmação
    resp = tcp.recv(8)
    if resp != bytes([171, 205, 0, 129, 0, 0, 1, 17]):
        print("Login falhou ou resposta inesperada")
        return

    print("Login aceito, iniciando feed")
    tcp.sendall(rtsp_command())

    # keep-alive
    threading.Thread(target=send_keep_alive, args=(tcp,),daemon=True).start()

    # Inicia ffplay subprocess para exibição ao vivo
    ffmpeg = subprocess.Popen(
        ['ffplay', '-loglevel', 'quiet', '-i', '-', '-fflags', 'nobuffer', '-flags', 'low_delay', '-framedrop'],
        stdin=subprocess.PIPE
    )

    # Abre socket UDP para receber vídeo
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind(('', UDP_PORT))

    try:
        while True:
            data, _ = udp.recvfrom(65536)
            if len(data) < 8:
                continue

            if data[0:2] != bytes([188, 222]):
                continue

            if data[7] == 1:  # tipo de mensagem == 1 (dados de vídeo)
                video_data = data[8:]
                ffmpeg.stdin.write(video_data)

    except KeyboardInterrupt:
        print("Encerrando...")
    finally:
        ffmpeg.terminate()
        udp.close()
        tcp.close()

if __name__ == "__main__":
    main()
