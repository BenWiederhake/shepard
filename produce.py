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
# Corresponds to 60dB
DYNAMIC_RANGE = 1000
DYNAMIC_RANGE_LOG2 = math.log2(DYNAMIC_RANGE)
SHEPHERD_PERIOD_SAMPLES = SAMPLE_RATE * 5  # 5 seconds
SHEPHERD_OVERTONE_POWERS = [1, 2, 4, 8]
SHEPHERD_OVERTONE_MAXPOWER = 8

SHEPHERD_BASE_FREQUENCY = 220  # Goes up an octave


def sin_two_pi(x):
    # Slow:
    # return slow_sinpi(2 * x)
    # Fast but slightly inaccurate:
    # return math.sin(2 * math.pi * x)
    # Let's go with triangles instead:
    effective_phase = x % 1
    if effective_phase < 0.5:
        return effective_phase
    else:
        return 1 - effective_phase


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


def amplitude_at(frequency):
    if frequency < SHEPHERD_BASE_FREQUENCY:
        return 0
    if frequency < 2 * SHEPHERD_BASE_FREQUENCY:
        factor = frequency / SHEPHERD_BASE_FREQUENCY
        # The idea is this:
        #     progress = math.log2(factor)
        #     return (1 / DYNAMIC_RANGE) * exp(ln(DYNAMIC_RANGE) * progress)
        # However, this can be simplified:
        return factor ** DYNAMIC_RANGE_LOG2 / DYNAMIC_RANGE

    if frequency > 2 * SHEPHERD_OVERTONE_MAXPOWER * SHEPHERD_BASE_FREQUENCY:
        return 0
    if frequency > SHEPHERD_OVERTONE_MAXPOWER * SHEPHERD_BASE_FREQUENCY:
        factor = (2 * SHEPHERD_OVERTONE_MAXPOWER * SHEPHERD_BASE_FREQUENCY) / frequency
        return factor ** DYNAMIC_RANGE_LOG2 / DYNAMIC_RANGE

    return 1


def make_waveform():
    additional_samples = 0.0  # FIXME, can be negative, can be fractional
    waveform = []
    base_coefficient = SHEPHERD_BASE_FREQUENCY * SHEPHERD_PERIOD_SAMPLES / (SAMPLE_RATE * math.log(2))
    actual_time = compute_integer_place_near_1(base_coefficient)
    for t in range(SHEPHERD_PERIOD_SAMPLES):  # Integer in [0, SHEPHERD_PERIOD_SAMPLES). Unit: samples
        t_0_1 = t / SHEPHERD_PERIOD_SAMPLES  # Real in [0, 1). Unit: fraction of whole waveform
        t_real_0_1 = t_0_1 * actual_time  # Real in [0, 1±epsilon). Unit: fraction of whole waveform
        phase = base_coefficient * (2 ** t_real_0_1 - 1)
        claimed_frequency = SHEPHERD_BASE_FREQUENCY * (2 ** t_0_1)
        akku = 0
        for power in SHEPHERD_OVERTONE_POWERS:
            akku += sin_two_pi(phase * power) * amplitude_at(claimed_frequency * power)
        waveform.append(round(1e8 * akku))
    print(f'Final phase: {phase}, final freq: {claimed_frequency}, time factor {actual_time}, frequencies are thus off by {math.log2(actual_time) * 1200:+} cents.')

    return waveform


def save_waveform(waveform):
    data = b''.join(SAMPLE_FORMAT.pack(sample) for sample in waveform)
    segment = AudioSegment(data, sample_width=SAMPLE_WIDTH, frame_rate=SAMPLE_RATE, channels=1)
    # print(segment[:2].get_array_of_samples())
    segment = normalize(segment, headroom=10)
    # print(segment[:2].get_array_of_samples())
    filename = time.strftime(f'shepherd_w={SAMPLE_WIDTH}_r={SAMPLE_RATE}_d={SHEPHERD_PERIOD_SAMPLES / SAMPLE_RATE}_t=%s.flac')
    print(f'Saving to {filename}')
    segment.export(filename, 'flac')


def run():
    # print('amp sanity check:', [(factor, amplitude_at(SHEPHERD_BASE_FREQUENCY * factor)) for factor in [1, 1.3, 1.8, 2, 2.1, 4, 7.9, 8.0, 8.1, 12, 15, 16]])
    waveform = make_waveform()
    save_waveform(waveform)


if __name__ == '__main__':
    run()
