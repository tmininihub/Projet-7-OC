# Évaluation du RAG — 20 requêtes

## Périmètre

Les 20 requêtes et les 53 événements évalués proviennent des réponses de l'API transmises par l'utilisateur le 5 novembre 2026. L'évaluation porte uniquement sur les textes retournés (titre, description, date, lieu) ; aucune recherche indépendante dans le corpus OpenAgenda complet n'a été effectuée.

Les critères attendus pour chaque question sont documentés dans `evaluation_RAG_20_questions_detail.csv`.

## Annotation de pertinence

- `2` : correspond à la demande d'après le texte de la réponse ; toutes les contraintes essentielles observables sont respectées.
- `1` : correspond partiellement ou manque de preuves sur une contrainte essentielle.
- `0` : ne répond pas à la demande.

Les annotations sont **proposées par l'assistant et à valider humainement**, et ne constituent pas un « ground truth » certifié. La même question peut admettre de nombreux autres événements pertinents, même absents des réponses reçues.

## Métriques calculées

- **Précision stricte par question** = nombre de résultats notés `2` / nombre de résultats retournés pour cette question.
- **Précision large par question** = nombre de résultats notés `1` ou `2` / nombre de résultats retournés.
- **Hit strict** = 1 si au moins un résultat noté `2` est présent, sinon 0.
- **MRR strict** = 1 / rang du premier résultat noté `2` (0 si aucun).
- **nDCG gradué** = DCG des notes `0`, `1`, `2` dans l'ordre retourné, divisé par DCG de ces mêmes notes triées par pertinence décroissante ; ce chiffre juge le classement **parmi les seuls résultats retournés**, pas la capacité à récupérer les événements absents.

La moyenne macro calcule la moyenne des précisions des **20 requêtes** en donnant le même poids à chaque requête. La précision micro rapporte les résultats notés `2` aux **53 événements**.

**Ne pas appeler ces scores `Precision@5`** : l'API a retourné entre 1 et 4 événements par question. La précision est mesurée sur les résultats effectivement retournés, pas sur un k constant.

**Ne pas annoncer de Recall@k** : aucun inventaire exhaustif des événements pertinents présents dans le corpus n'a été établi.

## Vérification temporelle

Les dates ont été analysées séparément sur la base du 5 novembre 2026 :
- `passe_explicitement` signifie que la date fournie porte une année passée, ou une fin de période passée, explicite.
- `annee_non_precisee` signifie que l'année n'apparaît pas clairement dans le champ de date et qu'il ne faut pas la déduire arbitrairement.
- `periode_inclut_date_evaluation` signifie que la plage datée contient explicitement le 5 novembre 2026.

Une date passée ne rend pas automatiquement un résultat thématiquement non pertinent car les questions ne spécifiaient pas de date future. En revanche, dans une recommandation d'événements réellement accessibles aujourd'hui, la fraîcheur est un critère essentiel à mesurer et à améliorer.

Les chaînes de titres très proches ont un `groupe_doublon_potentiel` commun. Il ne s'agit pas d'une preuve d'identité : des séances distinctes ou des événements récurrents peuvent légitimement partager un titre.

## Résultats synthétiques (annotations provisoires)

- 20 questions, 53 résultats.
- 43 pleinement pertinents (note 2), 6 partiellement pertinents (note 1), 4 non pertinents (note 0).
- Précision stricte macro : 75,00 % (moyenne des taux par question).
- Précision stricte micro : 81,13 % (43 / 53).
- Hit strict : 85 % (17 / 20 questions).
- 20 résultats portent une date explicitement passée selon la règle ci-dessus.

## Limites et prochaines étapes

Pour construire un jeu de référence réellement indépendant, figer une copie datée du corpus, constituer des requêtes et critères de pertinence *avant* d'interroger le RAG, faire annoter par un humain ou arbitrer les désaccords, puis réexécuter l'évaluation. Pour un Recall@k, relever également les événements pertinents que FAISS ou le modèle n'ont pas retournés. Séparer à l'avenir les performances de la recherche FAISS, de la sélection par le LLM et de la fraîcheur des événements.