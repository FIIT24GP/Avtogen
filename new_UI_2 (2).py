import csv
import os
import subprocess
import time
import threading
import logging
import numpy as np

import streamlit as st
import psutil
import pynvml
from prometheus_client import Gauge, start_http_server, REGISTRY
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# === CONFIG ===
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "hf.co/t-tech/T-lite-it-1.0-Q8_0-GGUF:Q8_0"
model_path = r"E:\ollama_chat\models\intfloat\multilingual-e5-large"
CSV_LOG = "E:\\ollama_chat\\analitika_history2.csv"
RAISS_DB = ['analitika_docx_pdf_html_v2', 'analitika1', 'analitika3', 'weld_tks_v1']
GRAFANA_LOGS_URL = "http://localhost:3003/d/34e0395a-530e-428f-bbca-4465ccce4c46/prometheus-logs"
APP_LOG_FILE = "E:\\ollama_chat\\resource_usage.log"

# Настройка логирования в файл
logging.basicConfig(
    filename=APP_LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# Настройка страницы Streamlit
st.set_page_config(page_title="RAG с FAISS и Ollama", layout="wide")

# Скрываем лишние элементы Streamlit и добавляем кастомный стиль
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    .answer-box {
        background-color: #333333;
        color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #555;
        font-size: 16px;
        line-height: 1.6;
    }
    @keyframes blink {
        50% { opacity: 0; }
    }
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# Инициализация pynvml для GPU
try:
    pynvml.nvmlInit()
    GPU_AVAILABLE = True
except pynvml.NVMLError:
    GPU_AVAILABLE = False
    logging.warning("Графический процессор NVIDIA не обнаружен, или не удалось выполнить инициализацию pynvml.")

# Инициализация Prometheus метрик
def init_prometheus_metrics():
    metrics = {}
    metric_names = {
        'cpu_usage': ('app_cpu_usage_percent', 'CPU usage percentage'),
        'memory_usage': ('app_memory_usage_mb', 'Memory usage in MB'),
        'disk_io': ('app_disk_io_bytes', 'Disk I/O in bytes'),
        'network_io': ('app_network_io_bytes', 'Network I/O in bytes'),
        'gpu_memory_usage': ('app_gpu_memory_usage_mb', 'GPU memory usage in MB'),
        'tfidf_time': ('app_tfidf_time_seconds', 'TF-IDF reranking time in seconds')
    }

    for key, (name, description) in metric_names.items():
        if name not in REGISTRY._names_to_collectors:
            metrics[key] = Gauge(name, description)
        else:
            metrics[key] = REGISTRY._names_to_collectors[name]

    return metrics

# Инициализация метрик
prometheus_metrics = init_prometheus_metrics()

# Функция мониторинга ресурсов
def monitor_resources():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_used_mb = memory.used / (1024 * 1024)
    disk_io = psutil.disk_io_counters()
    network_io = psutil.net_io_counters()

    prometheus_metrics['cpu_usage'].set(cpu_percent)
    prometheus_metrics['memory_usage'].set(memory_used_mb)
    prometheus_metrics['disk_io'].set(disk_io.read_bytes + disk_io.write_bytes)
    prometheus_metrics['network_io'].set(network_io.bytes_sent + network_io.bytes_recv)

    log_message = (f"CPU: {cpu_percent}%, Memory: {memory_used_mb:.2f} MB, "
                   f"Disk I/O: {disk_io.read_bytes + disk_io.write_bytes} bytes, "
                   f"Network I/O: {network_io.bytes_sent + network_io.bytes_recv} bytes")

    # GPU memory monitoring
    if GPU_AVAILABLE:
        try:
            device_count = pynvml.nvmlDeviceGetCount()
            total_gpu_memory_used_mb = 0
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                total_gpu_memory_used_mb += mem_info.used / (1024 * 1024)
            prometheus_metrics['gpu_memory_usage'].set(total_gpu_memory_used_mb)
            log_message += f", GPU Memory: {total_gpu_memory_used_mb:.2f} MB"
        except pynvml.NVMLError as e:
            log_message += f", GPU Memory: Error ({str(e)})"
            prometheus_metrics['gpu_memory_usage'].set(0)
    else:
        log_message += ", GPU Memory: Not available"
        prometheus_metrics['gpu_memory_usage'].set(0)

    logging.info(log_message)

# Функция запуска мониторинга
def start_monitoring(interval=5):
    while True:
        monitor_resources()
        time.sleep(interval)

# Запуск Prometheus сервера и мониторинга
start_http_server(8000)
monitoring_thread = threading.Thread(target=start_monitoring, args=(5,), daemon=True)
monitoring_thread.start()

# === Функция для получения списка моделей Ollama ===
@st.cache_data
def models_list():
    result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')
    model_names = [line.split()[0] for line in lines[1:] if line.strip()]
    return model_names

ollama_models = models_list()
default_model = MODEL_NAME if MODEL_NAME in ollama_models else ollama_models[0]

# === Загружаем векторную БД ===
@st.cache_resource
def load_vector_db(db_name):
    embeddings = HuggingFaceEmbeddings(model_name=model_path, model_kwargs={'device': 'cpu'})
    return FAISS.load_local(db_name, embeddings, allow_dangerous_deserialization=True)

# === Создаем Ollama LLM ===
def create_ollama_model(model_name, temperature, max_tokens, top_p):
    return OllamaLLM(
        model=model_name,
        model_kwargs={"temperature": temperature, "max_tokens": max_tokens, "top_p": top_p}
    )

# === Функция для ранжирования с BM25 ===
def rerank_with_bm25(query, documents, top_k=5):
    if not documents or not query:
        return [], [0.0] * min(top_k, len(documents))

    tokenized_query = query.split()
    tokenized_docs = [doc.page_content.split() for doc in documents]

    bm25 = BM25Okapi(tokenized_docs)
    scores = bm25.get_scores(tokenized_query)

    sorted_indices = np.argsort(scores)[::-1][:top_k]
    return [documents[i] for i in sorted_indices], [float(scores[i]) for i in sorted_indices]

# === Функция для ранжирования с TF-IDF ===
def rerank_with_tfidf(query, documents, top_k=5):
    if not documents or not query:
        return [], [0.0] * min(top_k, len(documents))

    # Извлекаем текст документов
    doc_texts = [doc.page_content for doc in documents]

    # Создаем TF-IDF векторизатор
    vectorizer = TfidfVectorizer()
    # Вычисляем TF-IDF матрицу для документов и запроса
    tfidf_matrix = vectorizer.fit_transform(doc_texts + [query])

    # Разделяем матрицу на документы и запрос
    doc_vectors = tfidf_matrix[:-1]
    query_vector = tfidf_matrix[-1]

    # Вычисляем косинусное сходство между запросом и документами
    scores = cosine_similarity(query_vector, doc_vectors)[0]

    # Сортируем документы по убыванию релевантности
    sorted_indices = np.argsort(scores)[::-1][:top_k]
    return [documents[i] for i in sorted_indices], [float(scores[i]) for i in sorted_indices]

# === Функция ответа с потоковым выводом ===
def answer_question(prompt, model_name, temperature, max_tokens, top_p, use_rag, db, rerank_method):
    start_time = time.time()
    ollama_llm = create_ollama_model(model_name, temperature, max_tokens, top_p)
    russian_prompt = f"""
        Ты эксперт по аналитике. Ответь на русском языке максимально точно и профессионально, используя предоставленный контекст. Если контекст не содержит достаточно информации, дай общий ответ на основе своих знаний, но укажи, что информация ограничена.
        Вопрос: {prompt}
        Ответ:
    """
    answer = ""
    source_text = ""
    faiss_time = 0.0
    bm25_time = 0.0
    tfidf_time = 0.0
    llm_time = 0.0

    logging.info(f"Processing question: {prompt}")

    if use_rag:
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            output_key="answer",
            return_messages=True
        )

        # Замер времени FAISS
        faiss_start = time.time()
        retriever = db.as_retriever(search_kwargs={"k": 20})
        sources = retriever.invoke(russian_prompt)
        faiss_time = time.time() - faiss_start
        logging.info(f"FAISS retrieval time: {faiss_time:.2f} seconds")

        # Замер времени реранжирования
        rerank_start = time.time()
        if rerank_method == "BM25":
            reranked_sources, rerank_scores = rerank_with_bm25(russian_prompt, sources, top_k=5)
            bm25_time = time.time() - rerank_start
            logging.info(f"BM25 reranking time: {bm25_time:.2f} seconds")
        else:
            reranked_sources, rerank_scores = rerank_with_tfidf(russian_prompt, sources, top_k=5)
            tfidf_time = time.time() - rerank_start
            logging.info(f"TF-IDF reranking time: {tfidf_time:.2f} seconds")
            prometheus_metrics['tfidf_time'].set(tfidf_time)

        # Формируем контекст
        context = "\n\n".join([f"[{i + 1}] {doc.page_content}" for i, doc in enumerate(reranked_sources)])
        full_prompt = f"""
            Ты эксперт по аналитике. Ответь на русском языке максимально точно и профессионально.
            Вопрос: {russian_prompt}
            Контекст:
            {context}
        """

        # Формируем информацию об источниках
        source_info = []
        for i, (doc, score) in enumerate(zip(reranked_sources, rerank_scores), 1):
            filename = doc.metadata.get("source", "Unknown file")
            content = doc.page_content.strip()
            source_info.append(
                f"[{i}] 📄 **Файл**: {filename} ({rerank_method} Score: {score:.2f})\n\n{content}"
            )
        source_text = "\n\n---\n\n".join(source_info)

        # Замер времени LLM
        llm_start = time.time()
        for chunk in ollama_llm.stream(full_prompt):
            answer += chunk
            yield chunk
        llm_time = time.time() - llm_start
        logging.info(f"LLM generation time: {llm_time:.2f} seconds")
    else:
        llm_start = time.time()
        for chunk in ollama_llm.stream(russian_prompt):
            answer += chunk
            yield chunk
        llm_time = time.time() - llm_start
        logging.info(f"LLM generation time: {llm_time:.2f} seconds")
        source_text = "📄 Режим RAG отключён — источники не используются."

    response_time = time.time() - start_time
    logging.info(f"Total response time: {response_time:.2f} seconds")

    # Сохранение в CSV
    write_header = not os.path.exists(CSV_LOG)
    with open(CSV_LOG, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
        if write_header:
            writer.writerow([
                "Question", "Answer", "Model", "Temperature", "Max Tokens", "Top P",
                "Response Time (s)", "FAISS Time (s)", "BM25 Time (s)", "TF-IDF Time (s)", "LLM Time (s)", "Sources"
            ])
        writer.writerow([
            prompt, answer, model_name, temperature, max_tokens, top_p,
            round(response_time, 2), round(faiss_time, 2), round(bm25_time, 2), round(tfidf_time, 2), round(llm_time, 2), source_text
        ])

    yield answer, source_text

# === Streamlit UI ===
st.markdown("<h1 style='text-align: center; width: 100%; font-size: 30pt'>📄🔍 RAG технология LLM + FAISS</h1>",
            unsafe_allow_html=True)

st.sidebar.markdown("Задавайте вопросы по базе знаний:")

# Настройки в боковой панели
st.sidebar.header("⚙️ Параметры модели")
model_name = st.sidebar.selectbox("Выбор модели:", ollama_models, index=ollama_models.index(default_model))
selected_db_name = st.sidebar.selectbox("📚 Выберите FAISS базу данных:", RAISS_DB)
temperature = st.sidebar.slider("Температура:", 0.0, 1.0, 0.2, 0.1,
                               help="Чем ближе к 1.0, тем больше креатива у модели")
max_tokens = st.sidebar.slider("Количество токенов:", 200, 3000, 1500, 100,
                              help="Максимальное количество токенов в ответе")
top_p = st.sidebar.slider("Top-P:", 0.0, 1.0, 0.3, 0.1, help="Чем ближе к 1.0, тем больше креатива у модели")
use_rag = st.sidebar.checkbox("🔁 Включить RAG (поиск по базе документов)", value=True)
rerank_method = st.sidebar.selectbox("Метод реранжирования:", ["BM25", "TF-IDF"], index=0)

# Мониторинг в боковой панели
st.sidebar.header("📊 Мониторинг")
with st.sidebar:
    st.metric("CPU Usage", f"{psutil.cpu_percent()}%")
    st.metric("Memory Usage", f"{psutil.virtual_memory().used / (1024 * 1024):.2f} MB")
    if GPU_AVAILABLE:
        try:
            device_count = pynvml.nvmlDeviceGetCount()
            total_gpu_memory_used_mb = 0
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                total_gpu_memory_used_mb += mem_info.used / (1024 * 1024)
            st.metric("GPU Memory Usage", f"{total_gpu_memory_used_mb:.2f} MB")
        except pynvml.NVMLError:
            st.metric("GPU Memory Usage", "Error")
    else:
        st.metric("GPU Memory Usage", "Not available")

# Логи Prometheus и приложения
st.sidebar.header("📜 Логи")
with st.sidebar:
    st.markdown(f"[Открыть логи в Grafana]({GRAFANA_LOGS_URL})")

# Загружаем векторную базу
db = load_vector_db(selected_db_name)

# Ввод вопроса
st.header("💬 Ввод вопроса")
question = st.text_area("Введите вопрос по аналитике:")

if st.button("Поиск"):
    if not question.strip():
        st.warning("Введите вопрос перед отправкой.")
    else:
        with st.spinner("Генерация ответа..."):
            st.subheader("Ответ LLM:")
            with st.container():
                answer_container = st.empty()
                full_answer = ""
                source_text = ""
                response_time = 0.0
                start_time = time.time()
                for item in answer_question(question, model_name, temperature, max_tokens, top_p, use_rag, db, rerank_method):
                    if isinstance(item, str):
                        full_answer += item
                        answer_container.markdown(
                            f'<div class="answer-box">{full_answer}<span style="animation: blink 1s step-end infinite;">|</span></div>',
                            unsafe_allow_html=True
                        )
                    else:
                        full_answer, source_text = item
                        answer_container.markdown(
                            f'<div class="answer-box">{full_answer}<span style="animation: blink 1s step-end infinite;">|</span></div>',
                            unsafe_allow_html=True
                        )
                response_time = time.time() - start_time
            st.subheader("📁 Источники:")
            st.text_area("Файлы", value=source_text, height=400)
            st.sidebar.metric("Last Response Time", f"{response_time:.2f} s")

# Очистка pynvml при завершении
if GPU_AVAILABLE:
    pynvml.nvmlShutdown()