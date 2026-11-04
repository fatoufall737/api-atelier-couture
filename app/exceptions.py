from fastapi import HTTPException


class NonTrouve(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=404, detail=detail)


class Conflit(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=409, detail=detail)


class DonneesInvalides(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=422, detail=detail)


class NonAuthentifie(HTTPException):
    def __init__(self, detail: str = "Authentification requise"):
        super().__init__(
            status_code=401, detail=detail, headers={"WWW-Authenticate": "Bearer"}
        )


class AccesInterdit(HTTPException):
    def __init__(self, detail: str = "Droits insuffisants pour cette action"):
        super().__init__(status_code=403, detail=detail)