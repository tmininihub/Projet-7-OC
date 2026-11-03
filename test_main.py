import main
from main import app, RAG, chunkstring
from fastapi.testclient import TestClient
from langchain_mistralai import ChatMistralAI, MistralAIEmbeddings
import numpy as np

texte = str({'Event 1': {'Titre': 'Journées du Matrimoine 2025 - Les Elles du Jazz', 'Description': 'Atelier ludique autour d’un puzzle et d’un site riche en playlists, vidéos et biographies, permettant de découvrir des musiciennes et compositrices américaines', 'Date': '20 et 21 septembre 2025', 'Emplacement': 'Cité Audacieuse'}, 'Event 2': {'Titre': 'Le ministère de la Culture célèbre le jazz dans les jardins du Palais-Royal', 'Description': 'Le ministère de la Culture vous donne rendez-vous dans les jardins du Palais-Royal à l’occasion de la Fête de la musique, pour une journée de concerts consacrée aux multiples courants du jazz, des années 1910 à aujourd’hui.', 'Date': 'Dimanche 21 juin, 13h15', 'Emplacement': 'Jardins du Palais-Royal'}, 'Event 3': {'Titre': 'Une histoire du Jazz avec La Sirène de Paris', 'Description': 'Le 21 juin, pour la fête de la musique LaSirène se produit au kiosque du Luxembourg (kiosque à musique du Luxembourg, rue Vaugirard, 6e arr.).', 'Date': 'Dimanche 21 juin, 14h00', 'Emplacement': 'Kiosque à Musique du Luxembourg'}, 'Event 4': {'Titre': 'ZootFor Kids / Atelier Jazz Jeune Public', 'Description': 'Le Zoot Collectif invite les enfants à plonger dans l’univers du jazz !', 'Date': 'Dimanche 11 octobre, 15h00', 'Emplacement': 'JASS CLUB'}, 'Event 5': {'Titre':'Analogik Stomp Machine / Ft. Margherita Gruden & Lilou Claverie', 'Description': "Le saxophone ? Pierre Lapprand est tombé dedans à l’âge de 7 ans. Il n'a depuis cessé d'expérimenter, explorant les recoins les plus libres et incisifs du jazz moderne avec Congé Spatial et Chrones, avant de créer un univers électronique à l'énergie tellurique avec Pierre & The Stompers.", 'Date': 'Samedi 30 mai, 19h30, 21h30, 22h30', 'Emplacement': 'JASS CLUB'}})
embeddings = MistralAIEmbeddings(model="mistral-embed-2312")

def test_RAG(texte):
    chunks = list(chunkstring(texte, 500))
    for i in chunks:
        assert len(i)<=500
        embedded_chunk = np.array(embeddings.embed_query(i))
        shape_embedded = embedded_chunk.shape
        assert shape_embedded[0] == 1024

    Client = TestClient(app)
    response = Client.post("/RAG",params={"prompt": "Je cherche un event de Jazz"})

    assert response.status_code == 200
    response = response.json()
    texte = " ".join(str(v) for v in response.values()).lower()
    assert "jazz" in texte


test_RAG(texte)