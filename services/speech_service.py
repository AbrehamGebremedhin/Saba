
import asyncio
from kokoro import KPipeline
import soundfile as sf
import speech_recognition as sr

class AsyncSpeechService:
    def __init__(self, lang_code='a', voice='bf_alice'):
        self.pipeline = KPipeline(lang_code=lang_code)
        self.voice = voice

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

    def listen(self):
        """
        Listens to the microphone and returns the recognized speech as text.
        Requires the 'speech_recognition' library.
        """
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                print("Listening...")
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                # recognizer.dynamic_energy_threshold = True
                recognizer.energy_threshold = 400
                audio = recognizer.listen(source)
                try:
                    print("Recognizing...")
                    return recognizer.recognize_google(audio)
                except sr.UnknownValueError:
                    return None
        except sr.WaitTimeoutError:
            print("Listening timed out - no speech detected.")
            return None
        except Exception as e:
            print(f"Error accessing microphone: {e}")
            return None
            
        try:
            text = recognizer.recognize_google(audio)
            print(f"Recognized: {text}")
            return text
        except sr.UnknownValueError:
            print("Could not understand audio.")
            return None
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            return None
        