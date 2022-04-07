#!/usr/bin/env python3

from pydub import AudioSegment
from pydub.effects import normalize

import math
from mpmath import sinpi as slow_sinpi
import struct
import time

SAMPLE_FORMAT = struct.Struct('<i')
SAMPLE_WIDTH = SAMPLE_FORMAT.size
assert SAMPLE_WIDTH == 4
SAMPLE_RATE = 48000
SHEPHERD_PERIOD_SAMPLES = SAMPLE_RATE * 5  # 5 seconds

SHEPERD_BASE_FREQUENCY = 330  # Goes up an octave


def sinpi(x):
    # Slow:
    # return slow_sinpi(x)
    # Fast but slightly inaccurate:
    return math.sin(math.pi * x)


def compute_integer_place_near_1(coefficient):
    # Assume f(x) = coefficient * (2 ** x - 1)
    # We want to find an x close to 1 such that f(x) is integer.
    y_up = math.ceil(coefficient)
    x_up = math.log2(y_up / coefficient + 1)
    y_down = math.floor(coefficient)
    x_down = math.log2(y_down / coefficient + 1)
    assert 0.9 < x_down <= 1 <= x_up < 1.1, (coefficient, x_down, x_up)
    # Because x will end up multiplicative, we can't just compare (x_up - 1) and (1 - x_down)
    error_up = x_up / 1
    error_down = 1 / x_down
    #print(f'y={y_down}/{y_up}, x={x_down}/{x_up}, error={error_down}/{error_up}')
    if error_up < error_down:
        return x_up
    else:
        return x_down


def make_waveform():
    additional_samples = 0.0  # FIXME, can be negative, can be fractional
    waveform = []
    base_coefficient = SHEPERD_BASE_FREQUENCY * SHEPHERD_PERIOD_SAMPLES / (SAMPLE_RATE * math.log(2))
    extra_time = compute_integer_place_near_1(base_coefficient) - 1
    for t in range(SHEPHERD_PERIOD_SAMPLES):  # Integer in [0, SHEPHERD_PERIOD_SAMPLES). Unit: samples
        t_0_1 = t / SHEPHERD_PERIOD_SAMPLES  # Real in [0, 1). Unit: fraction of whole waveform
        t_real_0_1 = t_0_1 + (-2 * t_0_1 + 3) * t_0_1 * t_0_1 * extra_time  # Real in [0, 1±epsilon). Unit: fraction of whole waveform
        phase = base_coefficient * 2 * (2 ** t_real_0_1 - 1)
        waveform.append(round(1e6 * sinpi(phase)))
    print(f'Final phase: {phase}')

    return waveform


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
