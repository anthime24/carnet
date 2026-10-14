class CarnetError(Exception):
    """Erreur attendue, rapportée à l'appelant sous forme de JSON."""

    def __init__(self, error, detail=""):
        super().__init__(f"{error}: {detail}" if detail else error)
        self.error = error
        self.detail = detail
