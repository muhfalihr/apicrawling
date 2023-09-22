from json import dumps, load
import re
import unicodedata


from bs4 import BeautifulSoup
import requests
from flask import Response


class Utility:
    filters = ["categories", "new", "top", "popular"]
    cat = ["Arts & Photography", "Biographies & Memoirs", "Business & Investing", "Children's Books", "Comics & Graphic Novels", "Computers & Internet", "Cooking, Food & Wine", "Engineering", "Entertainment",
           "Health, Mind & Body", "History", "Humanities", "Law", "Literature & Fiction", "Mathematics", "Medicine", "Nonfiction", "Outdoors & Nature", "Religion & Spirituality", "Science", "Science Fiction & Fantasy", "Travel"]

    with open('ebooksdirectory/listLinks.json', 'r') as file:
        links = load(file)

    def __init__(self):
        pass

    def soup(link):
        user_agent = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'}

        req = requests.get(link, headers=user_agent)

        soup = BeautifulSoup(req.text, 'lxml')

        if 'listing.php' in link:
            return soup.find_all('section', 'main_content')
        else:
            return soup.find_all('article', 'main_categories')

    def returnError(message):
        '''Bila swagger mengambalikan server response 500 atau 400 maka akan memunculkan response body sesuai dengan ini.'''
        datas = {
            'status': 500,
            'data': [],
            'next_page': ''
        }
        datas_dumps = dumps(datas, indent=4)
        return datas_dumps, datas['status']

    def resp400(datas: dict):
        if datas['data'] != []:
            return datas, datas['status']
        else:
            datas.update({'status': 400})
            return datas, datas['status']

    def clean(text):
        cleaned = re.sub(r'\n+', '\n', text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned)
        normalized = unicodedata.normalize('NFKD', cleaned_text)
        ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
        replace_text = ascii_text.replace('\"', "'").replace('\r\n', ' - ')
        return replace_text.strip()


class Categories:
    def __init__(self, items):
        self.items = items
        self.headlink = 'http://www.e-booksdirectory.com/'

    def cat_smallText(self, cat_large):
        result = [[] for _ in range(len(cat_large))]

        for i in range(len(cat_large)):
            for item in self.items:
                for table in item.find_all('table'):
                    cs = [cs.text for cs in table.find_all('td', 'cat_small')[
                        i] if cs.text.strip() != '']
                    result[i].extend(cs)
        hasil = [[''] if not sublist else sublist for sublist in result]
        return hasil

    def cat_smallLink(self):
        result = [[self.headlink+a['href'] for a in cs.find_all('a')] for item in self.items for table in item.find_all(
            'table') for cs in table.find_all('td', 'cat_small')]
        hasil = [[''] if not sublist else sublist for sublist in result]
        return hasil

    def cat_largeText(self):
        return [cl.text for item in self.items for table in item.find_all(
            'table') for cl in table.find_all('td', 'cat_large')]

    def cat_largeLink(self):
        return [self.headlink+a['href'] for item in self.items for table in item.find_all(
            'table') for cl in table.find_all('td', 'cat_large') for a in cl.find_all('a')]


class GrabTheLink:
    def __init__(self):
        pass

    def takeHref(links):
        try:
            linkhref = ['http://www.e-booksdirectory.com/' + a['href'] for item in Utility.soup(
                links) for article in item.find_all('article', 'img_list') for a in article.find_all('a')]
        except:
            linkhref = ['http://www.e-booksdirectory.com/' + a['href']
                        for link in links
                        if link != ''
                        for item in Utility.soup(link) for article in item.find_all('article', 'img_list') for a in article.find_all('a')]
        return linkhref

    def takeLinkCategories(self):
        link = 'http://www.e-booksdirectory.com/'
        items = Utility.soup(link)

        kategori = Categories(items)

        clText = kategori.cat_largeText()
        clLink = kategori.cat_largeLink()
        csLink = kategori.cat_smallLink()

        all_categories = []
        for i in range(len(clText)):
            data = self.takeHref(clLink[i]) + self.takeHref(csLink[i])
            all_categories.append(data)

            datas_dumps = dumps(all_categories, indent=4)

            try:
                with open('links.json', 'w') as file:
                    file.write(datas_dumps)
            except:
                with open('links.json', 'r+') as file:
                    file.write(datas_dumps)

    def takeNTP(page: int, option: str):
        '''page = Berapa page yang akan anda ambil linknya, option = (new, top, popular) pilihan page yang akan anda ambil linknya. (Defaultnya New)'''
        user_agent = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'}

        match option.lower():
            case 'new':
                url = 'http://www.e-booksdirectory.com/new.php'
            case 'top':
                url = 'http://www.e-booksdirectory.com/top20.php'
            case 'popular':
                url = 'http://www.e-booksdirectory.com/popular.php'

        resp = requests.get(url, headers=user_agent)

        soup = BeautifulSoup(resp.text, 'lxml')

        items = soup.find_all('article', 'img_list')

        hrefLinks = []
        [hrefLinks.append('http://www.e-booksdirectory.com/'+a['href'])
         for item in items for a in item.find_all('a')]

        if page < 1:
            return ['']

        num = 0
        for i in range(page-1):
            data = {
                'submit': 'Next',
                'startid': f'{0+num}'
            }

            response = requests.post(url, data=data)

            soup = BeautifulSoup(response.text, 'html.parser')

            items = soup.find_all('article', 'img_list')

            [hrefLinks.append('http://www.e-booksdirectory.com/'+a['href'])
             for item in items for a in item.find_all('a')]
            num += 20

        return hrefLinks


class CrawlDetail:
    def __init__(self, link):
        self.__user_agent = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'}

        self.__link = link

        self.__resp = requests.get(self.__link, headers=self.__user_agent)

        self.__soup = BeautifulSoup(self.__resp.text, 'lxml')

        self.__items = self.__soup.find_all('section', 'main_content')

    def articles(self):
        return [article for item in self.__items for article in item.find_all('article')]

    def img(self):
        article = self.articles()
        return ''.join(['http://www.e-booksdirectory.com/'+img['src']
                        for img in article[1].find_all('img')])

    def title(self):
        article = self.articles()
        return ''.join([Utility.clean(strong.text) for strong in article[1].find_all(
            'strong', itemprop='name')])

    def author(self):
        article = self.articles()
        return ''.join([Utility.clean(span.text) for p in article[1].find_all('p') for span in p.find_all(
            'span', itemprop='author')])

    def publisher(self):
        article = self.articles()
        return ''.join([Utility.clean(span.text) for p in article[1].find_all('p') for span in p.find_all('span', itemprop='publisher')])

    def datePublished(self):
        article = self.articles()
        return ''.join([span.text for span in article[1].find_all('span', itemprop='datePublished')])

    def numPage(self):
        article = self.articles()
        np = [int(span.text) for p in article[1].find_all('p')
              for span in p.find_all('span', itemprop='numberOfPages')]
        return np[0] if len(np) == 1 and isinstance(np[0], int) else None

    def isbn(self):
        article = self.articles()

        return ''.join([span.text for p in article[1].find_all('p') for span in p.find_all('span', itemprop='isbn')])

    def desc(self):
        article = self.articles()

        return ''.join([Utility.clean(span.text) for p in article[1].find_all('p') for span in p.find_all('span', itemprop='description')])

    def download_link(self):
        article = self.articles()
        url = ''.join([href['href'] for href in article[1].find_all(
            'a') if href.text == 'Download link'])
        return url


class Save:
    def __init__(self, urls):
        self.urls = urls

    def returnSuccess(self):

        results = []
        datas = {
            'status': 200,
            'data': results
        }

        for link in self.urls:
            crawl = CrawlDetail(link)
            data = {
                'title': crawl.title(),
                'thumbnail_url': crawl.img(),
                'author': crawl.author(),
                'publisher': crawl.publisher(),
                'date_published': crawl.datePublished(),
                'number_of_page': crawl.numPage(),
                'isbn/asin': crawl.isbn(),
                'description': crawl.desc(),
                'original_site': crawl.download_link()
            }
            results.append(data)

            fix_data, code = Utility.resp400(datas)
            datas_dumps = dumps(fix_data, indent=4)

        return datas_dumps, code


class MatchingEBD:
    def __init__(self, filter, category=None, nop=1):
        self.filter = filter
        self.category = category
        self.nop = nop

    def match(self):
        match self.filter:
            case 'categories':
                cat = Utility.cat.index(self.category)
                save = Save(Utility.links[cat])
                results, code = save.returnSuccess()
            case 'new' | 'top' | 'popular':
                urls = GrabTheLink.takeNTP(int(self.nop), self.filter)
                save = Save(urls)
                results, code = save.returnSuccess()

        return Response(
            response=results,
            headers={"Content-Type": "application/json; charset=UTF-8"},
            status=code
        )
