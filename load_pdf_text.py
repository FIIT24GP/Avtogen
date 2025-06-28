# import os
# from pypdf import PdfReader
#
# folder = 'E:\\ollama_chat\\analitika\\'
# documents = []
#
# for file in os.listdir(folder):
#     elif file.endswith('.pdf'):
#         reader = PdfReader("lsystems_rus.pdf")
#         number_of_pages = len(reader.pages)
#         page = reader.pages[0]
#         text = page.extract_text()
#         # после pdf остаются абзацы после окончания строки делаем замены
#         text = text.replace('\n', ' ') # замена абзацев на пробелы
#         text = text.replace('  ', ' ') # замена двух пробелов на один пробел
#         text = text.replace('   ', ' ') # замена трех пробелов на один пробел
#         text = text.replace(' .', '.') # замена пробела перед точкой
#         text = text.replace(' ,', ',') # замена пробела перед запятой
import os

import os
from langchain_community.document_loaders import Docx2txtLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

path = 'E:\\ollama_chat\\testing\\'
model_path = r"E:\ollama_chat\models\intfloat\multilingual-e5-large"

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

def extract_text_from_docx(docx_file):
    loader = Docx2txtLoader(docx_file)
    documents = loader.load()
    return documents


def extract_text_from_pdf(pdf_file):
    loader = PyPDFLoader(pdf_file)
    documents = loader.load()
    return documents

def create_vector_store(documents):
    embeddings = HuggingFaceEmbeddings(model_name=model_path)
    text_splitter = SemanticChunker(
            embeddings=embeddings,
            breakpoint_threshold_type="percentile", # Разбиение по процентилю схожести
            breakpoint_threshold_amount=95 # Порог для определения границы чанка
        )
    docs = text_splitter.split_documents(documents)
    faiss_vector_store = FAISS.from_documents(docs, embeddings)

    return faiss_vector_store


def process_files(directory):
    docx_files, pdf_files = get_files_from_directory(directory)
    all_documents = []

    # Извлекаем текст из DOCX файлов
    for docx_file in docx_files:
        print(f"Processing DOCX file: {docx_file}")
        docx_documents = extract_text_from_docx(docx_file)
        all_documents.extend(docx_documents)

    # Извлекаем текст из PDF файлов
    for pdf_file in pdf_files:
        print(f"Processing PDF file: {pdf_file}")
        pdf_documents = extract_text_from_pdf(pdf_file)
        all_documents.extend(pdf_documents)

    faiss_vector_store = create_vector_store(all_documents)
    return faiss_vector_store

faiss_vector_store = process_files(path)
faiss_vector_store.save_local("testing")

# import chardet
# from bs4 import BeautifulSoup, UnicodeDammit
# from pathlib import Path
# from langchain_community.document_loaders import BSHTMLLoader
#
# from langchain_community.vectorstores import FAISS
# from langchain_core.documents import Document
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_text_splitters import RecursiveCharacterTextSplitter
#
# path = 'E:\\ollama_chat\\docs\\'
# model_path = r"E:\ollama_chat\models\intfloat\multilingual-e5-large"
#
# html_files = list(Path(path).rglob("*.html")) + list(Path(path).rglob("*.htm"))
#
#
# def safe_html_loader(file_path):
#     """Загружаем HTML файл"""
#     try:
#         # сначала явная кодировка UTF-8, если не она, то сработает исключение
#         loader = BSHTMLLoader(file_path, open_encoding='utf-8')
#         return loader.load()
#     except UnicodeDecodeError:
#         try:
#             # пробуем с другой кодировкой
#             with open(file_path, 'rb') as f:
#                 content = f.read()
#             detected_encoding = UnicodeDammit(content).original_encoding
#             loader = BSHTMLLoader(file_path, open_encoding=detected_encoding)
#             return loader.load()
#         except:
#             # необработанный синтаксический анализ, если предыдущее не помогло
#             with open(file_path, 'rb') as f:
#                 soup = BeautifulSoup(f.read(), 'html.parser')
#             return [Document(
#                 page_content=soup.get_text(separator=' ', strip=True),
#                 metadata={"source_file": os.path.basename(file_path)}
#             )]
#
# def process_html_files(html_files):
#     all_docs = []
#     for file_path in html_files:
#         try:
#             docs = safe_html_loader(file_path)
#             # Добавляем дополнительные метаданные
#             for doc in docs:
#                 doc.metadata.update({
#                     "absolute_path": os.path.abspath(file_path),
#                     "file_type": "html",
#                     "last_modified": os.path.getmtime(file_path)
#                 })
#             all_docs.extend(docs)
#         except Exception as e:
#             print(f"Skipping {file_path} due to error: {str(e)}")
#             continue
#     return all_docs
#
# text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
# all_docs = process_html_files(html_files)
# split_docs = text_splitter.split_documents(all_docs)
#
# embeddings = HuggingFaceEmbeddings(model_name=model_path)
# db = FAISS.load_local("analitika_docx_pdf", embeddings, allow_dangerous_deserialization=True)
#
# new_db = FAISS.from_documents(split_docs, embeddings)
#
# db.merge_from(new_db)
#
# db.save_local("analitika_docx_pdf_html_v2")