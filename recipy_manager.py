import difflib
from typing import List
from bs4 import BeautifulSoup
import requests


def _hex(name: str):
    return name.encode('cp1251').hex()


def _get_url(ingredients: List[str]) -> str:
    fin_url = ""
    for ind in range(len(ingredients)):
        encoded = _hex(ingredients[ind])
        for i in range(0, len(encoded), 2):
            fin_url += "%" + encoded[i: i + 2].upper()
        if ind != len(ingredients) - 1:
            fin_url += "%2C+"

    return fin_url


class RecipyManager:
    def __init__(self, ingredients_path="ingredients.txt", logging=False):
        self._url = ("https://www.povarenok.ru/recipes/search/~INDEX/?ing=ING_LIST"
                     "&ing_exc=&kitchen=&type=&cat=&subcat=&orderby=")
        self._logging = logging
        self._data = []

        with open(ingredients_path, 'r', encoding='utf-8') as file:
            self._data = file.read().split(";")

        if self._logging:
            print(f"Initialized Recipy Manager with path to ingredients = {ingredients_path}."
                  f"Loaded {len(self._data)} recipies")

    def find_nearest(self, name: str) -> List[str]:
        return difflib.get_close_matches(name, self._data)

    def parse_web(self, ingredients: List[str], page=2):
        if self._logging:
            print("Started parsing...")

        fin_url = self._url.replace("INDEX", str(page)).replace("ING_LIST", _get_url(ingredients))
        soup = BeautifulSoup(requests.get(fin_url).content, 'html5lib')
        articles = soup.find_all('article', class_='item-bl')

        # Создаем список для хранения данных
        recipes_list = []

        # Проходимся по всем найденным элементам <article>
        for article in articles:
            recipe = dict()

            # Получаем информацию о рецепте
            recipe['name'] = article.find('h2').text.strip()
            recipe['link'] = article.find('a')['href']
            recipe['ingredients'] = [ingredient.text.strip() for ingredient in
                                     article.find_all('div', class_='ingr_fast')[0].find_all('span')]
            recipe['desc'] = article.find_all('p')[1].text.strip()  # Выбираем второй элемент <p>
            recipe['img_link'] = article.find('img')['src']

            # Добавляем информацию о рецепте в список
            recipes_list.append(recipe)

        return recipes_list
