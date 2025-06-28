from opensearchpy import OpenSearch
from sentence_transformers import SentenceTransformer
from ollama import Client as OllamaClient
import logging

# --- Настройка логирования ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("semantic_search.log", encoding='utf-8'),
        logging.StreamHandler()  # Чтобы и в консоль, и в файл
    ]
)

# --- Конфигурация ---
INDEX_NAME = "semantic-docs-e5"

# --- Подключение к OpenSearch ---
client = OpenSearch(
    hosts=[{'host': 'localhost', 'port': 9200}],
    http_auth=None,
    use_ssl=False,
    verify_certs=False
)

# --- Инициализация моделей ---
embed_model = SentenceTransformer('intfloat/multilingual-e5-base')
ollama_client = OllamaClient(host='http://localhost:11434')


# --- Переформулировка запроса ---
def reformulate_query(prompt):
    try:
        response = ollama_client.generate(
            model='gemma3:27b',
            prompt=(
                f"Ты — ассистент по улучшению поисковых запросов. "
                f"Твоя задача — переформулировать запрос для лучшего семантического поиска, "
                f"расширив его синонимами и ключевыми словами, сохранив смысл. "
                f"Ответом выдай ТОЛЬКО переформулированный текст, без пояснений. "
                f"\n\nЗапрос: \"{prompt}\"\nПереформулированный:"
            ),
            options={"temperature": 0.3, "num_predict": 100}
        )
        return response['response'].strip()
    except Exception as e:
        logging.warning(f"Ollama не отвечает, используем оригинальный запрос. Ошибка: {e}")
        return prompt


# --- Семантический поиск ---
def semantic_search(query, k=5):
    rewritten = reformulate_query(query)
    logging.info(f"Переформулированный запрос: {rewritten}")

    query_vector = embed_model.encode(rewritten)
    body = {
        "size": k,
        "query": {
            "knn": {
                "embedding": {
                    "vector": query_vector.tolist(),
                    "k": k
                }
            }
        },
        "_source": ["paragraph", "filename"]  # Получаем только нужные поля
    }
    response = client.search(index=INDEX_NAME, body=body)
    return response["hits"]["hits"]


# --- Генерация ответа на основе найденных документов ---
def generate_answer(query, search_results):
    if not search_results:
        return "Извините, не удалось найти релевантную информацию по вашему запросу."

    # Собираем контекст из найденных документов
    context_parts = []
    for i, result in enumerate(search_results):
        paragraph = result['_source']['paragraph']
        filename = result['_source']['filename']
        score = result['_score']

        # Добавляем только релевантные результаты (с хорошим скором)
        if score > 0.5:  # Порог релевантности
            context_parts.append(f"[Документ: {filename}]\n{paragraph}")

    if not context_parts:
        return "Найденная информация недостаточно релевантна для ответа на ваш запрос."

    context = "\n\n".join(context_parts)

    # Ограничиваем контекст для избежания переполнения
    max_context_length = 4000
    if len(context) > max_context_length:
        context = context[:max_context_length] + "..."

    try:
        prompt = f"""Ты — эксперт-аналитик. На основе предоставленной информации дай подробный и структурированный ответ на вопрос пользователя.

ВАЖНО:
- Используй ТОЛЬКО информацию из предоставленного контекста
- Если информации недостаточно, честно об этом скажи
- Структурируй ответ логично и подробно
- Приводи конкретные факты и данные из документов
- Не придумывай информацию, которой нет в контексте

Вопрос пользователя: {query}

Контекст из документов:
{context}

Ответ:"""

        response = ollama_client.generate(
            model='gemma3:27b',
            prompt=prompt,
            options={
                "temperature": 0.1,  # Низкая температура для точности
                "num_predict": 1000,  # Больше токенов для подробного ответа
                "top_p": 0.9,
                "repeat_penalty": 1.1
            }
        )

        return response['response'].strip()

    except Exception as e:
        logging.error(f"Ошибка при генерации ответа: {e}")
        return f"Ошибка при генерации ответа. Найденная информация:\n\n" + "\n\n".join(
            [r['_source']['paragraph'] for r in search_results[:3]])


# --- Интерактивный поиск ---
def interactive_search():
    print("=== Семантический поиск по документам ===")
    print("Введите 'exit' для выхода\n")

    while True:
        query = input("Ваш вопрос: ").strip()
        if query.lower() in ['exit', 'quit', 'выход']:
            break

        if not query:
            continue

        print("\n🔍 Поиск информации...")

        # Поиск релевантных документов
        search_results = semantic_search(query, k=7)

        if not search_results:
            print("❌ Ничего не найдено")
            continue

        # Показываем найденные документы для отладки
        print(f"\n📋 Найдено {len(search_results)} релевантных фрагментов:")
        for i, result in enumerate(search_results[:3]):  # Показываем только топ-3
            score = result['_score']
            filename = result['_source']['filename']
            text_preview = result['_source']['paragraph'][:200] + "..." if len(
                result['_source']['paragraph']) > 200 else result['_source']['paragraph']
            print(f"{i + 1}. [{filename}] (score: {score:.3f})\n   {text_preview}\n")

        # Генерируем ответ
        print("🤖 Генерация ответа...\n")
        answer = generate_answer(query, search_results)

        print("=" * 80)
        print("ОТВЕТ:")
        print("=" * 80)
        print(answer)
        print("=" * 80)
        print()


# === Пример использования ===
if __name__ == "__main__":
    # Тестовый запрос
    test_query = "Зарубежные марки БПЛА и их производители"

    print(f"Тестовый запрос: {test_query}")
    print("=" * 50)

    # Поиск
    search_results = semantic_search(test_query, k=5)

    # Показываем результаты поиска
    print("Найденные документы:")
    for i, result in enumerate(search_results):
        score = result['_score']
        filename = result['_source']['filename']
        text = result['_source']['paragraph'][:200] + "..." if len(result['_source']['paragraph']) > 200 else \
        result['_source']['paragraph']
        print(f"{i + 1}. [{filename}] (score: {score:.3f})\n   {text}\n")

    # Генерируем ответ
    print("=" * 50)
    answer = generate_answer(test_query, search_results)
    print("СГЕНЕРИРОВАННЫЙ ОТВЕТ:")
    print("=" * 50)
    print(answer)
    print()

    # Запуск интерактивного режима
    choice = input("Запустить интерактивный режим? (y/n): ")
    if choice.lower().startswith('y'):
        interactive_search()