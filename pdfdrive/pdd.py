from json import dumps
import re
import unicodedata
from flask import Response

from bs4 import BeautifulSoup
import requests


class Utility:
    pagecount = {
        '': 'Any pages',
        '1-24': '1-24',
        '25-50': '25-50',
        '51-100': '51-100',
        '100-*': '100+'
    }

    pubyear = ['', '2015', '2010', '2005', '2000', '1990']

    exactmatch = [False, True]

    def clean(text):
        '''Mengganti string uniq dengan dengan string sesuai format ascii, serta menghilangkan "\n" serta mengganati kutip dua menjadi kutip satu. Serta menghilangkan karakter tidak penting diakhir kalimat atau kata'''
        cleaned = re.sub(r'\n+', '\n', text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned)
        # normalized = unicodedata.normalize('NFKD', cleaned_text)
        # ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
        # replace_text = ascii_text.replace('\"', "'").replace('\r\n', ' - ')
        return cleaned_text.strip().rstrip(":,./;'\=-")

    def unique(inList):
        '''Membuat value di sebuah list menjadi uniq'''
        unique_list = []
        [unique_list.append(x) for x in inList if x not in unique_list]
        return unique_list

    def resp404(datas: dict):
        if datas['data'] != []:
            return datas, datas['status']
        else:
            datas.update({'status': 404})
            return datas, datas['status']


class Search:
    def __init__(self, keyword='', pagecount='', pubyear='', category=None, exactmatch=False, page=1, categories_list=False, subcat=False):
        '''pagecount(Opsional) = Opsi ("1-24", "25-50", "51-100", "100+")\npubyear(Opsional) = Opsi ("2015", "2010", "2005", "2000", "1990")\ncategory(Opsional) = diambil dari API get-category\nexactmatch(Opsional) = pencarian yang benar-benar cocok\npage(Opsional) = halaman ke berapa yang ingin diambil'''
        self.keyword = keyword.replace(' ', '+')
        self.pagecount = pagecount
        self.pubyear = pubyear
        self.category = category
        self.exactmatch = exactmatch
        self.page = page
        self.categories_list = categories_list
        self.subcat = subcat
        self.ua = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'}
        self.linkcat = 'https://www.pdfdrive.com/'
        if self.exactmatch == True:
            self.link = f'https://www.pdfdrive.com/search?q={self.keyword}&pagecount={self.pagecount}&pubyear={self.pubyear}&searchin=&em=1&page={self.page}'
        elif self.category == None:
            self.link = f'https://www.pdfdrive.com/search?q="{self.keyword}"&pagecount={self.pagecount}&pubyear={self.pubyear}&searchin=&em=0&page={self.page}'
        elif self.category != None:
            self.link = f'https://www.pdfdrive.com/category/{self.category}/p{self.page}/'

    def BSoup(self, link, tag=None, clss=None):
        resp = requests.get(link, headers=self.ua)
        soup = BeautifulSoup(resp.text, 'lxml')
        match clss:
            case None:
                for item in soup.find_all('div', 'dialog-left'):
                    return item
            case 'ebook-main':
                for item in soup.find_all(tag, clss):
                    return item
            case 'pagination':
                for item in soup.find_all(tag, clss):
                    return item
            case 'categories-list':
                for item in soup.find_all(tag, clss):
                    return item
            case 'box':
                for item in soup.find_all(tag, {'id': 'categories subcategories'}):
                    return item

    def getLink(self, item):
        match self.category:
            case None:
                return ['https://www.pdfdrive.com'+a['href'] for div in item.find_all('div', 'file-right') for a in div.find_all('a', 'ai-search')]
            case _:
                return ['https://www.pdfdrive.com'+a['href'] for div in item.find_all('div', 'file-right') for a in div.find_all('a', class_=False)]

    def takeTitle(self, item):
        return ''.join([Utility.clean(title.text) for div in item.find_all('div', 'ebook-right-inner') for title in div.find_all('h1', 'ebook-title')])

    def takeThumb(self, item):
        return ''.join([img['src'] for img in item.find_all('img', 'ebook-img')])

    def takeAuthor(self, item):
        return ''.join([Utility.clean(author.text) for author in item.find_all('span', {'itemprop': 'creator'})])

    def infoGreen(self, item):
        return [ig.text for ig in item.find_all('span', 'info-green')]

    def matching(self, values: list, field: str):
        match field:
            case 'Pages':
                return ''.join([item for item in values if field in item])
            case 'year':
                return ''.join([item for item in values if item.isdigit()])
            case 'fullsize':
                return ''.join([item if 'MB' in item else item if 'KB' in item else '' for item in values])

    def takeTags(self, item):
        values = [Utility.clean(a.text) for tags in item.find_all(
            'div', 'ebook-tags') for a in tags.find_all('a')]
        return values if values != [] else ''

    def download(self, item):
        return ''.join(['https://www.pdfdrive.com'+a['href'] for span in item.find_all('span', {'id': 'download-button'}) for a in span.find_all('a', {'id': 'download-button-link'})])

    def nextPage(self, items):
        mp = [li.text for item in items.find_all(
            'div', 'pagination') for li in item.find_all('li', class_=False)][-2]
        return int(self.page)+1 if int(self.page) < int(mp) else '' if int(mp) == int(self.page) else ''

    def categories(self):
        item1 = self.BSoup(self.linkcat, 'div', 'categories-list')
        links = ['https://www.pdfdrive.com'+a['href']
                 for a in item1.find_all('a', class_=False)]
        name = [Utility.clean(a.text)
                for a in item1.find_all('a', class_=False)]
        id = [re.search(r'/category/(\d+)', link).group(1) for link in links]
        return links, name, id

    def subcategories(self):
        item2 = self.BSoup(self.link, 'div', 'box')

        links = ['https://www.pdfdrive.com'+a['href']
                 for a in item2.find_all('a', class_=False)]
        name = [Utility.clean(a.text)
                for a in item2.find_all('a', class_=False)]
        id = [re.search(r'/category/(\d+)', link).group(1)
              for link in links]
        return links, name, id

    def crawl(self, link=None, cat=None, id=None):
        match cat:
            case None:
                item = self.BSoup(link, 'div', 'ebook-main')
                values = self.infoGreen(item)
                data = {
                    'title': self.takeTitle(item),
                    'thumbnail_link': self.takeThumb(item),
                    'author': self.takeAuthor(item),
                    'count_page': self.matching(values, 'Pages'),
                    'pub_year': self.matching(values, 'year'),
                    'file_size': self.matching(values, 'fullsize'),
                    'language': values[-1],
                    'download_link': self.download(item)
                }
            case _:
                data = {
                    'link': link,
                    'category': cat,
                    'category_id': id
                }
        return data

    def displayResult(self):
        datas = []
        try:
            match self.categories_list:
                case False:
                    item = self.BSoup(self.link)
                    data = {
                        'status': 200,
                        'data': datas,
                        'next_page': self.nextPage(item)
                    }
                    for link in self.getLink(item):
                        datas.append(self.crawl(link))

                        fix_data, code = Utility.resp404(data)
                        results = dumps(fix_data, indent=4)

                case True:
                    data = {
                        'status': 200,
                        'data': datas
                    }
                    match self.subcat:
                        case False:
                            links, category, id_cat = self.categories()
                            for link, cat, id in zip(links, category, id_cat):
                                datas.append(self.crawl(link, cat, id))
                        case True:
                            subcat_links, subcat, subcat_id = self.subcategories()
                            for link, cat, id in zip(subcat_links, subcat, subcat_id):
                                datas.append(self.crawl(link, cat, id))

                    fix_data, code = Utility.resp404(data)
                    results = dumps(fix_data, indent=4)

            return Response(
                response=results,
                headers={
                    "Content-Type": "application/json; charset=UTF-8"},
                status=code
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
                headers={"Content-Type": "application/json;"},
                status=500
            )
