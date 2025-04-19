#!/usr/bin/env python3
import csv
import tensorflow as tf
import tensorflow_hub as hub

def main():
    model = hub.load('https://tfhub.dev/google/yamnet/1')
    class_map_path = model.class_map_path().numpy().decode('utf-8')

    with tf.io.gfile.GFile(class_map_path) as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            print(f"{idx:03d}: {row['display_name']}")

if __name__ == '__main__':
    main()