"""Controller layer for authentication and registration use cases."""

from repositories.user_repository import UserRepository


class UserController:
    def __init__(self, repository=None):
        self.repository = repository or UserRepository()

    def authenticate(self, username: str, password: str) -> dict:
        return self.repository.authenticate(username, password)

    def register(self, full_name: str, username: str, password: str) -> int:
        return self.repository.register(full_name, username, password)

    def list_users(self) -> list[dict]:
        return self.repository.list_users()
