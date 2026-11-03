# Projet 7 OpenClassrooms — Puls-Events

API de recommandation d'événements culturels à Paris fondée sur une architecture **RAG** (*Retrieval-Augmented Generation*).

Le système associe une recherche sémantique dans un index **FAISS** à la génération d'une réponse par un modèle **Mistral**. Un utilisateur peut, par exemple, demander : « Je cherche un événement sur le spatial à Paris ».

> **État du projet :** prototype fonctionnel avec index et données pré-calculés, API FastAPI et conteneurisation Docker. Les éléments d'évaluation présentés ci-dessous distinguent les observations communiquées des mesures non encore établies.

## Sommaire

1. [Architecture et parcours d'une requête](#architecture-et-parcours-dune-requête)
2. [Données et construction de l'index](#données-et-construction-de-lindex)
3. [Choix technologiques et modèles](#choix-technologiques-et-modèles)
4. [Installation et exécution avec Docker](#installation-et-exécution-avec-docker)
5. [API et exemples d'utilisation](#api-et-exemples-dutilisation)
6. [Tests, couverture et évaluation](#tests-couverture-et-évaluation)
7. [Résultats observés et limites](#résultats-observés-et-limites)
8. [Pistes d'amélioration](#pistes-damélioration)
9. [Structure du dépôt](#structure-du-dépôt)

## Architecture et parcours d'une requête

```text
                   CONSTRUCTION DE L'INDEX (/Build)
OpenDataSoft / OpenAgenda (événements parisiens)
             |
             v
Champs : titre + description + date + lieu
             |
             v
Découpage en segments de 500 caractères
             |
             v
Mistral Embeddings (mistral-embed-2312)
             |
             v
Vecteurs de 1 024 dimensions -> FAISS IndexFlatL2
             |
             +-> correspondance segment <-> événement
             |
             v
  Sauvegarde locale (joblib)


                      RECHERCHE (/RAG)
Question de l'utilisateur
             |
             v
Embedding de la question (même modèle Mistral)
             |
             v
Recherche des 5 segments les plus proches dans FAISS
             |
             v
Remontée aux événements et suppression des doublons de titres
             |
             v
Mistral Small : sélection, classement et mise en forme
             |
             v
Réponse JSON servie par FastAPI
```

Le terme *RAG* décrit ici le fait de fournir au modèle génératif des événements récupérés dans une base externe plutôt que de lui demander de produire une recommandation sans contexte.

### Détails de la recherche

Dans `main.py`, la fonction `RAG(prompt: str)` :

1. convertit la question en vecteur ;
2. récupère les **5 segments** les plus proches avec `index.search(..., k=5)` ;
3. retrouve les événements auxquels ces segments appartiennent grâce à `dico_event` ;
4. dédoublonne les événements par titre ;
5. demande au LLM de classer les résultats et d'écarter ceux qui ne correspondent pas ;
6. transforme les lignes structurées produites par le LLM en objet JSON.

**Important :** cinq segments récupérés ne signifient pas nécessairement cinq événements distincts. Plusieurs segments peuvent provenir du même événement, et le LLM peut écarter certains candidats.

## Données et construction de l'index

**Source :** jeu public OpenAgenda accessible par l'API d'export OpenDataSoft :

```text
https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/evenements-publics-openagenda/exports/json
```

La fonction `Build()` utilise des paramètres de filtrage comportant `location_city:Paris` et `updatedat:2026`. Ce dernier critère concerne la mise à jour d'une fiche, et **ne garantit pas que la date de tenue de l'événement soit en 2026 ou postérieure à la date de recherche**.

Pour chaque événement, le programme concatène les champs `title_fr`, `longdescription_fr`, `daterange_fr` et `location_name`, puis réalise un découpage **par blocs de 500 caractères**, sans chevauchement ni prise en compte des frontières de phrases.

Chaque segment est transformé en embedding, puis ajouté à un index `faiss.IndexFlatL2(1024)`. Ce type d'index effectue une recherche exacte selon la distance euclidienne au carré. Le dictionnaire `dico_event` permet de faire correspondre les indices des segments aux événements d'origine.

Les artefacts chargés par le programme au démarrage sont :

- `events.joblib` : événements source ;
- `dico_event` : correspondances événements/segments ;
- `FAISS_Index` : index FAISS sérialisé.

Le dépôt prévoit ainsi une utilisation du RAG sans recalculer les embeddings à chaque lancement.

### Point d'attention sur la reconstruction

Le code actuel expose **`POST /Build`**, et non `/Rebuild`. De plus, `Build()` sauvegarde l'index sous le nom **`FAISS Index`** (avec espace), alors que le démarrage charge **`FAISS_Index`** (avec underscore). Cette incohérence devra être corrigée pour que la reconstruction remplace réellement l'index utilisé au prochain démarrage.

La reconstruction nécessite des appels Mistral pour les segments ; elle peut être longue et consommer des crédits API. Elle n'est pas nécessaire pour les tests simples de `/RAG` avec les artefacts déjà présents.

## Choix technologiques et modèles

| Composant | Technologie utilisée | Rôle |
|---|---|---|
| Langage | Python | Orchestration du pipeline |
| API | FastAPI / Uvicorn | Routes HTTP et documentation Swagger |
| Source de données | OpenAgenda via OpenDataSoft | Événements culturels |
| Embeddings | `mistral-embed-2312` | Représentation vectorielle des segments et des questions |
| Recherche vectorielle | FAISS `IndexFlatL2` | Recherche des voisins les plus proches |
| Génération | `mistral-small-2603` via LangChain | Filtrage, classement, formulation |
| Persistance | Joblib | Sauvegarde et chargement des données et de l'index |
| Déploiement local | Docker | Environnement reproductible |
| Tests | TestClient / assertions Python ; pytest et pytest-cov pour la mesure | Vérifications fonctionnelles et couverture |

Le choix d'une recherche sémantique permet de rapprocher des formulations différentes d'un même besoin. FAISS est adapté à une recherche vectorielle locale ; Mistral Small est utilisé pour transformer les candidats récupérés en recommandations lisibles. Les raisons de coût, de latence ou de supériorité par rapport à d'autres solutions n'ont pas été mesurées comparativement dans ce projet.

## Installation et exécution avec Docker

### Prérequis

- Docker Desktop (ou un moteur Docker compatible) ;
- une clé API Mistral valide ;
- un accès réseau pour les appels au service Mistral.

### 1. Récupérer le dépôt

```bash
git clone https://github.com/tmininihub/Projet-7-OC.git
cd Projet-7-OC
```

Il est aussi possible de télécharger le ZIP depuis GitHub puis de l'extraire.

### 2. Configurer la clé API

Créer un fichier `.env` à la racine :

```dotenv
MISTRAL_API_KEY=VOTRE_CLE_API
```

Ne pas publier cette clé. Le dépôt ignore `.env` via `.gitignore`.

### 3. Construire l'image

```bash
docker build -t project7-rag .
```

Le `Dockerfile` fourni utilise **Python 3.12 slim**, installe les dépendances de `requirements.txt` et démarre Uvicorn.

### 4. Démarrer l'API

```bash
docker run --env-file .env -p 8000:8000 project7-rag
```

Ouvrir ensuite **http://localhost:8000/docs** pour accéder à Swagger.

> **Attention :** le fichier `main.py` contient actuellement un appel direct à `RAG("Je cherche un event sur le spatial")` à la fin du module. Cet appel s'exécute aussi lors de l'import par Uvicorn et déclenche une requête Mistral supplémentaire au démarrage. Il est conseillé de le retirer ou de le placer dans une condition `if __name__ == "__main__":`.

### Exécution locale sans Docker (facultatif)

```bash
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

Utiliser un environnement virtuel Python et renseigner `MISTRAL_API_KEY` au préalable. Les fichiers de données et d'index doivent être présents dans le répertoire de travail attendu.

## API et exemples d'utilisation

### `POST /RAG`

Effectue une recherche à partir du paramètre **`prompt` passé dans la query string** (ce n'est pas un corps JSON).

Depuis Swagger : sélectionner `POST /RAG` → **Try it out** → remplir `prompt` → **Execute**.

Exemple en ligne de commande :

```bash
curl -X POST "http://localhost:8000/RAG?prompt=Je%20cherche%20un%20event%20sur%20le%20spatial"
```

La réponse attendue est un objet JSON contenant zéro ou plusieurs entrées `Event 1`, `Event 2`, etc., avec les champs :

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

La structure dépend de la bonne application du format demandé au LLM. **Si le modèle renvoie un texte non conforme**, les lignes ne sont pas retenues par le parseur ; une réponse vide peut donc refléter une erreur de formatage et pas seulement une absence d'événements.

### `POST /Build`

Télécharge des données OpenDataSoft et produit des embeddings et un index FAISS. Cette opération est coûteuse par rapport à une simple interrogation de `/RAG`, et le problème de nom de fichier décrit plus haut doit être résolu avant de compter sur une reconstruction complète.

## Tests, couverture et évaluation

### Vérifications actuellement présentes

Le fichier `test_main.py` vérifie notamment :

- que les segments examinés ne dépassent pas 500 caractères ;
- que les embeddings renvoyés ont une dimension de 1 024 ;
- qu'une requête `POST /RAG` renvoie un code HTTP 200 ;
- que le texte d'une réponse à une question sur le jazz contient le terme `jazz`.

Ces vérifications existent dans le dépôt, mais **ne constituent pas toutes des tests unitaires isolés** : les embeddings et la route RAG utilisent des services externes, et le test ne remplace pas ces appels par des mocks.

**Limite du fichier actuel :** `def test_RAG(texte)` attend un argument que pytest interprète comme un nom de fixture. Or aucune fixture `texte` n'est définie dans ce fichier. La fonction est également appelée directement en fin de fichier. La découverte standard par `pytest` doit donc être corrigée avant de présenter cette suite comme automatisée et reproductible.

### Couverture communiquée

Une mesure effectuée sur le projet complet a été **rapportée à 67 %**. Après retrait de la fonction `Build` du code mesuré, le résultat fourni est :

```text
Name      Stmts   Miss  Cover
----------------------------
main.py      56      0   100%
----------------------------
TOTAL        56      0   100%
```

La couverture est donc de **100 % pour le périmètre restant après retrait de `Build`**, pas de 100 % pour l'application complète. Le 67 % est un résultat communiqué, non une mesure reproduite lors de la rédaction de ce document. La couverture des lignes ne garantit pas à elle seule la qualité des assertions ni la couverture de tous les comportements.

Une fois les tests adaptés à pytest, les commandes pertinentes sont :

```bash
python -m pytest -v
python -m pytest --cov=main --cov-report=term-missing
```

La seconde commande suppose que `pytest-cov` est installé.

### Jeu de test annoté : état et méthode

Un **jeu de test annoté** associe à chaque question des **événements jugés pertinents à l'avance**, indépendamment des résultats du système. Il permet de vérifier objectivement la qualité de la recherche.

Les exemples de sorties présentés ci-dessous sont des **observations**, mais ils ne suffisent pas à constituer un jeu annoté complet : les références attendues n'ont pas été documentées séparément.

Format conseillé :

| Question | Événements attendus (annotations humaines) | Événements renvoyés | Pertinence / commentaire |
|---|---|---|---|
| Je cherche un événement sur le spatial | À renseigner avant le test | À renseigner après le test | À évaluer |
| Je cherche un événement de jazz | À renseigner avant le test | À renseigner après le test | À évaluer |

À terme, utiliser plusieurs questions variées et évaluer les résultats avec **Precision@k**, **Recall@k** ou **Hit@k**. Aucune valeur chiffrée de ces métriques n'est annoncée ici, faute de références annotées et de calcul vérifiable.

## Résultats observés et limites

### Exemple de réponse : événements spatiaux

Pour la requête « Je cherche un event sur le spatial », une sortie de cinq événements a été communiquée :

| Titre renvoyé | Date indiquée | Lieu |
|---|---|---|
| Objectifs Terre, la révolution des satellites | 2 août – 31 décembre 2022 | Cité des sciences et de l'Industrie |
| Journées Portes Ouvertes à l'Agence Spatiale Européenne | 19 et 20 septembre (année non précisée) | Siège de l'Agence spatiale européenne |
| Les conférences – Explorer l'espace, mieux habiter notre planète | 21 octobre 2023 – 20 janvier 2024 | Cité des sciences et de l'Industrie |
| Visite commentée de l'exposition Mission spatiale | Samedi 31 janvier (année non précisée) | Cité des sciences et de l'Industrie |
| Rendez-vous avec l'espace : Week-end spatial | 14 et 15 février (année non précisée) | Cité des sciences et de l'Industrie |

**Observation qualitative :** les cinq titres et descriptions correspondent au thème spatial. Cela illustre la capacité du pipeline à retrouver des contenus thématiquement proches, **sans démontrer une précision ou un rappel mesurés**.

**Limite importante :** certaines dates sont explicitement passées, et d'autres ne comportent pas d'année. Au **3 novembre 2026**, on ne peut donc pas considérer ces cinq recommandations comme une liste validée d'événements à venir. L'API ne contient pas actuellement de filtrage explicite sur les dates futures dans sa route `/RAG`.

### Autres limites identifiées dans le code

- **Découpage naïf** : les blocs fixes de 500 caractères peuvent couper une phrase ou séparer des informations importantes.
- **Recherche sur seulement cinq segments** : possibilité de récupérer plusieurs segments d'un même événement, limitant la diversité des candidats.
- **Filtrage de pertinence laissé au LLM** : absence de seuil explicite sur la distance FAISS.
- **Formatage fragile** : le code découpe les lignes sur le séparateur exact `" | "` ; une sortie différente peut être ignorée.
- **Dépendances à des services externes** : le comportement dépend de la disponibilité, des quotas et de la réponse des API Mistral.
- **Coût de la construction** : embeddings demandés segment par segment, sans traitement par lots.
- **Chargement des fichiers à l'import** : des artefacts manquants peuvent empêcher l'application de démarrer.
- **Couverture partielle** : le chemin de construction de l'index n'est pas couvert selon les résultats rapportés.
- **Tests à restructurer** : le fichier existant combine un appel direct et une fonction dont le paramètre ne correspond pas à une fixture pytest.

## Pistes d'amélioration

Les améliorations suivantes sont **proposées**, non présentées comme déjà implémentées :

1. **Fiabiliser les données** : filtrer les événements selon leur vraie date de déroulement ; normaliser les dates incomplètes ; contrôler les valeurs manquantes.
2. **Corriger le cycle de reconstruction** : harmoniser le nom du fichier FAISS, tester `/Build`, gérer les erreurs réseau et prévoir des sauvegardes atomiques.
3. **Optimiser l'indexation** : regrouper les embeddings par lots et utiliser un découpage respectant mieux les phrases, éventuellement avec chevauchement.
4. **Améliorer la récupération** : comparer plusieurs valeurs de `k`, diversifier les événements, tester des seuils de pertinence et des filtres sur les dates/lieux.
5. **Sécuriser la génération** : imposer une réponse structurée JSON validée par un schéma plutôt que de parser librement des lignes au séparateur `|`.
6. **Rendre les tests fiables** : utiliser pytest avec fixtures et mocks, séparer tests unitaires et tests d'intégration, couvrir les cas d'erreur et la route `/Build`.
7. **Quantifier la pertinence** : constituer un jeu annoté indépendant et publier les scores de récupération et de qualité finale.
8. **Nettoyer le démarrage** : retirer l'appel `RAG(prompt)` exécuté à l'import et fournir une route de contrôle de santé si nécessaire.

## Structure du dépôt

Principaux fichiers vérifiés dans le dépôt GitHub :

```text
Projet-7-OC/
├── README.md
├── main.py               # Construction de l'index et route RAG
├── test_main.py          # Vérifications actuellement présentes
├── Dockerfile            # Image Python 3.12, Uvicorn
├── requirements.txt      # Dépendances Python
├── .gitignore            # Exclut .env
├── events.joblib         # Événements sérialisés
├── dico_event            # Mapping segment -> événement (via dictionnaire)
└── FAISS_Index           # Index vectoriel chargé par main.py
```

Le code utilise également le nom `FAISS Index` pour une **sortie de reconstruction** : il ne faut pas le confondre avec le fichier `FAISS_Index` chargé par l'API.

---

**Cadre pédagogique :** projet réalisé dans le cadre du Projet 7 OpenClassrooms. Ce README documente l'implémentation consultée, les résultats de couverture communiqués et les observations fournies, sans attribuer de métriques non calculées au système.
