import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import sounddevice as sd
import numpy as np
import queue

# ===== Model & Device Config =====
device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

model_id = "openai/whisper-large-v3"
print(f"Device set to use {device}")

model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
).to(device)
processor = AutoProcessor.from_pretrained(model_id)

pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    torch_dtype=torch_dtype,
    device=device
)
pipe.model.eval()  # Slight efficiency boost

# ===== Audio Config =====
samplerate = 16000
channels = 1
block_duration = 0.5  # seconds per chunk
silence_threshold = 0.01
silence_duration_end = 1.0  # seconds before we decide you stopped talking
MIN_SPEECH_DURATION = 1.0  # seconds before we send to Whisper

# ===== Queue for audio stream =====
q = queue.Queue()

def audio_callback(indata, frames, time_, status):
    if status:
        print(status)
    q.put(indata.copy())

def is_speech(audio, threshold=silence_threshold):
    return np.mean(np.abs(audio)) > threshold

# ===== Main Listening Loop =====
print("Listening... Press Ctrl+C to stop.")
try:
    with sd.InputStream(
        samplerate=samplerate,
        channels=channels,
        callback=audio_callback,
        blocksize=int(samplerate * block_duration)
    ):
        speech_buffer = []
        recording = False
        silence_blocks = 0

        while True:
            audio_block = q.get()
            audio_np = np.squeeze(audio_block)

            if is_speech(audio_np):
                speech_buffer.append(audio_np)
                recording = True
                silence_blocks = 0
            elif recording:
                silence_blocks += 1
                speech_buffer.append(audio_np)

                if silence_blocks * block_duration >= silence_duration_end:
                    chunk = np.concatenate(speech_buffer)
                    speech_buffer = []
                    recording = False

                    duration = len(chunk) / samplerate
                    if duration >= MIN_SPEECH_DURATION:
                        print("Processing speech...")
                        result = pipe(
                            chunk,
                            return_timestamps=True,
                            generate_kwargs={"language": "en"}  # Force English
                        )
                        print("Transcription:", result.get("text"))
                    else:
                        print("[Too short, skipping transcription]")

except KeyboardInterrupt:
    print("Stopped listening.")
