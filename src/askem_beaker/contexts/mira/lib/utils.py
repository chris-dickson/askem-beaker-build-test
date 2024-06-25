import glob
import json
import logging
import os

import chromadb
import openai

logger = logging.getLogger(__name__)


def start_chromadb(collection_name="examples", path="/home/jupyter/chromadb_functions_mira"):
    chroma_client = chromadb.PersistentClient(path=path)
    print('collections are:')
    print(chroma_client.list_collections())

    collection = chroma_client.get_or_create_collection(name=collection_name)

    openai.api_key = os.environ["OPENAI_API_KEY"]
    return collection


def query_examples(query, n_results=5):
    u_query_collection = start_chromadb(collection_name="user_queries")
    examples_collection = start_chromadb(collection_name="examples")
    results = u_query_collection.query(query_texts=[query], n_results=n_results)
    examples_ids = results["ids"][0]
    examples = examples_collection.get(ids=examples_ids)["documents"]

    print(examples)

    return examples


def query_docs(query, collection_name="documentation_index", path="/home/jupyter/chromadb_functions_mira", n_results=5):
    collection = start_chromadb(collection_name=collection_name, path=path)
    result = collection.query(query_texts=[query], n_results=n_results)
    text = ""
    for i in range(len(result["ids"][0])):
        text += f"Documentation from {result['ids'][0][i]} :\n{result['documents'][0][i]}"

    return text


def query_functions_classes(
    query, collection_name="function_index", path="/home/jupyter/chromadb_functions_mira", n_results=5
):
    collection = start_chromadb(collection_name=collection_name, path=path)
    result = collection.query(query_texts=[query], n_results=n_results)
    text = ""
    for i in range(len(result["ids"][0])):
        text += f"Information related to for function or class: {result['ids'][0][i]} :\n{result['documents'][0][i]}\n"

    return text
