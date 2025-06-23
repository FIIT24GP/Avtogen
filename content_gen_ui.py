import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLineEdit, QListWidget, QLabel
)

# Предзаданные данные на тему нейросетей
INITIAL_PROMPT = "Что такое нейронные сети?"
SHORT_THESES = [
    "Определение нейронной сети",
    "Области применения нейросетей",
    "Типы нейронных сетей"
]
SLIDE_TEXTS = {
    "Определение нейронной сети": "Нейронная сеть — это математическая модель, построенная по аналогии с работой биологических нейронов.",
    "Области применения нейросетей": "Нейронные сети применяются в распознавании образов, обработке естественного языка и медицинской диагностике.",
    "Типы нейронных сетей": "Основные типы нейросетей включают свёрточные, рекуррентные и полносвязные сети."
}
LECTURE_TEXTS = {
    "Нейронная сеть — это математическая модель, построенная по аналогии с работой биологических нейронов.": (
        "Нейронные сети состоят из связанных между собой искусственных нейронов, которые могут обучаться на основе входных данных. "
        "Они способны выявлять сложные зависимости и закономерности, что позволяет решать задачи классификации, регрессии и прогнозирования."
    ),
    "Нейронные сети применяются в распознавании образов, обработке естественного языка и медицинской диагностике.": (
        "Современные нейронные сети эффективно используются для распознавания изображений и речи. "
        "В медицине они помогают диагностировать заболевания на ранних стадиях и интерпретировать сложные данные обследований."
    ),
    "Основные типы нейросетей включают свёрточные, рекуррентные и полносвязные сети.": (
        "Свёрточные сети применяются в обработке изображений, рекуррентные сети используются для анализа временных рядов и текстов, а полносвязные сети — для широкого спектра задач, где важны сложные нелинейные связи."
    )
}


class ContentGenerationGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Генерация контента лекции")
        self.resize(600, 600)

        layout = QVBoxLayout()

        self.prompt_input = QLineEdit()
        self.prompt_input.setText(INITIAL_PROMPT)
        self.generate_btn = QPushButton("Генерировать")

        layout.addWidget(self.prompt_input)
        layout.addWidget(self.generate_btn)

        layout.addWidget(QLabel("Короткие тезисы:"))
        self.theses_list = QListWidget()
        self.theses_list.addItems(SHORT_THESES)
        self.generate_from_thesis_btn = QPushButton("Генерировать по тезису")

        layout.addWidget(self.theses_list)
        layout.addWidget(self.generate_from_thesis_btn)

        layout.addWidget(QLabel("Текст слайда:"))
        self.slide_text_list = QListWidget()
        self.generate_lecture_text_btn = QPushButton("Генерировать текст лекции")

        layout.addWidget(self.slide_text_list)
        layout.addWidget(self.generate_lecture_text_btn)

        layout.addWidget(QLabel("Текст лекции:"))
        self.lecture_text_list = QListWidget()

        layout.addWidget(self.lecture_text_list)

        self.setLayout(layout)

        # Подключение сигналов
        self.generate_btn.clicked.connect(self.generate_theses)
        self.generate_from_thesis_btn.clicked.connect(self.generate_slide_text)
        self.generate_lecture_text_btn.clicked.connect(self.generate_lecture_text)

    def generate_theses(self):
        self.theses_list.clear()
        self.theses_list.addItems(SHORT_THESES)

    def generate_slide_text(self):
        selected = self.theses_list.currentItem()
        if selected:
            text = SLIDE_TEXTS.get(selected.text(), "Текст не найден.")
            self.slide_text_list.clear()
            self.slide_text_list.addItem(text)

    def generate_lecture_text(self):
        selected = self.slide_text_list.currentItem()
        if selected:
            text = LECTURE_TEXTS.get(selected.text(), "Текст не найден.")
            self.lecture_text_list.clear()
            self.lecture_text_list.addItem(text)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ContentGenerationGUI()
    window.show()
    sys.exit(app.exec_())
