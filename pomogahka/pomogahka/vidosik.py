import whisper
import cv2
import pytesseract
import json
from transformers import pipeline
import os

# Загрузка модели Whisper для транскрипции
model = whisper.load_model("base")

# Создаем конвейер для суммаризации один раз
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def extract_audio(video_path, audio_path):
    """Извлечение аудиодорожки из видеофайла."""
    # Используем ffmpeg для извлечения аудио
    command = f"ffmpeg -i {video_path} -vn -acodec mp3 {audio_path} -y"
    result = os.system(command)
    if result != 0:
        raise Exception("Ошибка при извлечении аудио с помощью ffmpeg")
    return audio_path

def convert_video_to_m4a(video_path, audio_path):
    """Конвертация видео в аудио формат m4a."""
    m4a_path = os.path.splitext(audio_path)[0] + ".m4a"
    command = f"ffmpeg -i {video_path} -vn -c:a aac {m4a_path} -y"
    result = os.system(command)
    if result != 0:
        raise Exception("Ошибка при конвертации видео в m4a")
    return m4a_path

def transcribe_audio(audio_path):
    """Транскрипция аудио с использованием Whisper."""
    result = model.transcribe(audio_path)
    return result["text"]

def extract_formulas(frame):
    """Распознавание формул на кадре видео с использованием OCR."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray, config='--psm 6')
    return text

# def generate_summary(text):
#     """Генерация краткого конспекта с использованием модели BART."""
#     summary = summarizer(text, max_length=150, min_length=50, do_sample=False)
#     return summary[0]["summary_text"]

def generate_summary(text, max_length=150, min_length=50):
    """Генерация краткого конспекта с использованием модели BART."""
    try:
        summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
        return summary[0]["summary_text"]
    except Exception as e:
        print(f"Ошибка при генерации суммаризации: {e}")
        return ""


def process_lesson(video_path):
    """Основная функция обработки видеоурока."""
    temp_audio_path = "temp_audio.mp3"
    # Извлечение аудио
    extract_audio(video_path, temp_audio_path)
    # Транскрипция
    transcript = transcribe_audio(temp_audio_path)
    # Генерация конспекта
    # summary = generate_summary(transcript)
    # Сохранение результатов
    output = {
        "transcript": transcript,
         "summary": ""
    }
    with open("lesson_output.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    return output

if __name__ == "__main__":
    video_file = "lecture.mp4"
    os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
    result = process_lesson(video_file)
    print("Конспект:", result["summary"])