import os

import dotenv
import google.generativeai as genai
import markdown
from chromadb import EmbeddingFunction, Documents, Embeddings

dotenv.load_dotenv()

# Get the environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

EMBEDDING_DIMENSION = 768


def get_all_models():
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)

class GeminiEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        model = 'models/text-embedding-004'
        title = "DeepLife"
        embeddings = genai.embed_content(model=model, content=input, task_type="retrieval_document", title=title)["embedding"]
        # Ensure the embeddings have the correct dimension
        if len(embeddings[0]) != EMBEDDING_DIMENSION:
            raise ValueError(f"Expected embedding dimension {EMBEDDING_DIMENSION}, but got {len(embeddings[0])}")
        return embeddings


def format_content(content):
    # if there more then one \n in a row, replace it with one \n
    content = content.replace('\n\n\n\n\n', '\n')
    content = content.replace('\n\n\n\n', '\n')
    content = content.replace('\n\n\n', '\n')
    content = content.replace('\n\n', '\n')
    content = markdown.markdown(content)
    return content


def get_relevant_passage(query, db, n_results=5):
    passage = db.query(query_texts=[query], n_results=n_results)
    result = ''
    for i in range(len(passage['documents'][0])):
        content = passage['documents'][0][i]
        content = format_content(content)
        metadata = passage['metadatas'][0][i]
        # convert metadata dictionary to string
        metadata = ', '.join([f'{k}: {v}' for k, v in metadata.items()])
        result += "source: " + metadata + ' | content: ' + content + '\n-------------------\n'
    return result, passage['documents'][0], passage['metadatas'][0]


def make_prompt(query, relevant_passage):
    escaped = relevant_passage.replace("'", "").replace('"', "").replace("\n", " ")
    prompt = ("""You are a productivity and optimisation guru focused on the concept of deep life, \
    that answers questions using text from the context included below. \
    Be sure to respond in a complete sentence, being comprehensive, including all relevant background information. \
    - If the context is irrelevant to the answer, you may ignore it. \
    - Give the required definitions, explanations, step by step instructions, and examples. \
    In the format of a markdown file with headers, paragraphs and lists to the following question: \
    FORMAT:
    ---------
    ### DEFINITION
    ...
    ### EXPLANATION
    ...
    ### INSTUCTIONS
    ...
    ### EXAMPLES
    1. ...
    ---------
    QUESTION: '{query}'
    CONTEXT: '{relevant_passage}'

    ANSWER:
    """).format(query=query, relevant_passage=escaped)
    return prompt


def generate_answer(query, db, model = 'gemini-1.5-pro-latest'):
    passage, content, metadata = get_relevant_passage(query, db, n_results=10)
    # print(passage)
    prompt = make_prompt(query, passage)
    model = genai.GenerativeModel(model)
    answer = model.generate_content(prompt)

    if answer.text:
        return answer.text, content, metadata
    else:
        return answer, content, metadata