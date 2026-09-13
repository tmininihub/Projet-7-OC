# Projet 7 OpenClassrooms — RAG d'événements parisiens

Ce projet est une API de recommandation d'événements à Paris basée sur un système **RAG** (*Retrieval-Augmented Generation*).

L'idée est simple : l'utilisateur écrit une demande en langage naturel, par exemple :

> Je cherche un événement immersif et original à Paris.

Le projet transforme cette demande en vecteur, recherche les événements les plus proches dans un index **FAISS**, puis envoie les événements retrouvés à un modèle **Mistral** afin de produire une réponse lisible et classée.

Les données proviennent du jeu de données public **OpenAgenda / OpenDataSoft**.

---

## Comment fonctionne le projet ?

```text
Question utilisateur
        ↓
Embedding de la question avec Mistral
        ↓
Recherche des événements proches avec FAISS
        ↓
Récupération des informations des événements
        ↓
Envoi de la question + des événements au LLM Mistral
        ↓
Réponse finale via l'API FastAPI
```

Le dépôt contient déjà l'index FAISS et les événements nécessaires pour utiliser le RAG sans reconstruire toute la base.

---

# Lancer le projet — étape par étape

Il n'est pas nécessaire d'installer Python, FAISS, FastAPI ou les autres bibliothèques manuellement : **Docker s'occupe de créer l'environnement complet.**

Il faut seulement installer Docker Desktop, télécharger le projet, ajouter une clé API Mistral et exécuter les commandes indiquées ci-dessous.

## Étape 1 — Installer Docker Desktop

Télécharger et installer Docker Desktop :

https://www.docker.com/products/docker-desktop/

Une fois installé, lancer Docker Desktop et attendre qu'il soit complètement démarré. Sur Windows, Docker Desktop doit rester ouvert pendant l'utilisation du projet.

## Étape 2 — Télécharger le projet

### Méthode la plus simple : Download ZIP

Sur cette page GitHub :

1. cliquer sur le bouton vert **Code** ;
2. cliquer sur **Download ZIP** ;
3. décompresser le fichier ZIP dans un dossier de votre choix.

### Ou avec Git

Si Git est déjà installé, ouvrir un terminal et exécuter :

```bash
git clone https://github.com/tmininihub/Projet-7-OC.git
cd Projet-7-OC
```

## Étape 3 — Ajouter une clé API Mistral

Le projet utilise Mistral pour créer les embeddings et générer la réponse finale. Il faut donc disposer d'une clé API Mistral.

Dans le dossier du projet, créer un fichier nommé exactement :

```text
.env
```

Puis écrire dedans :

```text
MISTRAL_API_KEY=VOTRE_CLE_MISTRAL
```

Le dossier doit alors ressembler à ceci :

```text
Projet-7-OC/
├── .env
├── Dockerfile
├── main.py
├── requirements.txt
├── FAISS_Index
├── events.joblib
└── dico_event
```

⚠️ Le fichier `.env` contient une clé privée et ne doit pas être publié ou partagé.

## Étape 4 — Ouvrir un terminal dans le dossier du projet

Sur Windows :

1. ouvrir le dossier `Projet-7-OC` dans l'Explorateur de fichiers ;
2. cliquer dans la barre d'adresse du dossier ;
3. écrire `powershell` ;
4. appuyer sur Entrée.

Un terminal PowerShell s'ouvre directement dans le bon dossier. Il doit s'agir du dossier contenant le `Dockerfile`.

## Étape 5 — Construire l'image Docker

Dans le terminal, exécuter :

```bash
docker build -t project7-rag .
```

Cette étape peut prendre quelques minutes la première fois. Docker crée l'environnement et installe automatiquement les dépendances nécessaires.

Quand la commande est terminée sans erreur, l'image `project7-rag` est prête.

## Étape 6 — Lancer l'API

Exécuter :

```bash
docker run --env-file .env -p 8000:8000 project7-rag
```

Après quelques secondes, le terminal doit afficher quelque chose ressemblant à :

```text
Application startup complete.
Uvicorn running on http://0.0.0.0:8000
```

Le serveur est alors lancé. Le terminal reste occupé pendant que l'API fonctionne : c'est normal.

Dans un navigateur, ouvrir :

http://localhost:8000/docs

---

# Utiliser le RAG

La page `http://localhost:8000/docs` permet de tester l'API directement, sans écrire de code.

Dans cette page :

1. ouvrir **POST `/RAG`** ;
2. cliquer sur **Try it out** ;
3. écrire une question dans le champ `prompt` ;
4. cliquer sur **Execute**.

Par exemple :

```text
Je cherche un événement immersif et original à Paris
```

L'API transforme la question en embedding, recherche les événements les plus proches dans FAISS, puis Mistral classe les résultats et génère la réponse finale.

---

# Reconstruire la base vectorielle

Une seconde route est disponible :

```text
POST /Rebuild
```

Elle permet de télécharger à nouveau les événements depuis OpenDataSoft, de recréer leurs embeddings et de reconstruire l'index FAISS.

Cette opération est beaucoup plus longue et effectue de nombreux appels à l'API Mistral. **Elle n'est pas nécessaire pour simplement lancer et tester le RAG**, puisque le dépôt contient déjà l'index et les données nécessaires.
