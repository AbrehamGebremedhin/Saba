
import asyncio
from kokoro import KPipeline
import soundfile as sf
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import sounddevice as sd
import numpy as np
import queue

class AsyncSpeechService:
    def __init__(self, lang_code='a', voice='bf_alice'):
        self.pipeline = KPipeline(lang_code=lang_code)
        self.voice = voice
        
        # Initialize Whisper model
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        
        model_id = "openai/whisper-large-v3"
        print(f"Device set to use {self.device}")
        
        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id, torch_dtype=self.torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
        ).to(self.device)
        self.processor = AutoProcessor.from_pretrained(model_id)
        
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=self.model,
            tokenizer=self.processor.tokenizer,
            feature_extractor=self.processor.feature_extractor,
            torch_dtype=self.torch_dtype,
            device=self.device
        )
        self.pipe.model.eval()
        
        # Audio config
        self.samplerate = 16000
        self.channels = 1
        self.block_duration = 0.5
        self.silence_threshold = 0.01
        self.silence_duration_end = 1.0
        self.MIN_SPEECH_DURATION = 1.0

    async def synthesize(self, text: str, output_prefix: str = "output"):
        loop = asyncio.get_event_loop()
        generator = self.pipeline(text, voice=self.voice)
        tasks = []
        for i, (gs, ps, audio) in enumerate(generator):
            print(i, gs, ps)
            # Write audio asynchronously
            task = loop.run_in_executor(None, sf.write, f'output.wav', audio, 24000)
            tasks.append(task)
        await asyncio.gather(*tasks)

    def audio_callback(self, indata, frames, time_, status):
        if status:
            print(status)
        self.q.put(indata.copy())

    def is_speech(self, audio, threshold=None):
        if threshold is None:
            threshold = self.silence_threshold
        return np.mean(np.abs(audio)) > threshold

    def listen(self):
        """
        Listens to the microphone and returns the recognized speech as text.
        Uses Whisper model for speech recognition.
        """
        self.q = queue.Queue()
        
        print("Listening... Press Ctrl+C to stop.")
        try:
            with sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                callback=self.audio_callback,
                blocksize=int(self.samplerate * self.block_duration)
            ):
                speech_buffer = []
                recording = False
                silence_blocks = 0

                while True:
                    audio_block = self.q.get()
                    audio_np = np.squeeze(audio_block)

                    if self.is_speech(audio_np):
                        speech_buffer.append(audio_np)
                        recording = True
                        silence_blocks = 0
                    elif recording:
                        silence_blocks += 1
                        speech_buffer.append(audio_np)

                        if silence_blocks * self.block_duration >= self.silence_duration_end:
                            chunk = np.concatenate(speech_buffer)
                            speech_buffer = []
                            recording = False

                            duration = len(chunk) / self.samplerate
                            if duration >= self.MIN_SPEECH_DURATION:
                                print("Processing speech...")
                                result = self.pipe(
                                    chunk,
                                    return_timestamps=True,
                                    generate_kwargs={"language": "en"}
                                )
                                text = result.get("text")
                                print("Transcription:", text)
                                return text
                            else:
                                print("[Too short, skipping transcription]")

        except KeyboardInterrupt:
            print("Stopped listening.")
            return None
        except Exception as e:
            print(f"Error during speech recognition: {e}")
            return None
        