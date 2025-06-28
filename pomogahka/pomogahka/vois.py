import re

import torch
import torchaudio
import textwrap

# Константы голосов
SPEAKER_AIDAR = "aidar"
SPEAKER_BAYA = "baya"
SPEAKER_KSENIYA = "kseniya"
SPEAKER_XENIA = "xenia"
SPEAKER_RANDOM = "random"

# Константы устройств
DEVICE_CPU = "cpu"
DEVICE_CUDA = "cuda"


class TTS:
    def __init__(
        self,
        speaker: str = SPEAKER_AIDAR,
        device: str = DEVICE_CUDA,
        samplerate: int = 48000
    ):
        self.model, _ = torch.hub.load(
            repo_or_dir="snakers4/silero-models",
            model="silero_tts",
            language="ru",
            put_accent=True,
            speaker="ru_v3"
        )


        self.device = torch.device(device)
        self.model.to(self.device)
        self.speaker = speaker
        self.samplerate = samplerate

    # def text2speech(self, text: str, output_path: str):
    #     chunks = textwrap.wrap(text, 150, break_long_words=False)
    #     audios = []
    #
    #     for i, chunk in enumerate(chunks, 1):
    #         try:
    #             audio = self.model.apply_tts(
    #                 text=chunk,
    #                 speaker=self.speaker,
    #                 sample_rate=self.samplerate,
    #                 put_accent=True,
    #                 put_yo=True
    #             )
    #             audios.append(audio)
    #         except Exception:
    #             print(f"Ошибка при обработке части {i}: Model couldn't generate your text, probably it's too long")
    #
    #     if audios:
    #         full_audio = torch.cat(audios)
    #         torchaudio.save(output_path, full_audio.unsqueeze(0), self.samplerate)
    #     else:
    #         raise RuntimeError("Ни одна часть текста не была успешно озвучена.")
    def text2speech(self, text: str, output_path: str):
        # Разбиение по предложениям
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        audios = []

        for i, sentence in enumerate(sentences, 1):
            try:
                audio = self.model.apply_tts(
                    text=sentence,
                    speaker=self.speaker,
                    sample_rate=self.samplerate,
                    put_accent=True,
                    put_yo=True
                )
                audios.append(audio)
            except Exception:
                print(f"Ошибка при обработке предложения {i}: Model couldn't generate your text")

        if audios:
            full_audio = torch.cat(audios)
            torchaudio.save(output_path, full_audio.unsqueeze(0), self.samplerate)
        else:
            raise RuntimeError("Ни одно предложение не было успешно озвучено.")

if __name__ == '__main__':
    tts = TTS(speaker=SPEAKER_XENIA, device=DEVICE_CUDA, samplerate=48000)

    with open('transcript.txt', 'r', encoding='utf-8') as f:
        text = f.read().strip()

    tts.text2speech(text, 'speech.wav')
