import os
import docx2txt
from opensearchpy import OpenSearch
from sentence_transformers import SentenceTransformer
import logging
import uuid

# --- Настройка логгирования ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Подключение к OpenSearch ---
client = OpenSearch(
    hosts=[{'host': 'localhost', 'port': 9200}],
    http_auth=None,  # Укажи (username, password), если включен security
    use_ssl=False,
    verify_certs=False
)

# --- Загружаем модель для эмбеддингов ---
model = SentenceTransformer("sentence-transformers/LaBSE")

# --- Название индекса ---
INDEX_NAME = "semantic-docs-v2"

# --- Создание индекса с KNN (если нужно) ---
def create_index():
    if client.indices.exists(INDEX_NAME):
        logging.info(f"Индекс '{INDEX_NAME}' уже существует — пропускаем создание.")
        return

    index_body = {
        "settings": {
            "index": {
                "knn": True
            }
        },
        "mappings": {
            "properties": {
                "filename": {"type": "keyword"},
                "paragraph": {"type": "text"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": 768,
                    "method": {
                        "name": "hnsw",
                        "engine": "faiss",
                        "space_type": "cosinesimil"
                    }
                }
            }
        }
    }

    client.indices.create(index=INDEX_NAME, body=index_body)
    logging.info(f"Создан индекс '{INDEX_NAME}'.")

# --- Извлечение текста из .docx файлов ---
def extract_texts_from_folder(folder_path="analitika\\"):
    texts = {}
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".docx"):
            path = os.path.join(folder_path, filename)
            try:
                text = docx2txt.process(path).strip()
                if text:
                    texts[filename] = text
                    logging.info(f"[✓] Извлечён текст из: {filename}")
                else:
                    logging.warning(f"[!] Пустой файл: {filename}")
            except Exception as e:
                logging.error(f"[✗] Ошибка при обработке {filename}: {e}")
    return texts

# --- Разбиение текста на абзацы ---
def split_into_paragraphs(text):
    return [p.strip() for p in text.split("\n\n") if p.strip()]

# --- Индексация абзацев в OpenSearch ---
def index_paragraphs(texts_dict):
    for filename, full_text in texts_dict.items():
        paragraphs = split_into_paragraphs(full_text)
        for i, para in enumerate(paragraphs):
            try:
                embedding = model.encode(para)
                doc_id = str(uuid.uuid4())
                doc = {
                    "filename": filename,
                    "paragraph": para,
                    "embedding": embedding.tolist()
                }
                client.index(index=INDEX_NAME, id=doc_id, body=doc)
                logging.info(f"Индексирован абзац {i + 1}/{len(paragraphs)} из {filename}")
            except Exception as e:
                logging.error(f"Ошибка при индексации абзаца: {e}")

# --- Запуск всего пайплайна ---
if __name__ == "__main__":
    create_index()
    texts = extract_texts_from_folder("analitika")
    index_paragraphs(texts)
    logging.info("Индексация завершена.")
