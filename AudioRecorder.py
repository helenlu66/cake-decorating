import pyaudio
import wave
import keyboard
import threading
import time
import yaml

class AudioRecorder:
    def __init__(self,  record_len = 10, chunk_size=1024, sample_format=pyaudio.paInt16, channels=1, rate=44100):
        self.record_len = record_len
        self.chunk_size = chunk_size
        self.sample_format = sample_format
        self.channels = channels
        self.rate = rate
        self.frames = []
        self.is_recording = False
        self.p = pyaudio.PyAudio()

    def record_human_speech(self, filepath):
        p = pyaudio.PyAudio()

        stream = p.open(format=self.sample_format,
                        channels=self.channels,
                        rate=self.rate,
                        input=True,
                        frames_per_buffer=self.chunk_size)


        print("Recording...")

        frames = []  # Initialize array to store frames

        # Store data in chunks 
        start_time = time.time()
        while True:
            data = stream.read(self.chunk_size)
            frames.append(data)
            if time.time() - start_time >= self.record_len:
                break
        # Stop and close the stream 
        stream.stop_stream()
        stream.close()
        # Terminate the PortAudio interface
        p.terminate()

        print("Finished recording.")

        stream.stop_stream()
        stream.close()
        p.terminate()

        # Save the recorded audio to a temporary WAV file
        wf = wave.open(filepath, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(self.sample_format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))

        return filepath
    
    def start_recording(self):
        self.stream = self.p.open(format=self.sample_format,
                                  channels=self.channels,
                                  rate=self.rate,
                                  frames_per_buffer=self.chunk_size,
                                  input=True)
        self.is_recording = True
        print("Recording...")

        while self.is_recording:
            data = self.stream.read(self.chunk_size)
            self.frames.append(data)

    def stop_recording(self):
        self.is_recording = False
        print("Recording stopped.")
        self.stream.stop_stream()
        self.stream.close()

        wf = wave.open(self.filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.p.get_sample_size(self.sample_format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        print("Audio saved as {}".format(self.filename))

    def on_key_event(self, event):
        if event.name == 'r' and event.event_type == keyboard.KEY_DOWN:
            self.start_recording()
        elif event.name == 's' and event.event_type == keyboard.KEY_DOWN:
            self.stop_recording()

def load_experiment_config(filename):
    with open(filename, 'r') as yaml_file:
        yaml_data = yaml_file.read()
    yaml_config = yaml.safe_load(yaml_data)
    return yaml_config


if __name__ == "__main__":
    exp_config = load_experiment_config('experiment_config.yaml')
    recorder = AudioRecorder(record_len=exp_config['human_speech_record_len'])
    recorder.record_human_speech('test_record.wav')

