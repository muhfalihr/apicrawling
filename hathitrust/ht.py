import re
import unicodedata
from json import dumps
from flask import Response

from bs4 import BeautifulSoup
import requests


class Utility:
    # Dictionary untuk dropdown option swagger ui
    types = {
        'ftaf': 'Full Text & All Fields',
        'all': 'All Fields',
        'title': 'Title',
        'author': 'Author',
        'subject': 'Subject',
        'isn': 'ISBN/ISSN',
        'publisher': 'Publisher',
        'seriestitle': 'Series Title'
    }

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

    def remSimp(values: list):
        complete_values = {}

        for value in values:
            parts = value.split('/')
            first_part = parts[0].strip()
            if first_part not in complete_values or len(value) > len(complete_values[first_part]):
                complete_values[first_part] = value

        comval = list(complete_values.values())
        result = []
        for item in comval:
            is_more_specific = False

            for other_item in comval:
                if item != other_item and item in other_item:
                    is_more_specific = True
                    break

            if not is_more_specific:
                result.append(item)

        return result

    def clean(text):
        '''Mengganti string uniq dengan dengan string sesuai format ascii, serta menghilangkan "\n" serta mengganati kutip dua menjadi kutip satu. Serta menghilangkan karakter tidak penting diakhir kalimat atau kata'''
        cleaned = re.sub(r'\n+', '\n', text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned)
        normalized = unicodedata.normalize('NFKD', cleaned_text)
        ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
        replace_text = ascii_text.replace('\"', "'").replace('\r\n', ' - ')
        return replace_text.strip().rstrip(",./;'\=-:")

    def unique(inList):
        '''Membuat value di sebuah list menjadi uniq'''
        unique_list = []
        [unique_list.append(x) for x in inList if x not in unique_list]
        return unique_list


class Select:
    def __init__(self, params, type=None, page=1, pagesize=10):
        self.params = params
        self.type = type
        self.page = page
        self.pagesize = pagesize
        self.ua = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'}
        match self.type:
            case 'all' | 'title' | 'author' | 'subject' | 'isn' | 'publisher' | 'seriestitle':
                self.url = f'https://catalog.hathitrust.org/Search/Home?type%5B%5D={self.type}&lookfor%5B%5D={self.params}&page={self.page}&pagesize={self.pagesize}'
            case 'ftaf':
                self.url = f'https://babel.hathitrust.org/cgi/ls?q1={self.params}&field1=ocr&a=srchls&ft=ft&lmt=ft&pn={self.page}'

    def BSoup(self, link, tag=None, cls=None):
        '''cls = class'''
        resp = requests.get(link, headers=self.ua)
        soup = BeautifulSoup(resp.text, 'lxml')
        match cls:
            case None:
                return soup
            case 'results-container':
                items = soup.find_all(tag, cls)
                for item in items:
                    return item
            case 'record d-flex flex-column gap-3 p-3 mb-3 mt-3':
                items = soup.find_all(tag, cls)
                for item in items:
                    return item
            case 'metadata':
                items = soup.find_all(tag, cls)
                for item in items:
                    return item
            case 'mainplain w-auto position-relative':
                items = soup.find_all(tag, cls)
                for item in items:
                    return item

    def getLink(self) -> str:
        match self.type:
            case 'ftaf':
                item = self.BSoup(
                    self.url, 'div', 'mainplain w-auto position-relative')
                return Utility.unique([a['href'] for a in item.find_all('a', 'list-group-item list-group-item-action w-sm-50') if '#viewability' not in a['href']])
            case _:
                item = self.BSoup(self.url, 'div', 'results-container')
                return Utility.unique(['https://catalog.hathitrust.org'+a['href'] for a in item.find_all('a', 'list-group-item list-group-item-action w-sm-50') if '#viewability' not in a['href']])

    def rdMetadata(self, item) -> list:
        return [dt.text for dt in item.find_all('dt', 'g-col-lg-4 g-col-12')]

    def rdValueNotA(self, item) -> list:
        return [Utility.clean(dd.text) for dd in item.find_all('dd', 'g-col-lg-8 g-col-12')]

    def mainAuthor(self, item):
        return ''.join([Utility.clean(a.text) for div in item.find_all('div', 'grid') for dt in div.find_all('dt', 'g-col-lg-4 g-col-12') for a in div.find_all('a', class_=False) if dt.text == 'Main Author'])

    def relNam(self, item):
        values = [Utility.clean(a.text) for div in item.find_all('div', 'grid') for dt in div.find_all(
            'dt', 'g-col-lg-4 g-col-12') for a in div.find_all('a', class_=False) if dt.text == 'Related Names']
        return values if values != [] else ''

    def subjects(self, item):
        values = Utility.remSimp([Utility.clean(a.text).replace('/', '>') for div in item.find_all('div', 'grid') for dt in div.find_all(
            'dt', 'g-col-lg-4 g-col-12') for a in div.find_all('a', class_=False) if dt.text == 'Subjects'])
        return values if values != [] else ''

    def isbn(self, item):
        for div in item.find_all('div', 'grid'):
            for dt in div.find_all('dt', 'g-col-lg-4 g-col-12'):
                for dd in div.find_all('dd', 'g-col-lg-8 g-col-12'):
                    if dt.text == 'ISBN':
                        result = Utility.clean(dd.text).split()
                        return result if result != [''] else ''

    def rdOriginSite(self, item) -> str:
        values = [a['href'] for dd in item.find_all(
            'dd', 'g-col-lg-8 g-col-12') for a in dd.find_all('a') if a.text == 'Find in a library']
        return values if values != [] else ''

    def matching_is_not_a(self, value, item):
        if value not in self.rdMetadata(item):
            return ''
        index = self.rdMetadata(item).index(value)
        return self.rdValueNotA(item)[index]

    def nextPage(self):
        soup = self.BSoup(self.url)
        np = [hrp['data-prop-next-href']
              for hrp in soup.find_all('hathi-results-pagination')][0]
        mp = [hrp['data-prop-max-pages']
              for hrp in soup.find_all('hathi-results-pagination')][0]
        match self.type:
            case 'ftaf':
                npNum = re.search(
                    r'a=srchls;lmt=ft;pn=(\d+)', np).group(1)
            case _:
                npNum = re.search(
                    rf'&ft=&pagesize={self.pagesize}&page=(\d+)', np).group(1)
        return '' if int(self.page) == int(mp) else int(npNum) if int(self.page) < int(mp) else ""

    def crawl(self, url):
        item = self.BSoup(
            url, 'article', 'record d-flex flex-column gap-3 p-3 mb-3 mt-3')
        title = item.find('div', 'article-heading d-flex gap-3').h1.text
        # data = self.isbn(item)
        data = {
            'title': Utility.clean(title),
            'description': {
                'main_author': self.mainAuthor(item),
                'related_names': self.relNam(item),
                'languages': self.matching_is_not_a('Language(s)', item),
                'published': self.matching_is_not_a('Published', item),
                'edition': self.matching_is_not_a('Edition', item),
                'subjects': self.subjects(item),
                'summary': self.matching_is_not_a('Summary', item),
                'note': self.matching_is_not_a('Note', item),
                'isbn': self.isbn(item) if self.isbn(item) != None else '',
                'physical_description': self.matching_is_not_a('Physical Description', item),
                'original_site': self.rdOriginSite(item)
            }
        }
        return data

    def displaysResults(self):
        datas = []
        data = {
            'status': 200,
            'data': datas,
            'next_page': self.nextPage()
        }
        for link in self.getLink():
            datas.append(self.crawl(link))

            fix_data, code = Utility.resp400(data)
            results = dumps(fix_data, indent=4)
            # with open('result.json', 'w') as file:
            #     file.write(results)
        return Response(
            response=results,
            headers={"Content-Type": "application/json; charset=UTF-8"},
            status=code
        )


# slct = Select('islam', 'subject')
# slct.displaysResults()
# links = slct.getLink()
# for link in links:
#     view = slct.crawl(link)
#     print(view)
