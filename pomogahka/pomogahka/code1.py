import os
import shutil
import subprocess
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import Cm

from pydub import AudioSegment
from pprint import pprint
import math

import time

import os

base_dir = os.path.dirname(__file__)
path = os.path.join(base_dir, "audio", "nina")
path_result = os.path.join(base_dir, "audio", "nina", "result")

text = []
name_old_folder = 'result'

# path = "/audio/nina/"
# path_result = "/audio/nina/result/"

#path_msi = 'C:\\Program Files (x86)\\MSI Afterburner\\'

files = os.listdir(path)

name_file = "123.m4a"

#os.chdir(path_msi)
#os.system('MSIAfterburner.exe -profile1')
os.chdir(path)


start = time.time()

audio = AudioSegment.from_file(name_file)
time_min = audio.duration_seconds / 60
frac, whole = math.modf(time_min)
time_sec = frac * 60
pprint({'time_sound': str(int(whole)) + ' минут ' + str(int(time_sec)) + ' секунд'})

filename, file_extension = os.path.splitext(name_file)
whisper = "whisper --language ru --model large-v3 -o ./result -- "
code_str = whisper + '"{}"'.format(name_file)

process = subprocess.Popen(
    code_str,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    shell=True,
    encoding='utf-8',
    errors='replace'
)

while True:
    realtime_output = process.stdout.readline()
    if realtime_output == '' and process.poll() is not None:
        break
    if realtime_output:
        print(realtime_output.strip(), flush=True)


with open(path_result + filename + '.txt', encoding="utf8") as f:
    contents = f.read()
    text.append(contents.replace("\n", " "))

with open(path_result + filename + "2.txt", "w", encoding='utf-8') as output:
    output.write(str(text[0]))

document = Document()
sections = document.sections
for section in sections:
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(3)
    section.right_margin = Cm(1.5)

p = document.add_paragraph(text)
style = document.styles['Normal']
p.style.font.name = 'Times New Roman'
p.style.font.size = Pt(14)
p.paragraph_format.line_spacing = 1.5
p.style.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY

document.save(path_result + filename + ".docx")
os.rename(path + name_old_folder, path + filename)

os.chdir(path)
filename, file_extension = os.path.splitext(name_file)
# os.system('ffmpeg -i ' + name_file + ' -ar 48000 -ac 2 -ab 128000 -f wav ' + filename + '.wav')
os.system('ffmpeg -i ' + '"{}"'.format(name_file) + ' ' + '"{}"'.format(filename) + '.flac')

shutil.make_archive(path + filename, 'zip', path + filename)

end = time.time()
time_code_min = (end - start) / 60
frac_code, whole_code = math.modf(time_code_min)
time_code_sec = frac_code * 60
pprint({'Время работы:': str(int(whole_code)) + ' минут ' + str(int(time_code_sec)) + ' секунд'})

#os.chdir(path_msi)
#os.system('MSIAfterburner.exe -profile2')