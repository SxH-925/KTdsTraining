import os
from dotenv import load_dotenv
from openai import AzureOpenAI



# Load environment variables
load_dotenv()

openai_endpoint = os.getenv("OPENAI_ENDPOINT")
openai_api_key = os.getenv("OPENAI_API_KEY")
chat_model = os.getenv("CHAT_MODEL")

# Initialize Azure OpenAI client
chat_client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint=openai_endpoint,
    api_key=openai_api_key
)

def get_openai_response(messages, use_rag=True, search_endpoint=None, search_api_key=None, index_name=None):
    """
    GPT 응답을 생성하는 함수 (기본적으로 RAG 활성화)
    """
    rag_params = {
        "data_sources": [
            {
                "type": "azure_search",
                "parameters": {
                    "endpoint": search_endpoint,
                    "index_name": index_name,
                    "authentication": {
                        "type": "api_key",
                        "key": search_api_key,
                    }
                }
            }
        ]
    } if use_rag and search_endpoint and search_api_key and index_name else {}

    response = chat_client.chat.completions.create(
        model=chat_model,
        messages=messages,
        extra_body=rag_params
    )
    return response.choices[0].message.content

def regenerate_fix_code(messages):
    """
    수정 코드만 다시 생성하도록 GPT에 요청
    이전에 동일 요청이 있다면 중복 제거 후 재요청
    """
    temp_messages = messages.copy()

    if temp_messages and temp_messages[-1]["role"] == "user" and "수정 코드만 다시 생성해줘" in temp_messages[-1]["content"]:
        temp_messages.pop()

    temp_messages.append({
        "role": "user",
        "content": "위 코드에 대해 수정 코드만 다시 생성해줘. 불필요한 설명 없이 코드 블록만 출력해줘."
    })

    response = chat_client.chat.completions.create(
        model=chat_model,
        messages=temp_messages,
        extra_body={}  # regenerate는 RAG 비활성화
    )
    return response.choices[0].message.content
