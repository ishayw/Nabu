"""
Create a 2-second silence WAV file for testing short recording handling.
"""
import numpy as np
import soundfile as sf

# Generate 2 seconds of silence
sample_rate = 44100
duration = 2.0
samples = int(sample_rate * duration)
silence = np.zeros(samples)

# Save as WAV
output_file = "recordings/test_short_silence.wav"
sf.write(output_file, silence, sample_rate)

print(f"Created {output_file}: {duration} seconds of silence")
print(f"Sample rate: {sample_rate} Hz")
print(f"Samples: {samples}")
