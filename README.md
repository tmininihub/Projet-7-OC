# Projet 7 OpenClassrooms — RAG d'événements parisiens

Ce projet est une API de recommandation d'événements à Paris basée sur un système **RAG** (*Retrieval-Augmented Generation*).

L'idée est simple : l'utilisateur écrit une demande en langage naturel, par exemple :

> Je cherche un événement immersif et original à Paris.

Le projet transforme cette demande en vecteur, recherche les événements les plus proches dans un index **FAISS**, puis envoie les événements retrouvés à un modèle **Mistral** afin de produire une réponse lisible et classée.

Les données proviennent du jeu de données public **OpenAgenda / OpenDataSoft**.

---

## Comment fonctionne le projet ?

Le fonctionnement général est le suivant :

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

Le dépôt contient déjà les fichiers nécessaires pour utiliser l'index existant :

- `FAISS_Index` : index vectoriel utilisé pour la recherche ;
- `events.joblib` : événements enregistrés ;
- `dico_event` : correspondance entre les événements et les chunks indexés ;
- `main.py` : API FastAPI et logique RAG ;
- `requirements.txt` : dépendances Python ;
- `Dockerfile` : instructions permettant de construire l'application dans Docker.

---

# Lancer le projet — guide pas à pas pour débutant

Il n'est pas nécessaire d'installer Python, FAISS, FastAPI ou les autres bibliothèques manuellement.

**Docker s'occupe de créer l'environnement complet.**

Il faut seulement :

1. installer Docker Desktop ;
2. télécharger ce projet ;
3. ajouter une clé API Mistral ;
4. exécuter deux commandes Docker.

---

## Étape 1 — Installer Docker Desktop

Télécharger et installer **Docker Desktop** :

https://www.docker.com/products/docker-desktop/

Une fois installé, lancer Docker Desktop et attendre qu'il soit complètement démarré.

> Sur Windows, Docker Desktop doit rester ouvert pendant l'utilisation du projet.

---

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

---

## Étape 3 — Créer une clé API Mistral

Le projet utilise les modèles Mistral pour créer les embeddings et générer la réponse finale.

Il faut donc disposer d'une **clé API Mistral**.

Créer/récupérer une clé depuis votre compte Mistral, puis aller dans le dossier du projet.

Créer un fichier nommé exactement :

```text
.env
```

Dans ce fichier, écrire :

```text
MISTRAL_API_KEY=VOTRE_CLE_MISTRAL
```

Exemple de structure du dossier :

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

⚠️ **Ne jamais publier ou partager le fichier `.env`**, car il contient votre clé privée.

---

## Étape 4 — Ouvrir un terminal dans le dossier du projet

### Sur Windows

Dans l'Explorateur de fichiers :

1. ouvrir le dossier `Projet-7-OC` ;
2. cliquer dans la barre d'adresse du dossier ;
3. écrire `powershell` ;
4. appuyer sur Entrée.

Un terminal PowerShell s'ouvre directement au bon endroit.

Vous devez être dans le dossier contenant le `Dockerfile`.

---

## Étape 5 — Construire l'image Docker

Dans le terminal, exécuter :

```bash
docker build -t project7-rag .
```

Cette étape peut prendre quelques minutes la première fois.

Docker va notamment :

- télécharger l'environnement Python ;
- installer les dépendances du projet ;
- copier les fichiers du projet dans l'image Docker.

Quand cette commande est terminée sans erreur, l'image `project7-rag` est prête.

> Cette étape n'est généralement nécessaire qu'une première fois, ou après une modification du projet.

---

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

Le serveur est alors lancé.

**Le terminal reste occupé tant que l'API fonctionne : c'est normal.**

Il ne faut pas ouvrir `http://0.0.0.0:8000` dans le navigateur.

Ouvrir plutôt :

http://localhost:8000/docs

---

# Utiliser l'API

FastAPI fournit automatiquement une interface Swagger accessible ici :

http://localhost:8000/docs

Elle permet de tester l'application sans écrire de code.

## Faire une recherche avec le RAG

Dans Swagger :

1. ouvrir **POST `/RAG`** ;
2. cliquer sur **Try it out** ;
3. écrire une question dans le champ `prompt` ;
4. cliquer sur **Execute**.

Exemple :

```text
Je cherche un événement immersif et original à Paris
```

L'API recherche les événements les plus proches dans FAISS, puis Mistral les classe et génère la réponse finale.

---

## Recréer la base vectorielle

L'API possède également une route :

```text
POST /Rebuild
```

Cette route :

1. télécharge à nouveau les événements depuis OpenDataSoft ;
2. découpe leur contenu en chunks ;
3. recrée les embeddings avec Mistral ;
4. reconstruit l'index FAISS ;
5. sauvegarde les nouvelles données.

⚠️ Cette opération peut être **beaucoup plus longue** et effectuer de nombreux appels à l'API Mistral. Elle n'est pas nécessaire pour simplement tester `/RAG` avec l'index déjà fourni dans le dépôt.

---

# Arrêter le projet

Dans le terminal dans lequel Docker est lancé, appuyer sur :

```text
Ctrl + C
```

Le serveur s'arrête.

Pour le relancer plus tard, il suffit normalement de refaire :

```bash
docker run --env-file .env -p 8000:8000 project7-rag
```

Il n'est pas nécessaire de refaire `docker build` tant que le projet n'a pas changé.

---

# Problèmes fréquents

### `docker` n'est pas reconnu

Docker Desktop n'est probablement pas installé ou n'est pas correctement démarré.

### Impossible de se connecter à Docker / Docker Engine

Ouvrir Docker Desktop et attendre qu'il ait fini de démarrer, puis réessayer.

### Erreur liée à `MISTRAL_API_KEY`

Vérifier que le fichier `.env` existe dans le dossier du projet et contient bien :

```text
MISTRAL_API_KEY=VOTRE_CLE
```

### Le terminal semble bloqué après `Uvicorn running...`

C'est normal. Le serveur est simplement en train d'attendre des requêtes.

Ouvrir :

http://localhost:8000/docs

### Message concernant Hugging Face / `HF_TOKEN`

Un avertissement indiquant que les requêtes vers Hugging Face ne sont pas authentifiées peut apparaître au démarrage. Ce message n'empêche pas nécessairement l'API de fonctionner.

### Le port 8000 est déjà utilisé

Il est possible d'utiliser un autre port sur le PC, par exemple :

```bash
docker run --env-file .env -p 8080:8000 project7-rag
```

Puis ouvrir :

http://localhost:8080/docs

---

# Technologies utilisées

- **Python**
- **FastAPI** pour exposer le système sous forme d'API REST
- **Docker** pour rendre l'application facilement exécutable sur une autre machine
- **FAISS** pour la recherche vectorielle
- **Mistral AI** pour les embeddings et la génération de texte
- **LangChain** pour l'intégration des modèles Mistral
- **OpenDataSoft / OpenAgenda** pour les données d'événements
- **Joblib** pour sauvegarder et recharger les données et l'index

---

## Résumé ultra-court

Pour quelqu'un qui possède déjà Docker et une clé Mistral :

```bash
git clone https://github.com/tmininihub/Projet-7-OC.git
cd Projet-7-OC
```

Créer `.env` :

```text
MISTRAL_API_KEY=VOTRE_CLE_MISTRAL
```

Puis :

```bash
docker build -t project7-rag .
docker run --env-file .env -p 8000:8000 project7-rag
```

Enfin ouvrir :

http://localhost:8000/docs
