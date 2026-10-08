# social_collector

Collecte de posts (texte, image, commentaires) autour d'un sujet, stockés dans MongoDB.

## Architecture
- `connectors/base.py` : interface `SocialConnector` (la source est interchangeable).
- `connectors/instagram.py` : hashtag → posts récents → commentaires (API Graph).
- `connectors/mock.py` : jeu de données local pour développer sans accès Meta.
- `storage.py` : upsert idempotent dans `posts`, images dans GridFS.
- `pipeline.py` : orchestre collecte, téléchargement d'images, statistiques.

## Lancer
    pip install -r requirements.txt
    cp .env.example .env            # puis renseigner IG_USER_ID et IG_ACCESS_TOKEN
    python -m social_collector --source mock --topic "décès de Jacques Chirac"
    python -m social_collector --source instagram --topic "Jacques Chirac" --hashtag jacqueschirac
    pytest

## Prérequis Meta (source instagram)
Compte Instagram professionnel lié à une Page Facebook, app Meta approuvée en App Review
(permission instagram_basic + feature Instagram Public Content Access). Limite : 30 hashtags
distincts par 7 jours. Les noms de version de l'API et les règles évoluent : vérifier la documentation.

## Commentaires : dégradation propre
La récupération des commentaires est tentée pour chaque média collecté. Si le contexte
d'authentification n'autorise pas l'accès aux commentaires d'un média précis, le média est
quand même enregistré avec une liste de commentaires vide et l'erreur est journalisée.
Seul un token invalide ou expiré interrompt la collecte. Les permissions réellement requises
et le comportement pour les médias issus de hashtags sont à valider avec un token réel.
