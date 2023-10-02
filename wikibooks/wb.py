import re
from json import dumps, loads
from flask import Response, send_file
from io import BytesIO
from datetime import datetime

from bs4 import BeautifulSoup
import requests


class Utility:
    def clean(text):
        '''Mengganti string uniq dengan dengan string sesuai format ascii, serta menghilangkan "\n" serta mengganati kutip dua menjadi kutip satu. Serta menghilangkan karakter tidak penting diakhir kalimat atau kata'''
        cleaned = re.sub(r'\n+', '\n', text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned)
        return cleaned_text.strip().rstrip(":,./;'\=-")

    def unique(inList):
        '''Membuat value di sebuah list menjadi uniq'''
        unique_list = []
        [unique_list.append(x) for x in inList if x not in unique_list]
        return unique_list

    def tostring(value: list):
        return ', '.join([' '.join(item) for item in value])


class TakeWB:
    def __init__(self, departement=None, listDepartement=False, id=None, keyword=None, limit=20, page=1):
        self.departement = departement
        self.listDepartement = listDepartement
        self.id = id
        self.keyword = keyword
        self.limit = limit
        self.page = page
        self.offset = int(page)*int(limit)
        self.ua = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'}
        if self.listDepartement == True:
            self.url = 'https://en.wikibooks.org/wiki/Main_Page'
        elif self.departement != None:
            self.url = f'https://en.wikibooks.org/wiki/Department:{self.departement}'
        elif self.id != None:
            self.url = f'https://en.wikibooks.org/w/api.php?action=query&prop=revisions&titles={self.id}&rvslots=*&rvprop=content&formatversion=2&format=json'
        elif self.keyword != None:
            self.url = f'https://en.wikibooks.org/w/index.php?title=Special:Search&limit={self.limit}&offset={self.offset}&ns0=1&search={self.keyword.replace(" ", "+")}'
        self.resp = requests.get(self.url, headers=self.ua)
        self.soup = BeautifulSoup(self.resp.text, 'lxml')

    def BSoup(self, tag=None, attr=None):
        match attr:
            case {'style': 'flex: 1 0 50%; width:50%; min-width:10em; float: right; box-sizing: border-box; font-size:95%; display: flex; flex-wrap: wrap;'}:
                for item in self.soup.find_all(tag, attr):
                    return item
            case {'style': 'vertical-align:top; height:1%; padding:0em 0.5em 0.2em 0.5em; width:50%;'}:
                for item in self.soup.find_all(tag, attr):
                    return item
            case 'vector-body':
                for item in self.soup.find_all(tag, attr):
                    return item
            case {'id': 'mw-search-top-table'}:
                for item in self.soup.find_all(tag, attr):
                    return item
            case _:
                return self.soup

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

    def book(self):
        value = self.resp.content.decode('utf-8')
        return loads(value)['query']['pages']

    def crawl(self, link=None, title=None, id=None, filesize=None, countword=None):
        if self.id == None:
            data = {
                "link": link,
                "title": title,
                "id": id
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
        status_code = self.resp.status_code
        try:
            if self.listDepartement == True:
                item = self.BSoup('div', {
                    'style': 'flex: 1 0 50%; width:50%; min-width:10em; float: right; box-sizing: border-box; font-size:95%; display: flex; flex-wrap: wrap;'})
                data = {
                    "status": status_code,
                    "data": datas
                }
                links, titles, ids = self.dept(item)
                for link, title, id in zip(links, titles, ids):
                    datas.append(self.crawl(link, title, id))
            elif self.departement != None:
                item = self.BSoup('td', {
                    'style': 'vertical-align:top; height:1%; padding:0em 0.5em 0.2em 0.5em; width:50%;'})
                data = {
                    "status": status_code,
                    "data": datas
                }
                links, titles, ids = self.featuredBooks(item)
                for link, title, id in zip(links, titles, ids):
                    datas.append(self.crawl(link, title, id))
            elif self.id != None:
                content = self.book()
                data = {
                    "status": status_code,
                    "data": content
                }
            elif self.keyword != None:
                item = self.BSoup('div', 'vector-body')
                data = {
                    "status": status_code,
                    "data": datas,
                    "next_page": self.nextPage(item)
                }
                links, titles, ids, filesize, countword = self.takeResults(
                    item)
                for link, title, id, fs, cw in zip(links, titles, ids, filesize, countword):
                    datas.append(self.crawl(link, title, id, fs, cw))

            results = dumps(data, indent=4)

            return Response(
                response=results,
                headers={"Content-Type": "application/json; charset=UTF-8"},
                status=status_code
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


class download:
    def __init__(self, title):
        self.title = title
        self.url = f'https://en.wikibooks.org/api/rest_v1/page/pdf/{title}'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'}

    def req(self):
        resp = requests.get(self.url, headers=self.headers)

        if resp.status_code == 200:
            content = resp.content
            headers = resp.headers
            content_type = headers['content-type']
            filename = self.title+'.pdf'

            file = BytesIO(content)

            response = send_file(
                path_or_file=file, as_attachment=True, mimetype=content_type, download_name=filename, last_modified=datetime.now())

            return response
        else:
            soup = BeautifulSoup(resp.text, 'lxml')
            response = [resp.text for resp in soup.find_all('p')]

            return Response(
                response=response,
                headers={"Content-Type": "application/json; charset=UTF-8"},
                status=resp.status_code
            )
