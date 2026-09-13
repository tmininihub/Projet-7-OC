import dotenv
import os
import pandas as pd
import requests
import fastapi
import uvicorn
import requests
import joblib
import numpy as np
import faiss
from langchain_mistralai import ChatMistralAI, MistralAIEmbeddings
from langchain_community.vectorstores import FAISS
from fastapi import FastAPI
from mistralai.client import Mistral
from dotenv import load_dotenv

from fastapi import FastAPI

load_dotenv()

api_key = os.environ.get("MISTRAL_API_KEY")
client = Mistral(api_key=api_key)

app = FastAPI()

dico_event = joblib.load("dico_event")
all_events = joblib.load("events.joblib")
index = joblib.load("FAISS_Index")

embeddings = MistralAIEmbeddings(model="mistral-embed-2312")
llm = ChatMistralAI(model="mistral-small-2603")

def chunkstring(string, length):
    return (string[0+i:length+i] for i in range(0, len(string), length))

@app.post("/RAG")
def RAG(prompt: str):
    embedding_prompt = embeddings.embed_query(prompt)
    embedding_prompt = np.array(embedding_prompt)
    embedding_prompt = embedding_prompt[np.newaxis,:]
    distances,chunks = index.search(embedding_prompt,k=2)

    list_events = []
    list_tempo = []
    for i in chunks:
        for chunk in i:
            for key, value in dico_event.items():
                if chunk in value:
                    if all_events[key]['title_fr'] in list_tempo:
                        continue
                    else:
                        list_tempo.append(all_events[key]['title_fr'])
                        list_events.append({"titre": all_events[key]['title_fr'],"description": all_events[key]['longdescription_fr'], "localisation": all_events[key]['location_name'],"date": all_events[key]['daterange_fr']})

    messages = [
        (
            "system",
            """Tu es un guide spécialisé dans les événements.
    Classe TOUS les événements du plus adapté au moins adapté.

    Pour chaque événement, réponds exactement comme ceci :
    Titre | Description courte | Date | Emplacement

    Un événement par ligne.
    N'ajoute aucun autre texte."""
        ),
        ("human",
        f"""Demande : {prompt}
        Événements disponibles :{list_events}""")]

    reponse = llm.invoke(messages)

    dico_return = {}
    index_event = 0
    for i, event in enumerate(reponse.content.splitlines(), start=1):
        infos = event.split(" | ")

        if len(infos) == 4:
            index_event+=1
            dico_return[f"Event {index_event}"] = {
        "Titre": infos[0],
        "Description": infos[1],
        "Date": infos[2],
        "Emplacement": infos[3]
    }
    print(dico_return)
    return dico_return


@app.post("/Rebuild")
def Rebuild():
    url = "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/evenements-publics-openagenda/exports/json"

    params = {
        "refine": [
            "location_city:Paris",
            "updatedat:2026"
        ]
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    all_events = response.json()
    joblib.dump(all_events, "events.joblib")

    dico_event = {}
    list_embedding = []
    index_event = 0
    index_chunk = 0

    for i in range(len(all_events)):
        dico_event[index_event] = []
        chunks_description = list(chunkstring(all_events[i]['title_fr'] + all_events[i]['longdescription_fr'] + all_events[i]['daterange_fr'] + all_events[i]['location_name'],500))
        for chunk in chunks_description:
            dico_event[index_event].append(index_chunk)
            index_chunk+=1
            Embedding_data = client.embeddings.create(model="mistral-embed-2312",inputs=[chunk])
            list_embedding.append(Embedding_data.data[0].embedding)
        index_event+=1
        if len(list_embedding) % 100 == 0:
            joblib.dump(list_embedding, "list_embedding")
    joblib.dump(list_embedding, "list_embedding")
    joblib.dump(dico_event, "dico_event")

    tableau_embedding = np.array(list_embedding)
    print(tableau_embedding.shape)

    index = faiss.IndexFlatL2(1024)
    index.add(tableau_embedding)
    joblib.dump(index, "FAISS Index")

    return f"Rebuild terminé : {len(all_events)} événements et {len(list_embedding)} embeddings créés."