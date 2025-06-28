import subprocess
import re

# Путь к вашему видео
video_path = 'newlecture.mp4'


# Имя файла для сохранения таймингов
timings_file = 'frame_change_timings.txt'

# Команда ffmpeg для анализа изменений кадров
ffmpeg_command = [
    'ffmpeg',
    '-i', video_path,
    '-vf', 'select=gt(scene\,0.7),showinfo',
    '-f', 'null',
    '-'
]

# Выполнение команды и сбор stdout/stderr
process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
stdout, stderr = process.communicate()

# Регулярное выражение для поиска строк showinfo с кадрами
showinfo_pattern = re.compile(r"showinfo.*n:\s*(\d+).*pts_time:\s*([\d\.]+)")

# Список для хранения таймингов
timings = []

# Обработка вывода ffmpeg
for line in stderr.splitlines():
    match = showinfo_pattern.search(line)
    if match:
        frame_number = int(match.group(1))
        pts_time = float(match.group(2))
        # Можно фильтровать по сцене или по другим параметрам
        # Для простоты записываем все
        timings.append(pts_time)

# Запись таймингов в файл
with open(timings_file, 'w') as f:
    if timings:
        for t in sorted(timings):
            f.write(f"{t}\n")
        print(f"Найдено {len(timings)} смен кадров. Тайминги сохранены в {timings_file}")
    else:
        print("Тайминги смены кадров не найдены.")