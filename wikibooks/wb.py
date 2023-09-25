import re
from json import dumps, loads
from flask import Response

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
        return cleaned_text.strip().rstrip(":,./;'\=-")

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

    def resp400(datas: dict):
        if datas['data'] != []:
            return datas, datas['status']
        else:
            datas.update({'status': 400})
            return datas, datas['status']

    def tostring(value: list):
        return ', '.join([' '.join(item) for item in value])


class TakeWB:
    def __init__(self, departement=None, listDepartement=False, id=None, keyword=None, limit=20, page=1):
        self.departement = departement
        self.listDepartement = listDepartement
        self.id = id
        self.keyword = keyword.replace(' ', '+')
        self.limit = limit
        self.page = page
        self.offset = int(page)*int(limit)
        self.ua = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'}
        if self.listDepartement is True:
            self.url = 'https://en.wikibooks.org/wiki/Main_Page'
        elif self.departement != None:
            self.url = f'https://en.wikibooks.org/wiki/Department:{self.departement}'
        elif self.id != None:
            self.url = f'https://en.wikibooks.org/w/api.php?action=query&prop=revisions&titles={self.id}&rvslots=*&rvprop=content&formatversion=2&format=json'
        elif self.keyword != None:
            self.url = f'https://en.wikibooks.org/w/index.php?title=Special:Search&limit={self.limit}&offset={self.offset}&ns0=1&search={self.keyword}'

    def BSoup(self, tag=None, attr=None):
        resp = requests.get(self.url, headers=self.ua)
        soup = BeautifulSoup(resp.text, 'lxml')
        match attr:
            case {'style': 'flex: 1 0 50%; width:50%; min-width:10em; float: right; box-sizing: border-box; font-size:95%; display: flex; flex-wrap: wrap;'}:
                for item in soup.find_all(tag, attr):
                    return item
            case {'style': 'vertical-align:top; height:1%; padding:0em 0.5em 0.2em 0.5em; width:50%;'}:
                for item in soup.find_all(tag, attr):
                    return item
            case 'vector-body':
                for item in soup.find_all(tag, attr):
                    return item
            case {'id': 'mw-search-top-table'}:
                for item in soup.find_all(tag, attr):
                    return item
            case _:
                return soup

    def nextPage(self, item):
        count = ''.join([div['data-mw-num-results-total']
                        for div in item.find_all('div', 'results-info')])
        mp = int(count)//int(self.limit)
        return int(self.page)+1 if int(self.page) < int(mp) else '' if int(mp) == int(self.page) else ''

    def takeResults(self, item):
        links = ['https://en.wikibooks.org'+a['href'] for ul in item.find_all(
            'ul', 'mw-search-results') for a in ul.find_all('a', class_=False)]
        title = [a.text for ul in item.find_all(
            'ul', 'mw-search-results') for a in ul.find_all('a', class_=False)]
        id = [re.search(r'\/wiki\/(.+)', a['href']).group(1) for ul in item.find_all(
            'ul', 'mw-search-results') for a in ul.find_all('a', class_=False)]
        raw = [div.text.split(' - ')[0]
               for div in item.find_all('div', 'mw-search-result-data')]
        filesize = [Utility.tostring(re.findall(
            r'(\d+)\s*(KB|MB)', value)) for value in raw]
        countword = [re.search(r'\((.*?)\)', value).group(1) for value in raw]

        return links, title, id, filesize, countword

    def dept(self, item):
        deplinks = Utility.unique(['https://en.wikibooks.org'+a['href']
                                   for a in item.find_all('a', class_=False)])
        deptitles = [a.text for a in item.find_all('a', class_=False)]
        depids = [teks.replace(' ', '_')
                  for teks in deptitles if teks != 'All subjects']
        return deplinks, deptitles, depids

    def featuredBooks(self, item):
        fblinks = Utility.unique(['https://en.wikibooks.org'+a['href']
                                  for li in item.find_all('li', class_=False) for a in li.find_all('a', class_=False)])
        fbtitles = [a.text for li in item.find_all(
            'li', class_=False) for a in li.find_all('a', class_=False)]
        fbids = [teks.replace(' ', '_').replace("'", '%27')
                 for teks in fbtitles]
        return fblinks, fbtitles, fbids

    def book(self, item):
        title = [loads(p.text)['query']['pages'][0]['title']
                 for p in item.find_all('p', class_=False)]
        content = [loads(p.text)['query']['pages'][0]['revisions'][0]['slots']
                   ['main']['content'] for p in item.find_all('p', class_=False)]
        return ''.join(title), ''.join(content)

    def crawl(self, link=None, title=None, id=None, content=None, filesize=None, countword=None):
        if self.id == None:
            data = {
                "link": link,
                "title": title,
                "id": id
            }
        elif self.id != None:
            data = {
                "title": title,
                "content": content
            }
        elif self.keyword != None:
            data = {
                "link": link,
                "title": title,
                "featured_book": id,
                "file_size": filesize,
                "count_word": countword
            }
        return data

    def displayResult(self):
        datas = []
        if self.listDepartement is True:
            item = self.BSoup('div', {
                              'style': 'flex: 1 0 50%; width:50%; min-width:10em; float: right; box-sizing: border-box; font-size:95%; display: flex; flex-wrap: wrap;'})
            data = {
                "status": 200,
                "data": datas
            }
            links, titles, ids = self.dept(item)
            for link, title, id in zip(links, titles, ids):
                datas.append(self.crawl(link, title, id))
        elif self.departement != None:
            item = self.BSoup('td', {
                              'style': 'vertical-align:top; height:1%; padding:0em 0.5em 0.2em 0.5em; width:50%;'})
            data = {
                "status": 200,
                "data": datas
            }
            links, titles, ids = self.featuredBooks(item)
            for link, title, id in zip(links, titles, ids):
                datas.append(self.crawl(link, title, id))
        elif self.id != None:
            item = self.BSoup()
            title, content = self.book(item)
            data = {
                "status": 200,
                "data": self.crawl(title=title, content=content)
            }
        elif self.keyword != None:
            item = self.BSoup('div', 'vector-body')
            data = {
                "status": 200,
                "data": datas,
                "next_page": self.nextPage(item)
            }
            links, titles, ids, filesize, countword = self.takeResults(item)
            for link, title, id, fs, cw in zip(links, titles, ids, filesize, countword):
                datas.append(self.crawl(link, title, id, fs, cw))

        fix_data, code = Utility.resp400(data)
        results = dumps(fix_data, indent=4)

        return Response(
            response=results,
            headers={"Content-Type": "application/json; charset=UTF-8"},
            status=code
        )
