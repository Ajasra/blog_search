import json
import os
import pathlib
import textwrap

import chromadb
import ebooklib
import markdown
from bs4 import BeautifulSoup
from ebooklib import epub

from libs.gemini_api import GeminiEmbeddingFunction

db_dir = 'data/chroma_db'
db_name = "DeepLife"


def extract_text_from_markdown(file_path):
    with open(file_path, 'r') as file:
        text = file.read()
    return markdown.markdown(text)


def extract_text_from_epub(file_path):
    book = epub.read_epub(file_path)
    text = ''
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_body_content(), 'html.parser')
        text += soup.get_text()
    return text


def load_essays():
    essays = []
    essay_dir = pathlib.Path('../data/essays')
    for file_path in essay_dir.glob('*.md'):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            metadata = {}
            if 'Original URL' in content:
                metadata['url'] = content.split('Original URL: ')[-1]
            else:
                metadata['url'] = 'None'
            essays.append({'content': content, 'metadata': metadata})
    return essays


def load_books(chunks=2048):
    books = []
    book_dir = pathlib.Path('../data/books')
    for file_path in book_dir.glob('*.epub'):
        book = epub.read_epub(file_path)
        book_name = file_path.stem
        book_text = ''
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_body_content(), 'html.parser')
            book_text += soup.get_text()
        book_text = textwrap.wrap(book_text, chunks)
        for i, chunk in enumerate(book_text):
            books.append({'content': chunk, 'metadata': {'name': book_name, 'chunk': i}})
    return books


def content_to_docs(content, max=10):
    docs = []
    for i in range(min(len(content), max)):
        docs.append(content[i])
    return docs


def create_chroma_db(documents, name):
    chroma_client = chromadb.PersistentClient(path=db_dir)
    db = chroma_client.get_or_create_collection(name=name, embedding_function=GeminiEmbeddingFunction())

    for i, d in enumerate(documents):
        print(f"Upserting document {i} md: {d['metadata']}")
        try:
            db.upsert(
                documents=d['content'],
                metadatas=d['metadata'],
                ids=str(i)
            )
        except Exception as e:
            print(f"Error upserting document {i}: {e}")
    return db


def get_chroma_db(name):
    chroma_client = chromadb.Client()
    if name in chroma_client.list_collections():
        return chroma_client.get_collection(name=name, embedding_function=GeminiEmbeddingFunction())
    else:
        return None


# Main logic to load or create ChromaDB
def get_db(reindex=False):

    if not reindex and os.path.exists(db_dir):
        chroma_client = chromadb.PersistentClient(path=db_dir)
        database = chroma_client.get_collection(name=db_name, embedding_function=GeminiEmbeddingFunction())
        print("ChromaDB loaded from disk")
    else:
        content = load_essays()
        print(f"Loaded {len(content)} essays")
        content += load_books()
        print(f"Loaded {len(content)} books")
        docs = content_to_docs(content, len(content)+1)
        database = create_chroma_db(docs, db_name)
        print("ChromaDB created and saved to disk")
    return database


def get_books_links():
    with open('data/books.json', 'r') as f:
        books = json.load(f)
    return books