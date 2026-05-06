import streamlit as st
from lxml import etree
from google import genai
import numpy as np
import os

api_key = ''
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
    return [chunks[i] for i in top_indices]

def generate_user_prompt(query, chunks, embeddings):

    context_chunks = semantic_search(query, chunks, embeddings)
    context_text = "\n".join(context_chunks)
    return f"Question is {query}. Here is the context: {context_text}"

def generate_response(system_prompt, user_query , chunks, embeddings, model="gemini-2.0-flash"):
    response = client.models.generate_content(
        model=model,
        config=genai.types.GenerateContentConfig(
            system_instruction=system_prompt),
            contents=generate_user_prompt(user_query, chunks, embeddings)
    )

    return response.text

st.title("XML/XSLT Chatbot")

uploaded_file = st.file_uploader("Upload a XML or XSL-file")

if uploaded_file:

    file_name = uploaded_file.name
    file_text = os.path.splitext(file_name)[1].lower()
    file_type = file_text.replace(".","")

    tree = etree.parse(uploaded_file)
    root = tree.getroot()

    if file_type == "xml":
        chunks = chunks_xml(root)
    elif file_type == "xsl":
        chunks = chunks_xsl(root)

    st.write(f"Filetype: {file_type.upper()}")

    embeddings = create_embeddings(chunks)
    st.session_state['chunks'] = chunks
    st.session_state['embeddings'] = embeddings

 
    system_prompt = (
    "You are a smart AI assistant that analyzes XML and XSl-files."
    "All the information will be retrieved via RAG from the relevant context, no hardcoded values."
    "Answer shortly, precisely and correctly based on the context."
    "Answer the questions directly, without extra explanations."
    "If the question is about the root-element, provide only the tag."
    "If the question is a value, attribute, id or text, provide only the value."
    "If the question contains the words 'path' or 'XPath', return the full absolute path from the root and include the predicates needed."
    "If multiple elements share the same tags, the full absolute path must include a predicate that ditinguishes the correct element based on relevant attributes or child elements from the context, and it must never be generic."
    "If the question is about a element that does not exist in the chunked RAG-context, respond: 'Information is not avaible in context'"
    "If the question is about a XSL-element, get information from select- or match attribute according to question"
)
        
    if file_type == "xml":

        q1 = "What is the root element?"
        q2 = "Give me all unique elements in this XML-file?"

        a1= generate_response(system_prompt, q1, chunks, embeddings)
        a2= generate_response(system_prompt, q2, chunks, embeddings)

        col1,col2 = st.columns(2)

        with col1:
            st.markdown("### Question 1")
            st.info(q1)
            st.success(a1)
        
        with col2:
            st.markdown("### Question 2")
            st.info(q2)
            st.success(a2)

    if file_type == "xsl":

        q1 = "What templates (match/select) are used in this XSL-file?"
        q2 = "What XSL instructions are used?"

        a1 = generate_response(system_prompt, q1, chunks, embeddings)
        a2 = generate_response(system_prompt, q2, chunks, embeddings)

        col3,col4 = st.columns(2)

        with col3:
            st.markdown("### Question 1")
            st.info(q1)
            st.success(a1)

        with col4:
            st.markdown("### Question 2")
            st.info(q2)
            st.success(a2)

        query = st.text_input("Write your question here")

        if query:
                anwser = generate_response(system_prompt, query ,st.session_state['chunks'], st.session_state['embeddings'])
                st.text_area("Answer from Chatbot", value=anwser, height=300)






