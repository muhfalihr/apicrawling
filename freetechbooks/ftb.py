import re
import unicodedata
from flask import Response
from json import dumps

from bs4 import BeautifulSoup
import requests


class Utility:
    def clean(text):
        '''Mengganti string uniq dengan dengan string sesuai format ascii, serta menghilangkan "\n" serta mengganati kutip dua menjadi kutip satu. Serta menghilangkan karakter tidak penting diakhir kalimat atau kata'''
        cleaned = re.sub(r'\n+', '\n', text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned)
        # normalized = unicodedata.normalize('NFKD', cleaned_text)
        # ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
        # replace_text = ascii_text.replace('\"', "'").replace('\r\n', ' - ')
        return cleaned_text.strip().rstrip(",./;'\=-:")

    def unique(inList):
        '''Membuat value di sebuah list menjadi uniq'''
        unique_list = []
        [unique_list.append(x) for x in inList if x not in unique_list]
        return unique_list

    def returnError(message):
        '''Bila swagger mengambalikan server response 500 atau 400 maka akan memunculkan response body sesuai dengan ini.'''
        datas = {
            'status': 500,
            'data': [],
            'next_page': ''
        }
        datas_dumps = dumps(datas, indent=4)
        return datas_dumps, datas['status']

    def espFN(text):
        words = text.split()
        reversed_text = ' '.join(words[1:])+f' {words[0]}'
        return reversed_text

    def resp400(datas: dict):
        if datas['data'] != []:
            return datas, datas['status']
        else:
            datas.update({'status': 400})
            return datas, datas['status']


class BrowseBooks:
    '''{
        'all': 'topics',
        'category': 'categories',
        'author': 'authors',
        'publisher': 'publishers',
        'license': 'licenses'
    }'''
    __bb = {
        'all': 'topics',
        'category': 'categories',
        'author': 'authors',
        'publisher': 'publishers',
        'license': 'licenses'
    }

    def __init__(self, by=None, page=1, id=None):
        try:
            self.by = self.__bb[by]
        except KeyError:
            self.by = by
        self.page = page
        self.id = id
        self.ua = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'}

        match self.by:
            case None:
                self.link = f'https://www.freetechbooks.com/{self.id}.html'
            case 'topics' | 'authors' | 'publishers' | 'licenses':
                self.link = f'https://www.freetechbooks.com/{self.by}?page={self.page}'
            case 'categories':
                self.link = f'https://www.freetechbooks.com/{self.by}'
            case 'topics' | _:
                self.link = f'https://www.freetechbooks.com/{self.id}.html?page={self.page}'

    def BSoup(self, link, tag=None, clss=None):
        resp = requests.get(link, headers=self.ua)
        soup = BeautifulSoup(resp.text, 'lxml')
        match clss:
            case None:
                return soup
            case 'col-lg-8 col-md-8':
                for item in soup.find_all(tag, clss):
                    return item

    def maxPage(self):
        item = self.BSoup(self.link, 'div', 'col-lg-8 col-md-8')
        mp = [li.text for ul in item.find_all(
            'ul', 'pagination') for li in ul.find_all('li')][-2]
        return int(mp)

    def getLink(self):
        item = self.BSoup(self.link)
        return Utility.unique([a['href'] for p in item.find_all('p', 'media-heading lead') for a in p.find_all('a')])

    def title(self, item):
        return ''.join([Utility.clean(p.text) for p in item.find_all('p', 'media-heading h3')])

    def thumb(self, item):
        return ''.join([img['src'] for div in item.find_all('div', 'media snippet-show') for img in div.find_all('img', 'thumbnail')])

    def author(self, item):
        return Utility.unique([Utility.clean(img['alt']) for row in item.find_all(
            'div', 'row') for img in row.find_all('img', 'thumbnail')][1:])

    def desc(self, item):
        return [Utility.clean(desc.text)
                for desc in item.find_all('div', 'col-xs-12')][0]

    def tags(self, item):
        return [Utility.clean(a.text) for div in item.find_all('div', class_=False) for a in div.find_all('a') for i in a.find_all('i', 'fa fa-book')]

    def excerpts(self, item):
        return ''.join([Utility.clean(bq.text) for bq in item.find_all('blockquote')])

    def linkDownload(self, item):
        value = ''.join([a['href']
                        for a in item.find_all('a', 'btn btn-primary')])
        return Utility.clean(value)

    def nextPage(self):
        item = self.BSoup(self.link, 'div', 'col-lg-8 col-md-8')
        try:
            mp = [li.text for ul in item.find_all(
                'ul', 'pagination') for li in ul.find_all('li')][-2]
            return int(self.page) + 1 if int(self.page) < int(mp) else '' if int(self.page) == int(mp) else ''
        except IndexError:
            return ''

    def snippetShowKey(self, item):
        return [strong.text for mss in item.find_all('div', 'media snippet-show') for strong in mss.find_all('strong')]

    def snippetShowValue(self, item):
        for span in item.find_all('span', 'visible-xs'):
            for div in span.find_all('div', class_=False):
                for strong in div.find_all('strong'):
                    strong.clear()
                return Utility.clean(div.text).replace('n/a', '').replace('N/A', '').split(':')

    def allSubCategories(self):
        item = self.BSoup(self.link)
        subcat_links = [a['href'] for table in item.find_all(
            'table', 'table table-hover table-responsive') for a in table.find_all('a')]
        subcat_name = [Utility.clean(a.text) for table in item.find_all(
            'table', 'table table-hover table-responsive') for a in table.find_all('a')]
        subcat_id = [re.search(r'/([^/]+)\.html$', a['href']).group(1) for table in item.find_all(
            'table', 'table table-hover table-responsive') for a in table.find_all('a')]
        return subcat_links, subcat_name, subcat_id

    def fnAuthorLinks(self):
        item = self.BSoup(self.link)
        author_links = Utility.unique([a['href'] for td in item.find_all(
            'td', 'col-md-3') for a in td.find_all('a')])
        author_fns = []
        for tb in item.find_all('tbody', class_=False):
            for tr in tb.find_all('tr', class_=False):
                for td in tr.find_all('td', 'col-md-1 text-center'):
                    td.clear()
                author_fns.append(Utility.clean(tr.text))
        author_ids = Utility.unique([re.search(r'/([^/]+)\.html$', a['href']).group(
            1) for td in item.find_all('td', 'col-md-3') for a in td.find_all('a')])
        return author_links, author_fns, author_ids

    def pubslicense(self):
        item = self.BSoup(self.link)
        links = [a['href'] for td in item.find_all(
            'td', 'col-md-6') for a in td.find_all('a')]
        name = [Utility.clean(a.text) for td in item.find_all(
            'td', 'col-md-6') for a in td.find_all('a')]
        ids = [re.search(r'/([^/]+)\.html$', a['href']).group(1)
               for td in item.find_all('td', 'col-md-6') for a in td.find_all('a')]
        return links, name, ids

    def dataCrawl(self, link=None):
        item = self.BSoup(link, 'div', 'col-lg-8 col-md-8')
        key = self.snippetShowKey(item)
        value = self.snippetShowValue(item)

        data = {
            'title': self.title(item),
            'link_thumbnail': self.thumb(item),
            'authors': self.author(item),
            'description': self.desc(item),
            'tags': self.tags(item),
            'publication_date': Utility.clean(value[key.index('Publication date')]),
            'isbn-10': Utility.clean(value[key.index('ISBN-10')]),
            'isbn-13': Utility.clean(value[key.index('ISBN-13')]),
            'paperback': Utility.clean(value[key.index('Paperback')]),
            'views': Utility.clean(value[key.index('Views')]),
            'document_type': Utility.clean(value[key.index('Document Type')]),
            'publisher': Utility.clean(value[key.index('Publisher')]),
            'license': Utility.clean(value[key.index('License')]),
            'post_time': Utility.clean(value[key.index('Post time')])+':00:00',
            'excerpts': self.excerpts(item),
            'link_download': self.linkDownload(item)
        }
        return data

    def crawl(self, link=None, name=None, id=None):
        match self.by:
            case 'topics':
                data = self.dataCrawl(link=link)
            case 'categories':
                data = {
                    'link': link,
                    'subcat_name': name,
                    'subcat_id': id
                }
            case 'authors':
                data = {
                    'link': link,
                    'author_name': name,
                    'author_id': id
                }
            case 'publishers':
                data = {
                    'link': link,
                    'pubs_name': name,
                    'pubs_id': id
                }
            case 'licenses':
                data = {
                    'link': link,
                    'license_name': name,
                    'license_id': id
                }
            case _:
                data = self.dataCrawl(link=link)

        return data

    def displayResult(self):
        datas = []
        match self.by:
            case None:
                data = {
                    'status': 200,
                    'data': datas
                }
                for link in self.getLink():
                    datas.append(self.crawl(link=link))

                fix_data, code = Utility.resp400(data)
                results = dumps(fix_data, indent=4)
            case 'topics':
                data = {
                    'status': 200,
                    'data': datas,
                    'next_page': self.nextPage()
                }
                for link in self.getLink():
                    datas.append(self.crawl(link=link))

                fix_data, code = Utility.resp400(data)
                results = dumps(fix_data, indent=4)

            case 'categories':
                data = {
                    'status': 200,
                    'data': datas
                }
                subcat_links, subcat_name, subcat_id = self.allSubCategories()
                for links, name, id in zip(subcat_links, subcat_name, subcat_id):
                    datas.append(self.crawl(links, name, id))

                fix_data, code = Utility.resp400(data)
                results = dumps(fix_data, indent=4)

            case 'authors':
                data = {
                    'status': 200,
                    'data': datas,
                    'next_page': self.nextPage()
                }
                author_links, author_name, authorid = self.fnAuthorLinks()
                for links, name, id in zip(author_links, author_name, authorid):
                    datas.append(self.crawl(links, Utility.espFN(name), id))

                fix_data, code = Utility.resp400(data)
                results = dumps(fix_data, indent=4)

            case 'publishers' | 'licenses':
                data = {
                    'status': 200,
                    'data': datas,
                    'next_page': self.nextPage()
                }
                pub_links, pub_name, pub_id = self.pubslicense()
                for links, name, id in zip(pub_links, pub_name, pub_id):
                    datas.append(self.crawl(links, name, id))

                fix_data, code = Utility.resp400(data)
                results = dumps(fix_data, indent=4)

            case _:
                data = {
                    'status': 200,
                    'data': datas,
                    'next_page': self.nextPage()
                }
                for link in self.getLink():
                    datas.append(self.crawl(link=link))

                fix_data, code = Utility.resp400(data)
                results = dumps(fix_data, indent=4)

        return Response(
            response=results,
            headers={"Content-Type": "application/json; charset=UTF-8"},
            status=code
        )
