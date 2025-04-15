import socket
import wave

host = '192.168.239.50'  # ESP32 IP
port = 8080

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))

with wave.open("output.wav", "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)  # 16-bit audio
    wf.setframerate(44100)
    
    print("Receiving audio and writing to output.wav...")
    try:
        while True:
            data = s.recv(1024)
            print(f"Received {len(data)} bytes")  # <- add this
            if not data:
                break
            wf.writeframes(data)
    except KeyboardInterrupt:
        pass

s.close()
print("Done! Play it with: aplay output.wav")
