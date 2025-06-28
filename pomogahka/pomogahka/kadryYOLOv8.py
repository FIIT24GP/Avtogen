import cv2
import numpy as np
import os
import logging
from skimage.metrics import structural_similarity as ssim

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("keyframe_detection.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def preprocess_frame(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (640, 360), interpolation=cv2.INTER_AREA)
    return resized

def compare_frames(frame1, frame2, threshold=0.93):
    score, _ = ssim(frame1, frame2, full=True)
    return score < threshold

def detect_keyframes(video_path, output_dir="keyframes", ssim_threshold=0.93, frame_interval=1):
    if not os.path.exists(video_path):
        logging.error(f"Видеофайл {video_path} не найден")
        return []

    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logging.error(f"Не удалось открыть видеофайл {video_path}")
        return []

    keyframes = []
    prev_frame = None
    frame_count = 0
    keyframe_idx = 0

    fps = cap.get(cv2.CAP_PROP_FPS)
    interval_frames = int(fps * frame_interval)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % interval_frames == 0:
            processed_frame = preprocess_frame(frame)

            if prev_frame is None or compare_frames(prev_frame, processed_frame, ssim_threshold):
                keyframe_path = os.path.join(output_dir, f"keyframe_{keyframe_idx}.png")
                cv2.imwrite(keyframe_path, frame)
                keyframes.append({
                    "frame_idx": frame_count,
                    "path": keyframe_path,
                    "timestamp": frame_count / fps
                })
                logging.info(f"Сохранен ключевой кадр {keyframe_idx} на {frame_count / fps:.2f} сек")
                keyframe_idx += 1
                prev_frame = processed_frame

        frame_count += 1

    cap.release()
    logging.info(f"Обработка завершена. Найдено {keyframe_idx} ключевых кадров")
    return keyframes

import shutil
import os

def filter_nearby_keyframes(keyframes, min_time_gap=1.5, output_dir="filtered_keyframes"):
    """
    Фильтрует ключевые кадры, оставляя только первый и последний из близкорасположенных,
    и копирует их в новую директорию.
    """
    if not keyframes:
        return []

    os.makedirs(output_dir, exist_ok=True)

    filtered = [keyframes[0]]
    group = [keyframes[0]]

    for i in range(1, len(keyframes)):
        delta = keyframes[i]['timestamp'] - group[-1]['timestamp']
        if delta < min_time_gap:
            group.append(keyframes[i])
        else:
            if len(group) > 2:
                filtered.append(group[-1])
            elif len(group) == 2:
                filtered.append(group[1])
            group = [keyframes[i]]
            filtered.append(keyframes[i])

    if len(group) > 2:
        filtered.append(group[-1])
    elif len(group) == 2:
        filtered.append(group[1])

    # Удаление дубликатов по frame_idx
    seen = set()
    final = []
    for f in filtered:
        if f['frame_idx'] not in seen:
            new_path = os.path.join(output_dir, os.path.basename(f['path']))
            shutil.copyfile(f['path'], new_path)
            final.append({
                "frame_idx": f['frame_idx'],
                "timestamp": f['timestamp'],
                "path": new_path
            })
            seen.add(f['frame_idx'])

    return final



# Пример вызова
if __name__ == "__main__":
    video_path = "lecture1.mp4"
    keyframes = detect_keyframes(video_path, ssim_threshold=0.93, frame_interval=1)

    filtered_keyframes = filter_nearby_keyframes(keyframes, min_time_gap=2, output_dir="filtered_keyframes")

    for kf in filtered_keyframes:
        print(f"{kf['timestamp']:.2f} сек — {kf['path']}")

    for kf in keyframes:
        print(f"{kf['timestamp']:.2f} сек — {kf['path']}")
