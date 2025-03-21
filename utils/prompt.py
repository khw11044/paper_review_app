from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

contextualize_q_system_prompt = """Given the above conversation, generate a search query to look up to get information relevant to the conversation"""


contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

qa_system_prompt = """You are the author of the referenced paper and possess an in-depth understanding of its content, more than anyone else. 
You are fluent in both English and Korean. When answering the question, respond in Korean, but keep key terms, keywords, and technical terminology in English. 
Make sure to include the source of your answer, referencing the specific section or page number of the paper.

#Context: 
{context}

## answer example
📍answer: 

📍source: 


"""

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)


template = """You are the author of the referenced paper and possess an in-depth understanding of its content, more than anyone else. 
You are fluent in both English and Korean. When answering the question, respond in Korean, but keep key terms, keywords, and technical terminology in English. 
Make sure to include the source of your answer, referencing the specific section or page number of the paper.


#Question:
{question}

#CONTEXT:
{context}

#Answer:
"""


# 요약을 위한 프롬프트 템플릿을 정의합니다.
summary_prompt = """Please summarize the sentence according to the following REQUEST.
    
REQUEST:
1. Summarize the main points in bullet points.
3. Write the summary in same language as the context.
4. DO NOT translate any technical terms.
5. DO NOT include any unnecessary information.
6. Summary must include important entities, numerical values.
7. Be sure to maintain the markdown format and precede each section heading and subheading with # or ##.
8. Don't include # SUMMARY in your summaries.

CONTEXT:
{context}

SUMMARY:"
"""

# 논문 전체 요약을 위한 map-reduce 프롬프트 템플릿을 정의합니다.
map_prompt = """You are a professional summarizer. 
You are given a summary list of documents and you make a summary list of this within 1 to 10 lines.
Please create a single summary of the documents according to the following REQUEST.
    
REQUEST:
1. Extract main points from a list of summaries of documents
2. Make final summaries in bullet points format.
3. Each summarized sentence must start with an emoji that fits the meaning of the each sentence.
4. Use various emojis to make the summary more interesting.
5. Write the summary in same language as the context.
6. DO NOT translate any technical terms.
7. DO NOT include any unnecessary information.
8. Be sure to maintain the markdown format and precede each section heading and subheading with # or ##.
9. Don't include # SUMMARY in your summaries.

Here is a list of summaries of documents: 
{context}

SUMMARY:"
"""


trans_prompt = """You are a translator specializing in academic papers.
    Your task is to translate an English paper into Korean.
    Please follow the given instructions carefully.

    REQUEST:
    1. Translate the content into Korean.
    2. Do not translate technical terms or key concepts; keep them in English (e.g., Cross Attention, Transformer).
    3. Maintain the original meaning without adding any unnecessary information.
    4. Make sure to preserve important entities and numerical values.
    5. Use Korean translations for natural expressions but leave awkward terms in English if necessary.
    6. Be sure to maintain the markdown format and precede each section heading and subheading with # or ##.
    7. If it's a math formula, write it in Markdown latex format.
    8. 한국어로 '요약' 이라는 제목은 빼주세요. 요약된 내용만 넣어주세요.
    9. 제목은 절대 한국어로 번역하지 말고 영어 제목 그대로 유지하세요.
    
    CONTEXT:
    {context}

    TRANSLATION:"""
