import streamlit as st
from lxml import etree
from google import genai
import numpy as np
import os

api_key = 'AIzaSyD7TV67mpsllnt7-Ge6RyOBkJlbocI0M_M'
client = genai.Client(api_key=api_key)

def chunks_xml(element, path=""):
    current_path = f"{path}/{element.tag}"
    text = f"Element Path: {current_path}\nTag: {element.tag}\nAttributes: {element.attrib}\n"
    if element.text and element.text.strip():
        text += f"Text: {element.text.strip()}\n"
    
    for child in element:
        text +=f"Child tag: {child.tag}\n"
        if child.text and child.text.strip():
            text += f"{child.tag}: {child.text.strip()}\n"
        if child.attrib:
            text += f"{child.tag} attributes: {child.attrib}\n"

    chunks = [text.strip()]
    
    for child in element:
        chunks.extend(chunks_xml(child, current_path))
    return chunks

def chunks_xsl(element, path=""):
    full_tag = str(element.tag)

    if "}" in full_tag:
        ns, tag = full_tag[1:].split("}", 1)
        if ns.endswith("1999/XSL/Transform"):
            full_tag = f"xsl:{tag}"
        elif ns.endswith("1999/XSL/Format"):
            full_tag = f"fo:{tag}"
        else:
            full_tag = tag

    current_path = f"{path}/{full_tag}"
    text = f"Element Path: {current_path}\nTag: {full_tag}\n"
    
    if element.attrib:
        text += f"Attributes: {element.attrib}\n"
    if element.text and element.text.strip():
        text += f"Text: {element.text.strip()}\n"

    for child in element:
        if child.text and child.text.strip():
            text += f"{child.tag}: {child.text.strip()}\n"
        if child.attrib:
            text += f"{child.tag} attributes: {child.attrib}\n"
    
    chunks = [text.strip()]

    for child in element:
        chunks.extend(chunks_xsl(child, current_path))
    return chunks


def create_embeddings(text_list, model="gemini-embedding-001", batch_size=100):
    all_embeddings =  []
    
    for i in range(0, len(text_list), batch_size):
        batch = text_list[i:i+batch_size]

        response = client.models.embed_content(
            model=model,
            contents=batch,
            config={"task_type": "SEMANTIC_SIMILARITY"}
        )
        all_embeddings.extend([e.values for e in response.embeddings])

    return all_embeddings

def cosine_similarity(a, b):
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0
    return np.dot(a,b) / (norm_a * norm_b)

def semantic_search(query, chunks, embeddings, top_k=30):
    query_embedding = client.models.embed_content(
        model="gemini-embedding-001",
        contents=[query],
        config={"task_type": "SEMANTIC_SIMILARITY"}
    ).embeddings[0].values
    scores = [cosine_similarity(query_embedding, emb) for emb in embeddings]
    top_indices = np.argsort(scores)[-top_k:][::-1]
    return "\n\n".join([chunks[i] for i in top_indices])

def generate_user_prompt(query):
    context = "\n".join(semantic_search(query, chunks, embeddings))

    user_prompt = f"Question is {query}. Here is the context: {context}"

    return user_prompt

def generate_response(system_prompt, user_message, model="gemini-2.0-flash"):
    response = client.models.generate_content(
        model=model,
        config=genai.types.GenerateContentConfig(
            system_instruction=system_prompt),
            contents=generate_user_prompt(user_message)
    )

    return response

st.title("XML/XSLT Chatbot")

uploaded_file = st.file_uploader("Upload a XML or XSL-file")




