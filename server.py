import socket
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import scipy.signal
import csv
import paho.mqtt.client as mqtt
import json

HOST = ''
PORT = 8080

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)
print(f"Server listening on port {PORT}…")

conn, addr = s.accept()
print(f"Client connected from {addr}")

model = hub.load('https://tfhub.dev/google/yamnet/1')
class_map_path = model.class_map_path().numpy().decode('utf-8')
def class_names_from_csv(path):
    names = []
    with tf.io.gfile.GFile(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            names.append(row['display_name'])
    return names

class_names = class_names_from_csv(class_map_path)

DESIRED_SR = 16000
def ensure_sample_rate(orig_sr, waveform, target_sr=DESIRED_SR):
    if orig_sr != target_sr:
        desired_len = int(round(len(waveform) * target_sr / orig_sr))
        waveform = scipy.signal.resample(waveform, desired_len)
    return target_sr, waveform

ORIG_SR = 44100
WINDOW_SEC = 0.96
WINDOW_SAMPLES = int(ORIG_SR * WINDOW_SEC)
WINDOW_BYTES   = WINDOW_SAMPLES * 2

MQTT_BROKER = '192.168.173.204'
MQTT_PORT   = 1883
MQTT_TOPIC  = 'esp32/sensors'

mqtt_client = None

def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")

def on_disconnect(client, userdata, rc):
    print(f"Disconnected from MQTT broker with result code {rc}")

def setup_mqtt():
    global mqtt_client
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect    = on_connect
    mqtt_client.on_disconnect = on_disconnect
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"MQTT connect error: {e}")

def publish_detection(danger):
    global mqtt_client
    if mqtt_client is None:
        setup_mqtt()

    try:
        payload = json.dumps({"audio": danger})
        mqtt_client.publish(MQTT_TOPIC, payload)
        print("MQTT publish:", payload)
    except Exception as e:
        print(f"MQTT publish error: {e}")
        setup_mqtt()

DANGEROUS_SOUNDS = {
    "Gunshot":   0.5,
    "Explosion": 0.5,
    "Vehicle":  0.5,
    "Speech":  0.2,
}

buffer = b''
THRESH = 0.2

setup_mqtt()

try:
    while True:
        data = conn.recv(4096)
        if not data:
            break
        buffer += data

        while len(buffer) >= WINDOW_BYTES:
            chunk, buffer = buffer[:WINDOW_BYTES], buffer[WINDOW_BYTES:]

            pcm = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0

            _, pcm16 = ensure_sample_rate(ORIG_SR, pcm)

            waveform = tf.convert_to_tensor(pcm16, dtype=tf.float32)
            scores, _, _ = model(waveform)
            mean_scores = tf.reduce_mean(scores, axis=0).numpy()

            # find all scores above THRESH
            flagged_idxs = np.where(mean_scores > THRESH)[0]
            for idx in flagged_idxs:
                print(f"Detected: {class_names[idx]} (score={mean_scores[idx]:.2f})")

            # compute numeric danger score [0..1] from weights × confidence
            danger_score = sum(
                DANGEROUS_SOUNDS[class_names[i]] * float(mean_scores[i])
                for i in flagged_idxs
                if class_names[i] in DANGEROUS_SOUNDS
            )
            danger_score = min(danger_score, 1.0)
            if danger_score > 0:
                publish_detection(danger_score)

except KeyboardInterrupt:
    print("Interrupted by user")

finally:
    conn.close()
    s.close()
    print("Server shut down")