import socket
import wave

HOST = ''   # all interfaces
PORT = 8080

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)
print(f"Server listening on port {PORT}...")
conn, addr = s.accept()
print(f"Connection from {addr}")

with wave.open("output.wav", "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)      # 16‑bit
    wf.setframerate(44100)
    try:
        while True:
            data = conn.recv(4096)        # ↑ larger recv buffer
            if not data:
                break
            wf.writeframesraw(data)        # ↑ raw append for speed/quality
    except KeyboardInterrupt:
        pass

conn.close()
s.close()
print("saved to output.wav")