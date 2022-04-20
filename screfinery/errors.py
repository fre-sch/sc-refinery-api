from fastapi import HTTPException, status


class IntegrityError(Exception):
    """
    Used when validation might have succeeded but the internal state of
    the application is not consistent.
    """
    pass


class NotFoundError(HTTPException):
    def __init__(self, resource_name, resource_id):
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            detail=f"{resource_name} for id `{resource_id}` not found"
        )