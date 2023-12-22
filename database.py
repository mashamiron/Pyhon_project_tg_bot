import pickle
import os
from typing import List

from stages import Stages

DEFAULT_STAGE = Stages.STARTED.value


class DataBase:
    def __init__(self, cache_path='./cache.pickle', logging=False, autosave_iter=10):
        """
        Initializes database.
        Database structure:
        {
            <user_id>: {
                <name>: str,
                <stage>: int,
                <ingredients>: list,
                <recipies>: list        # already parsed recipies for web-saving purposes
                <msg_id>: int           # for UI purposes
            }
        }
        :param cache_path:
        :param logging:
        :param autosave_iter:
        """
        self._cache_path = cache_path
        self._logging = logging
        self._data = {}
        self._autosave_iter = autosave_iter
        self._iter = 0

        if self._logging:
            print(f"Database initialized with cache_path = {cache_path}, autosave_iter = {autosave_iter}.")

        if self._logging:
            print(f"Fetching {cache_path}...")

        if os.path.exists(cache_path):
            with open(cache_path, 'rb') as file:
                self._data = pickle.load(file)

            if self._logging:
                print(f"Cache loaded from {cache_path}, {len(self._data)} rows.")

    def create_user(self, user_id: int, name="None") -> bool:
        if user_id not in self._data:
            self._data[user_id] = {
                "stage": DEFAULT_STAGE,
                "name": name,
                "ingredients": [],
                "recipies": [],
                "msg_id": -1
            }
            if self._logging:
                print(f"Created new user {user_id} with default stage")

            return True

        return False

    def dump_data(self):
        with open(self._cache_path, 'wb') as file:
            pickle.dump(self._data, file)
        if self._logging:
            print(f"Dumped data to {self._cache_path}.")

    def _update_iter(self):
        self._iter += 1
        if self._iter == self._autosave_iter:
            self.dump_data()
            self._iter = 0

    def set_stage(self, user_id: int, stage: int) -> None:
        if user_id in self._data:
            self._data[user_id]["stage"] = stage

            if self._logging:
                print(f"Updated stage for user {user_id}. Set to {stage}")
        else:
            self.create_user(user_id)
            self.set_stage(user_id, stage)

        self._update_iter()

    def get_stage(self, user_id: int) -> int:
        if user_id not in self._data:
            if self._logging:
                print(f"User with {user_id} not found.")

            return Stages.NOT_FOUND.value

        return self._data[user_id]["stage"]

    def get_user(self, user_id: int) -> dict:
        if user_id not in self._data:
            if self._logging:
                print(f"User with {user_id} not found.")

            return {}

        return self._data[user_id]

    def add_ingredient(self, user_id: int, ingredient: str) -> bool:
        if user_id not in self._data:
            if self._logging:
                print(f"User with {user_id} not found.")

            return False

        self._data[user_id]["ingredients"].append(ingredient)

        if self._logging:
            print(f"Added ingredient {ingredient} to {user_id}")

        self._update_iter()
        return True

    def set_msg_id(self, user_id: int, msg_id: int) -> bool:
        if user_id not in self._data:
            if self._logging:
                print(f"User with {user_id} not found.")

            return False

        self._data[user_id]["msg_id"] = msg_id

        if self._logging:
            print(f"Set msg_id = {msg_id} to {user_id}")

        self._update_iter()
        return True

    def get_msg_id(self, user_id: int) -> int:
        if user_id not in self._data:
            if self._logging:
                print(f"User with {user_id} not found.")

            return -1

        return self._data[user_id]["msg_id"]

    def pop_ingredient(self, user_id: int, index: int) -> int:
        if user_id not in self._data:
            if self._logging:
                print(f"User with {user_id} not found.")

            return -1

        self._data[user_id]["ingredients"].pop(index)

        if self._logging:
            print(f"Popped ingredient {index} from {user_id}'s list")

        self._update_iter()
        return len(self._data[user_id]["ingredients"])

    def get_recipies(self, user_id: int) -> List[dict]:
        if user_id not in self._data:
            if self._logging:
                print(f"User with {user_id} not found.")

            return []

        return self._data[user_id]["recipies"]

    def set_recipies(self, user_id: int, recipies: List[dict]) -> bool:
        if user_id not in self._data:
            if self._logging:
                print(f"User with {user_id} not found.")

            return False

        self._data[user_id]["recipies"] = recipies

        if self._logging:
            print(f"Set recipies to {user_id}")

        self._update_iter()
        return True
