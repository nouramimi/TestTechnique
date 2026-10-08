class ConnectorError(Exception):
    """Erreur générique d'un connecteur."""


class AuthError(ConnectorError):
    """Token invalide ou expiré : toute la collecte doit s'arrêter."""


class PermissionDeniedError(ConnectorError):
    """Permission manquante pour une ressource précise : la collecte peut continuer."""


class RateLimitError(ConnectorError):
    """Quota de l'API dépassé."""
