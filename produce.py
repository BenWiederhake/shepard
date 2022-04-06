#!/usr/bin/env python3

from pydub import AudioSegment
from pydub.effects import normalize

import math
import struct
import time

SAMPLE_FORMAT = struct.Struct('<i')
SAMPLE_WIDTH = SAMPLE_FORMAT.size
assert SAMPLE_WIDTH == 4
SAMPLE_RATE = 48000
SHEPHERD_PERIOD_SAMPLES = SAMPLE_RATE * 5  # 5 seconds


def make_waveform():
    return [round(1e3 * math.sin(t * 2 * math.pi * 440 / SAMPLE_RATE)) for t in range(SHEPHERD_PERIOD_SAMPLES)]  # FIXME


def save_waveform(waveform):
    data = b''.join(SAMPLE_FORMAT.pack(sample) for sample in waveform)
    segment = AudioSegment(data, sample_width=SAMPLE_WIDTH, frame_rate=SAMPLE_RATE, channels=1)
    print(segment[:2].get_array_of_samples())
    segment = normalize(segment, headroom=10)
    print(segment[:2].get_array_of_samples())
    filename = time.strftime(f'shepherd_w={SAMPLE_WIDTH}_r={SAMPLE_RATE}_d={SHEPHERD_PERIOD_SAMPLES / SAMPLE_RATE}_t=%s.flac')
    print(f'Saving to {filename}')
    segment.export(filename, 'flac')


def run():
    waveform = make_waveform()
    save_waveform(waveform)


if __name__ == '__main__':
    run()
