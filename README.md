# Projet 7 OpenClassrooms — Système de recommandation d'événements culturels par RAG

Ce projet propose une **API de recommandation d'événements culturels à Paris** à partir de requêtes formulées en langage naturel. Il repose sur une architecture **RAG** (*Retrieval-Augmented Generation*) combinant recherche sémantique, base vectorielle et modèle de langage.

L'objectif est de retrouver des événements proches de l'intention de l'utilisateur, puis de les présenter sous une forme structurée et lisible.

## 1. Architecture générale

Le système comporte deux étapes complémentaires : la **préparation des données** et la **recherche avec génération de réponse**.

```text
                 INDEXATION
OpenAgenda / OpenDataSoft
          │
          ▼
Extraction : titre, description, date, lieu
          │
          ▼
Découpage en segments de 500 caractères
          │
          ▼
Embeddings Mistral — 1 024 dimensions
          │
          ▼
Index vectoriel FAISS + association aux événements
          │
          ▼
Sauvegarde des données et de l'index


                  RECOMMANDATION
Question en langage naturel
          │
          ▼
Embedding de la question
          │
          ▼
Recherche des 5 segments les plus proches (FAISS)
          │
          ▼
Récupération des événements et suppression des doublons
          │
          ▼
Mistral Small : sélection et classement des résultats
          │
          ▼
Réponse JSON via FastAPI
```

La recherche sémantique permet d'identifier des événements à partir du **sens de la demande**, sans dépendre uniquement de la présence de mots-clés identiques.

## 2. Données et traitement

### Source

Les données proviennent du jeu public **OpenAgenda**, accessible par l'API **OpenDataSoft**. La construction de l'index cible des fiches d'événements localisées à Paris et utilise un filtre sur leur année de mise à jour.

[Accéder au jeu de données OpenAgenda](https://public.opendatasoft.com/explore/dataset/evenements-publics-openagenda/)

### Préparation et vectorisation

Pour chaque événement, quatre informations sont réunies :

- **Titre**
- **Description**
- **Date**
- **Lieu**

Le texte est découpé en **segments de 500 caractères**. Chaque segment est converti en un vecteur de **1 024 dimensions** avec `mistral-embed-2312`.

Ces vecteurs sont enregistrés dans **FAISS**. Un dictionnaire conserve leur association avec les événements d'origine pour restituer les informations complètes après la recherche.

L'index et les données sont sauvegardés localement avec **Joblib**, ce qui permet d'interroger le système sans recalculer les embeddings à chaque lancement.

### Recherche et génération

Lorsqu'une requête est reçue :

1. La demande est transformée en embedding avec le même modèle que les événements.
2. FAISS recherche les **5 segments les plus proches**, avec une distance euclidienne (`IndexFlatL2`).
3. Les événements associés sont récupérés et les doublons de titres sont supprimés.
4. **Mistral Small** examine les candidats, écarte ceux jugés hors sujet et classe les autres selon la demande.
5. L'API renvoie les résultats dans un objet JSON contenant le titre, la description, la date et l'emplacement.

Les cinq voisins recherchés sont des **segments**, et non nécessairement cinq événements distincts.

## 3. Technologies et choix techniques

| Technologie | Utilisation | Intérêt dans le projet |
|---|---|---|
| **Python** | Pipeline de traitement et logique applicative | Écosystème adapté à l'IA et au traitement des données |
| **OpenAgenda / OpenDataSoft** | Collecte d'événements | Données culturelles publiques |
| **Mistral Embed** (`mistral-embed-2312`) | Vectorisation des textes et des questions | Recherche fondée sur la proximité sémantique |
| **FAISS** (`IndexFlatL2`) | Recherche des vecteurs les plus proches | Recherche vectorielle exacte sur l'index local |
| **Mistral Small** (`mistral-small-2603`) | Sélection, classement et formulation | Production d'une réponse adaptée à la demande |
| **LangChain** | Intégration des modèles Mistral à l'application | Simplification des interactions avec les modèles |
| **FastAPI / Uvicorn** | Exposition des fonctionnalités sous forme d'API HTTP | Interface simple, documentation Swagger intégrée |
| **Joblib** | Persistance de l'index et des données | Réutilisation des résultats de l'indexation |
| **Docker** | Exécution de l'application | Environnement reproductible |

L'architecture sépare la récupération des informations et leur reformulation. Le modèle génératif travaille ainsi sur des **événements extraits de la base** plutôt que de produire des suggestions sans source de données.

## 4. API

L'application expose deux routes principales :

| Route | Méthode | Fonction |
|---|---|---|
| `/Build` | POST | Collecte les données et construit les représentations vectorielles ainsi que l'index FAISS |
| `/RAG` | POST | Recherche et recommande des événements en réponse à une question |

### Exemple de requête

`POST /RAG` reçoit le paramètre texte `prompt` dans l'URL :

```bash
curl -X POST "http://localhost:8000/RAG?prompt=Je%20cherche%20un%20event%20sur%20le%20spatial"
```

Format de réponse :

```json
{
  "Event 1": {
    "Titre": "Titre de l'événement",
    "Description": "Description courte",
    "Date": "Date de l'événement",
    "Emplacement": "Lieu"
  }
}
```

La documentation interactive de l'API est accessible à l'adresse **http://localhost:8000/docs** une fois le serveur démarré.

## 5. Tests et évaluation

### Tests fonctionnels

Les vérifications implémentées dans `test_main.py` portent sur :

- la taille maximale des segments (**500 caractères**) ;
- la dimension des embeddings (**1 024**) ;
- le code HTTP retourné par `/RAG` (**200** pour la requête testée) ;
- la présence du thème « jazz » dans une réponse à une question sur le jazz.

Les vérifications de génération d'embeddings et de réponse RAG font intervenir les services Mistral : elles relèvent donc aussi de **tests d'intégration**, et pas uniquement de tests unitaires isolés.

### Couverture de code

Les mesures de couverture réalisées donnent :

| Périmètre | Couverture |
|---|---:|
| Application complète | **67 %** |
| Application hors fonction de construction `Build` | **100 %** |

La différence correspond à la partie consacrée à la construction de l'index, non exercée par les tests considérés. Ces pourcentages mesurent l'exécution des lignes de code, pas directement la précision des recommandations.

### Évaluation qualitative

Une recherche portant sur le **domaine spatial** a produit cinq propositions en rapport avec le sujet :

| Événement retourné | Lieu |
|---|---|
| Objectifs Terre, la révolution des satellites | Cité des sciences et de l'industrie |
| Journées Portes Ouvertes à l'Agence spatiale européenne | Siège de l'Agence spatiale européenne |
| Les conférences — Explorer l'espace, mieux habiter notre planète | Cité des sciences et de l'industrie |
| Visite commentée de l'exposition Mission spatiale | Cité des sciences et de l'industrie |
| Rendez-vous avec l'espace : Week-end spatial | Cité des sciences et de l'industrie |

**Observation :** les cinq propositions correspondent thématiquement à la requête. Cet exemple met en évidence la capacité du système à retrouver des contenus liés à un sujet commun.

## 6. Limites et perspectives d'amélioration

Les premiers résultats montrent l'intérêt de la recherche sémantique, mais plusieurs axes pourraient améliorer la pertinence et la robustesse du système.

| Axe | Limite actuelle | Amélioration envisagée |
|---|---|---|
| **Actualité des événements** | Certaines recommandations peuvent concerner des dates passées | Filtrage explicite des dates de tenue et exclusion des événements expirés |
| **Découpage du texte** | Segments fixes de 500 caractères, pouvant interrompre une phrase | Découpage sémantique ou avec chevauchement |
| **Diversité des résultats** | La recherche s'effectue sur cinq segments, parfois issus d'un même événement | Récupération plus large, puis sélection d'événements distincts |
| **Indexation** | Création des embeddings segment par segment | Traitement par lots pour réduire le nombre d'appels |


## 7. Installation et démonstration

### Prérequis

- Docker Desktop
- Une clé API Mistral

### Récupération du projet

```bash
git clone https://github.com/tmininihub/Projet-7-OC.git
cd Projet-7-OC
```

Créer un fichier `.env` à la racine :

```dotenv
MISTRAL_API_KEY=VOTRE_CLE_MISTRAL
```

### Démarrage avec Docker

```bash
docker build -t project7-rag .
docker run --env-file .env -p 8000:8000 project7-rag
```

Accéder ensuite à **http://localhost:8000/docs**, puis utiliser la route `POST /RAG` avec une question en langage naturel.

Le dépôt contient un index et des données déjà enregistrés, permettant une démonstration sans reconstruction préalable de la base vectorielle.

## 8. Organisation du projet

```text
Projet-7-OC/
├── main.py            # Pipeline d'indexation et API RAG
├── test_main.py       # Vérifications fonctionnelles
├── events.joblib      # Données d'événements
├── dico_event         # Association des segments aux événements
├── FAISS_Index        # Index vectoriel
├── requirements.txt   # Dépendances Python
├── Dockerfile         # Conteneurisation de l'API
└── README.md          # Documentation technique
```

---

*Projet 7 — Formation OpenClassrooms. Système RAG de recommandation d'événements culturels à Paris.*
