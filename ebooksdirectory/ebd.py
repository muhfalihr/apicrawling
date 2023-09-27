import re
from json import dumps
from time import time

from bs4 import BeautifulSoup
import requests
from flask import Response


class Utility:
    filters = ["categories", "new", "top", "popular"]

    def resp404(datas: dict):
        if datas['data'] != []:
            return datas, datas['status']
        else:
            datas.update({'status': 404})
            return datas, datas['status']

    def clean(text):
        cleaned = re.sub(r'\n+', '\n', text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned)
        return cleaned_text.strip()


class AllCategories:
    def __init__(self, option=None, allcategories=False, id=None, countpage=1):
        self.allcategories = allcategories
        self.option = option if option != 'top' else 'top20'
        self.id = id
        self.countpage = int(countpage)
        self.headlink = 'http://www.e-booksdirectory.com/'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'}

        match self.option:
            case 'categories':
                self.link = f'http://www.e-booksdirectory.com/listing.php?category={self.id}'

            case 'new' | 'top20' | 'popular':
                self.link = f'http://www.e-booksdirectory.com/{self.option}.php'

            case _:
                self.link = 'http://www.e-booksdirectory.com'

    def BSoup(self, link):
        resp = requests.get(link, headers=self.headers)
        soup = BeautifulSoup(resp.text, 'lxml')
        return soup.find_all('section', 'main_content'), resp

    def allCategories(self, item):
        links = [self.headlink+a['href']
                 for article in item[0].find_all('article', 'main_categories') for a in article.find_all('a', class_=False)]
        names = [a.text for article in item[0].find_all('article', 'main_categories') for a in article.find_all(
            'a', class_=False)]
        ids = [re.search(r'category=(\d+)', a['href']).group(1)
               for article in item[0].find_all('article', 'main_categories') for a in article.find_all('a', class_=False)]

        return links, names, ids

    def articleLinks(self, item):
        return [self.headlink+a['href'] for article in item[0].find_all('article', 'img_list') for a in article.find_all('a', class_=False)]

    def articleData(self, item):
        article = [artikel for artikel in item[0].find_all(
            'article', {'itemtype': 'http://schema.org/Book'})]

        image = ''.join([self.headlink+img['src']
                        for img in article[0].find_all('img', {'itemprop': 'image'})])
        title = ''.join([strong.text for strong in article[0].find_all(
            'strong', {'itemprop': 'name'})])
        author = ''.join(
            [span.text for span in article[0].find_all('span', {'itemprop': 'author'})])
        publisher = ''.join(
            [span.text for span in article[0].find_all('span', {'itemprop': 'publisher'})])
        datePublished = ''.join(
            [span.text for span in article[0].find_all('span', {'itemprop': 'datePublished'})])
        nop = ''.join(
            [span.text for span in article[0].find_all('span', {'itemprop': 'numberOfPages'})])
        desc = ''.join(
            [span.text for span in article[0].find_all('span', {'itemprop': 'description'})])
        isbn = ''.join(
            [span.text for span in article[0].find_all('span', {'itemprop': 'isbn'})])
        download = ''.join([a['href'] for a in article[0].find_all(
            'a', {'target': '_blank'}) if a.text == 'Download link'])

        return image, title, author, publisher, datePublished, nop, desc, isbn, download

    def nextPage(self, item):
        for input in item[0].find_all('input', 'submit_button'):
            if input['value'] == 'Next':
                return self.countpage + 1
            elif input['value'] == 'Prev':
                return ''

    def NTPLinks(self, item):
        if self.countpage < 1:
            return ['']
        elif self.countpage == 1:
            links = self.articleLinks(item)
            return links
        else:
            num = 0
            for i in range(self.countpage-1):
                data = {
                    "submit": "Next",
                    "startid": f"{0+num}"
                }

                resp = requests.post(self.link, data=data)
                soup = BeautifulSoup(resp.text, 'lxml')
                items = soup.find_all('section', 'main_content')
                num += 20

            links = self.articleLinks(items)
            return links

    def crawl(self, link=None, name=None, id=None):
        match self.allcategories:
            case True:
                data = {
                    "id": id,
                    "link": link,
                    "name": name
                }
            case False:
                item, resp = self.BSoup(link)
                image, title, author, publisher, datePublished, nop, desc, isbn, download = self.articleData(
                    item)
                data = {
                    "title": Utility.clean(title),
                    "thumbnail_url": image,
                    "author": Utility.clean(author),
                    "publisher": Utility.clean(publisher),
                    "date_published": datePublished,
                    "number_of_page": nop,
                    "isbn/asin": isbn,
                    "description": Utility.clean(desc),
                    "original_site": download
                }
        return data

    def displayResult(self):
        datas = []
        try:
            match self.allcategories:
                case True:
                    item, resp = self.BSoup(self.link)
                    data = {
                        "status": resp.status_code,
                        "data": datas
                    }
                    links, names, ids = self.allCategories(item)
                    for link, name, id in zip(links, names, ids):
                        datas.append(self.crawl(link=link, name=name, id=id))

                    results = dumps(data, indent=4)

                case False:
                    item, resp = self.BSoup(self.link)

                    if self.option == 'categories' or '':
                        data = {
                            "status": resp.status_code,
                            "data": datas
                        }
                        for link in self.articleLinks(item):
                            datas.append(self.crawl(link=link))

                        results = dumps(data, indent=4)

                    else:
                        data = {
                            "status": resp.status_code,
                            "data": datas,
                            "next_page": self.nextPage(item)
                        }
                        for link in self.NTPLinks(item):
                            datas.append(self.crawl(link=link))

                        results = dumps(data, indent=4)

            return Response(
                response=results,
                headers={"Content-Type": "application/json; charset=UTF-8"},
                status=resp.status_code
            )
        except Exception as error:
            response = {
                "name": "HTTPError",
                "message": "Internal Server Error",
                "status": 500,
                "detail": str(error)
            }
            return Response(
                response=dumps(response, indent=4),
                headers={"Content-Type": "application/json; charset=UTF-8"},
                status=500
            )
