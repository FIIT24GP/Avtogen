import os
import csv
import time
import subprocess
import numpy as np
from typing import List, Dict, Optional, Generator

# Импорты из рабочих файлов - точно как есть
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Конфигурация - из new_UI_2 (2).py
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "hf.co/t-tech/T-lite-it-1.0-Q8_0-GGUF:Q8_0"
MODEL_PATH = r"E:\ollama_chat\models\intfloat\multilingual-e5-large"
CSV_LOG = "E:\\ollama_chat\\analitika_history2.csv"
RAISS_DB = ['analitika_docx_pdf_html_v2', 'analitika1', 'analitika3', 'weld_tks_v1']
GRAFANA_LOGS_URL = "http://localhost:3003/d/34e0395a-530e-428f-bbca-4465ccce4c46/prometheus-logs"
APP_LOG_FILE = "E:\\ollama_chat\\resource_usage.log"


class VectorBaseService:
    """Сервис для работы с векторной базой - код из load_pdf_text.py"""
    
    @staticmethod
    def get_files_from_directory(directory):
        docx_files = []
        pdf_files = []

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.docx'):
                    docx_files.append(os.path.join(root, file))
                elif file.endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))

        return docx_files, pdf_files

    @staticmethod
    def extract_text_from_docx(docx_file):
        loader = Docx2txtLoader(docx_file)
        documents = loader.load()
        return documents

    @staticmethod
    def extract_text_from_pdf(pdf_file):
        loader = PyPDFLoader(pdf_file)
        documents = loader.load()
        return documents

    @staticmethod
    def create_vector_store(documents):
        embeddings = HuggingFaceEmbeddings(model_name=MODEL_PATH)
        text_splitter = SemanticChunker(
                embeddings=embeddings,
                breakpoint_threshold_type="percentile",
                breakpoint_threshold_amount=95
            )
        docs = text_splitter.split_documents(documents)
        faiss_vector_store = FAISS.from_documents(docs, embeddings)
        return faiss_vector_store

    @classmethod
    def process_files(cls, directory):
        docx_files, pdf_files = cls.get_files_from_directory(directory)
        all_documents = []

        for docx_file in docx_files:
            print(f"Processing DOCX file: {docx_file}")
            docx_documents = cls.extract_text_from_docx(docx_file)
            all_documents.extend(docx_documents)

        for pdf_file in pdf_files:
            print(f"Processing PDF file: {pdf_file}")
            pdf_documents = cls.extract_text_from_pdf(pdf_file)
            all_documents.extend(pdf_documents)

        faiss_vector_store = cls.create_vector_store(all_documents)
        return faiss_vector_store


class RAGService:
    """Сервис для RAG генерации - код из new_UI_2 (2).py"""
    
    @staticmethod
    def get_ollama_models():
        """Получение списка доступных моделей Ollama"""
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            model_names = [line.split()[0] for line in lines[1:] if line.strip()]
            return model_names
        except Exception as e:
            print(f"Ошибка получения списка моделей: {e}")
            return [MODEL_NAME]

    @staticmethod
    def create_ollama_model(model_name: str, temperature: float, max_tokens: int, top_p: float):
        """Создание модели Ollama"""
        return OllamaLLM(
            model=model_name,
            model_kwargs={"temperature": temperature, "max_tokens": max_tokens, "top_p": top_p}
        )

    @staticmethod
    def rerank_with_bm25(query: str, documents: List, top_k: int = 5):
        """Реранжирование с BM25"""
        if not documents or not query:
            return [], [0.0] * min(top_k, len(documents))

        tokenized_query = query.split()
        tokenized_docs = [doc.page_content.split() for doc in documents]

        bm25 = BM25Okapi(tokenized_docs)
        scores = bm25.get_scores(tokenized_query)

        sorted_indices = np.argsort(scores)[::-1][:top_k]
        return [documents[i] for i in sorted_indices], [float(scores[i]) for i in sorted_indices]

    @staticmethod
    def rerank_with_tfidf(query: str, documents: List, top_k: int = 5):
        """Реранжирование с TF-IDF"""
        if not documents or not query:
            return [], [0.0] * min(top_k, len(documents))

        doc_texts = [doc.page_content for doc in documents]
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(doc_texts + [query])
        doc_vectors = tfidf_matrix[:-1]
        query_vector = tfidf_matrix[-1]
        scores = cosine_similarity(query_vector, doc_vectors)[0]
        sorted_indices = np.argsort(scores)[::-1][:top_k]
        return [documents[i] for i in sorted_indices], [float(scores[i]) for i in sorted_indices]


class ContentGenerationService:
    """Основной сервис для генерации контента"""
    
    def __init__(self, materials_path: str):
        self.materials_path = materials_path
        self.vector_base = None
        self.vector_service = VectorBaseService()
        self.rag_service = RAGService()
        
    def load_vector_base(self) -> bool:
        """Загрузка векторной базы из материалов"""
        try:
            if os.path.exists(self.materials_path) and os.listdir(self.materials_path):
                self.vector_base = self.vector_service.process_files(self.materials_path)
                return True
            else:
                print(f"Папка материалов пуста или не существует: {self.materials_path}")
                return False
        except Exception as e:
            print(f"Ошибка загрузки векторной базы: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Получение списка доступных моделей"""
        return self.rag_service.get_ollama_models()
    
    def _create_prompt_by_level(self, content: str, level: int) -> str:
        """Создание промта в зависимости от уровня генерации"""
        if level == 1:  # Генерация тезисов
            return f"""
            Ты — преподаватель вуза, разрабатывающий курс дополнительного образования. 
            На входе задаётся тема лекции, рассчитанной на 1,5 часа. 
            Сформируй список из примерно 15 заголовков слайдов, отражающих логичную и полноту раскрытия темы. 
            Каждый заголовок должен быть оформлен как учебный, без аннотаций и пояснений.
            Возвращай только список заголовков слайдов.
            
            Тема: {content}
            """
        elif level == 2:  # Генерация текста слайда
            return f"""
            Ты — преподаватель вуза, разрабатывающий слайды для курса дополнительного образования. 
            На входе задается один заголовок слайда. 
            Сформируй список кратких учебных пунктов (5-7), которые должны быть отображены на этом слайде. 
            Пункты должны быть четкими, академичными и раскрывать содержание темы. 
            Не включай пояснений, примеров или ссылок. Возвращай только список пунктов.
            
            Заголовок слайда: {content}
            """
        elif level == 3:  # Генерация текста лекции
            return f"""
            Ты — преподаватель вуза, готовящий устную часть лекции для курса дополнительного образования. 
            На входе задан заголовок слайда и список учебных пунктов. 
            Сгенерируй связный академический текст продолжительностью примерно 5 минут, охватывающий все указанные пункты. 
            Стиль — академический с элементами живой речи. 
            Текст должен быть логично разбит на абзацы. 
            Обязательно используй речевые переходы между фрагментами. 
            Завершать текст выводом не требуется.
            
            Содержание для раскрытия: {content}
            """
        else:
            return content
    
    def generate_content(self, 
                        content: str, 
                        level: int,
                        model_name: str = MODEL_NAME,
                        temperature: float = 0.2,
                        max_tokens: int = 1500,
                        top_p: float = 0.3,
                        rerank_method: str = "BM25") -> Generator[str, None, None]:
        """
        Генерация контента с потоковым выводом
        
        Args:
            content: Входной контент
            level: Уровень генерации (1-тезисы, 2-слайд, 3-лекция)
            model_name: Название модели Ollama
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов
            top_p: Top-p параметр
            rerank_method: Метод реранжирования (BM25 или TF-IDF)
            
        Yields:
            str: Фрагменты сгенерированного текста
        """
        start_time = time.time()
        answer = ""
        source_text = ""
        faiss_time = 0.0
        bm25_time = 0.0
        tfidf_time = 0.0
        llm_time = 0.0
        
        try:
            # Создаем промт для уровня
            russian_prompt = self._create_prompt_by_level(content, level)
            
            # Создаем модель
            ollama_llm = self.rag_service.create_ollama_model(
                model_name, temperature, max_tokens, top_p
            )
            
            if self.vector_base:
                # RAG режим - замеряем время как в new_UI_2 (2).py
                faiss_start = time.time()
                retriever = self.vector_base.as_retriever(search_kwargs={"k": 20})
                sources = retriever.invoke(russian_prompt)
                faiss_time = time.time() - faiss_start
                
                rerank_start = time.time()
                if rerank_method == "BM25":
                    reranked_sources, rerank_scores = self.rag_service.rerank_with_bm25(
                        russian_prompt, sources, top_k=5
                    )
                    bm25_time = time.time() - rerank_start
                else:
                    reranked_sources, rerank_scores = self.rag_service.rerank_with_tfidf(
                        russian_prompt, sources, top_k=5
                    )
                    tfidf_time = time.time() - rerank_start
                
                context = "\n\n".join([
                    f"[{i + 1}] {doc.page_content}" 
                    for i, doc in enumerate(reranked_sources)
                ])
                
                full_prompt = f"""
                {russian_prompt}
                
                Контекст из базы знаний:
                {context}
                """
                
                # Формируем информацию об источниках как в new_UI_2 (2).py
                source_info = []
                for i, (doc, score) in enumerate(zip(reranked_sources, rerank_scores), 1):
                    filename = doc.metadata.get("source", "Unknown file")
                    content_preview = doc.page_content.strip()
                    source_info.append(
                        f"[{i}] 📄 **Файл**: {filename} ({rerank_method} Score: {score:.2f})\n\n{content_preview}"
                    )
                source_text = "\n\n---\n\n".join(source_info)
            else:
                full_prompt = russian_prompt
                source_text = "📄 Режим RAG отключён — источники не используются."
            
            # Генерация с потоковым выводом и замером времени
            llm_start = time.time()
            for chunk in ollama_llm.stream(full_prompt):
                answer += chunk
                yield chunk
            llm_time = time.time() - llm_start
                
        except Exception as e:
            error_msg = f"Ошибка генерации: {str(e)}"
            answer = error_msg
            yield error_msg
        
        # Логирование в CSV как в new_UI_2 (2).py
        response_time = time.time() - start_time
        self._log_to_csv(
            content, answer, model_name, temperature, max_tokens, top_p,
            response_time, faiss_time, bm25_time, tfidf_time, llm_time, source_text
        )
    
    def _log_to_csv(self, question, answer, model_name, temperature, max_tokens, top_p,
                   response_time, faiss_time, bm25_time, tfidf_time, llm_time, sources):
        """Логирование в CSV файл как в new_UI_2 (2).py"""
        try:
            write_header = not os.path.exists(CSV_LOG)
            with open(CSV_LOG, "a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
                if write_header:
                    writer.writerow([
                        "Question", "Answer", "Model", "Temperature", "Max Tokens", "Top P",
                        "Response Time (s)", "FAISS Time (s)", "BM25 Time (s)", "TF-IDF Time (s)", "LLM Time (s)", "Sources"
                    ])
                writer.writerow([
                    question, answer, model_name, temperature, max_tokens, top_p,
                    round(response_time, 2), round(faiss_time, 2), round(bm25_time, 2), 
                    round(tfidf_time, 2), round(llm_time, 2), sources
                ])
        except Exception as e:
            print(f"Ошибка записи в CSV: {e}")
    
    def generate_content_sync(self, 
                             content: str, 
                             level: int,
                             model_name: str = MODEL_NAME,
                             temperature: float = 0.2,
                             max_tokens: int = 1500,
                             top_p: float = 0.3,
                             rerank_method: str = "BM25") -> str:
        """
        Синхронная генерация контента (для простых случаев)
        """
        result = ""
        for chunk in self.generate_content(
            content, level, model_name, temperature, max_tokens, top_p, rerank_method
        ):
            result += chunk
        return result
    
    def parse_theses(self, generated_text: str) -> List[str]:
        """Парсинг сгенерированных тезисов в список"""
        theses = []
        for line in generated_text.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Убираем нумерацию если есть
                if line[0].isdigit() and '.' in line[:5]:
                    line = line.split('.', 1)[1].strip()
                if line.startswith('- '):
                    line = line[2:].strip()
                if line:
                    theses.append(line)
        return theses
    
    def save_intermediate_results(self, theses: List[str], slide_texts: List[str], 
                                 filepath: str = "intermediate_texts.txt") -> bool:
        """Сохранение промежуточных результатов"""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("=== ТЕЗИСЫ ЛЕКЦИИ ===\n\n")
                for i, thesis in enumerate(theses, 1):
                    f.write(f"{i}. {thesis}\n")
                    
                f.write("\n\n=== ТЕКСТЫ СЛАЙДОВ ===\n\n")
                for i, text in enumerate(slide_texts, 1):
                    f.write(f"Слайд {i}:\n{text}\n\n")
            return True
        except Exception as e:
            print(f"Ошибка сохранения промежуточных результатов: {e}")
            return False
    
    def save_final_lecture(self, lecture_texts: List[str], 
                          filepath: str = "final_lecture.txt") -> bool:
        """Сохранение итогового текста лекции"""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("=== ИТОГОВЫЙ ТЕКСТ ЛЕКЦИИ ===\n\n")
                for i, text in enumerate(lecture_texts, 1):
                    f.write(f"Часть {i}:\n{text}\n\n")
            return True
        except Exception as e:
            print(f"Ошибка сохранения итогового текста: {e}")
            return False