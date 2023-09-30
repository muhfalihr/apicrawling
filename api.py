from ebooksdirectory import Utility as UEBD, AllCategories
from hathitrust import Utility as UHT, Select
from freetechbooks import BrowseBooks
from pdfdrive import Search, Utility as UPD
from wikibooks import TakeWB, download as Download

from flask_restx import Api, Resource
from flask import Flask, request


app = Flask(__name__)
api = Api(app, version='1.0', title='API Crawl',
          description='API Hasil Crawling Website')

ns1 = api.namespace('ebooksdirectory',
                    description='API Crawling web e-booksdirectory')
ns2 = api.namespace('hathitrust',
                    description='API Crawling web hathitrust')
ns3 = api.namespace(
    'freetechbooks', description='API Crawling web freetechbooks')
ns4 = api.namespace('pdfdrive', description='API Crawling web pdfdrive')
ns5 = api.namespace('wikibooks', description='API Crawling web wikibooks')


# EBOOKSDIRECTORY
@ns1.route('/get-all-categories')
class GetAllCatEBD(Resource):
    def get(self):
        '''Mengembalikan All Categories'''
        EBD = AllCategories(allcategories=True)
        return EBD.displayResult()


@ns1.route('/get-books')
@ns1.doc(
    params={
        "filters": {
            "description": "Define filters",
            "enum": [value for value in UEBD.filters],
            "default": UEBD.filters[0]
        },
        "category": {
            "description": "id taken from get all categories"
        },
        "page": {
            "description": "How many pages will you take?",
            "type": int
        }
    }
)
class GetValueEBD(Resource):
    @ns1.doc(description="NOTE:\nBila menggunakan filter categories maka untuk parameter countpage dikosongkan saja, dan untuk yang selain filter categories parameter category kosongkan saja")
    def get(self):
        '''Mengembalikan books sesuai filter categories, new, top, dan popular'''
        filters = request.args.get('filters')
        category = request.args.get('category')
        page = request.args.get('page')
        EBD = AllCategories(option=filters, id=category, page=page)
        return EBD.displayResult()


# HATHITRUST
value = UHT.types.values()
default = list(value)[0]


@ns2.route('/get-books')
@ns2.doc(
    params={
        "keyword": {
            "description": "what keywords do you want to search for",
            "required": True
        },
        "types": {
            "description": "search type",
            "enum": [value for value in UHT.types.values()],
            "default": default
        },
        "page": {
            "description": "what page do you want to take?",
            "type": int,
            "default": 1
        },
        "pagesize": {
            "description": "number of articles on one page (but for the type full text & all fields the default is 100)",
            "type": int,
            "default": 10
        }
    }
)
class GetValueHT(Resource):
    def get(self):
        '''Melakukan Pencarian dari menentukan types, keyword, dll'''
        keyword = request.args.get('keyword')
        value = request.args.get('types')
        type = ''.join(
            [key for key, val in UHT.types.items() if val == value])
        page = request.args.get('page')
        pagesize = request.args.get('pagesize')
        match = Select(keyword, type, page, pagesize)
        return match.displaysResults()


# FREETECHBOOKS
@ns3.route('/get-all-books')
@ns3.doc(
    params={
        "page": {
            "description": "what page do you want to take?",
            "type": int,
            "default": 1
        }
    }
)
class GetValueFTB1(Resource):
    def get(self):
        '''Mengembalikan All Books berdasarkan page'''
        page = request.args.get('page')
        BB = BrowseBooks('all', page=page)
        return BB.displayResult()


@ns3.route('/get-all-subcategories')
class GetAllSubCat(Resource):
    def get(self):
        '''Mengembalikan All Categories'''
        BB = BrowseBooks('category')
        return BB.displayResult()


@ns3.route('/get-all-subcategories-books')
@ns3.doc(
    params={
        "id": {
            "description": "id is the id of all-sub-categories",
            "required": True
        },
        "page": {
            'description': 'what page do you want to take?',
            'type': int,
            'default': 1
        }
    }
)
class GetValueSubCat(Resource):
    def get(self):
        '''Mengembalikan All Books sesuai id category'''
        subcat_id = request.args.get('id')
        page = request.args.get('page')
        BB = BrowseBooks(by='asc', page=page, id=subcat_id)
        return BB.displayResult()


@ns3.route('/get-all-authors')
@ns3.doc(
    params={
        'page': {
            'description': 'what page do you want to take?',
            'type': int,
            'default': 1
        }
    }
)
class GetAllAuthors(Resource):
    def get(self):
        '''Mengembalikan All Authors'''
        page = request.args.get('page')
        BB = BrowseBooks('author', page)
        return BB.displayResult()


@ns3.route('/get-all-authors-books')
@ns3.doc(
    params={
        "id": {
            "description": "id is the id of all-authors",
            "required": True
        }
    }
)
class GetValueAuthors(Resource):
    def get(self):
        '''Mengembalikan All Books sesuai id authors'''
        subcat_id = request.args.get('id')
        BB = BrowseBooks(id=subcat_id)
        return BB.displayResult()


@ns3.route('/get-all-publishers')
@ns3.doc(
    params={
        'page': {
            'description': 'what page do you want to take?',
            'type': int,
            'default': 1
        }
    }
)
class GetAllPubs(Resource):
    def get(self):
        '''Mengembalikan All Publishers'''
        page = request.args.get('page')
        BB = BrowseBooks('publisher', page)
        return BB.displayResult()


@ns3.route('/get-all-publishers-books')
@ns3.doc(
    params={
        "id": {
            "description": "id is the id of all-publishers",
            "required": True
        }
    }
)
class GetValuePubs(Resource):
    def get(self):
        '''Mengembalikan All Books sesuai id Publisher'''
        subcat_id = request.args.get('id')
        BB = BrowseBooks(id=subcat_id)
        return BB.displayResult()


@ns3.route('/get-all-licenses')
@ns3.doc(
    params={
        'page': {
            'description': 'what page do you want to take?',
            'type': int,
            'default': 1
        }
    }
)
class GetAllLic(Resource):
    def get(self):
        '''Mengembalikan All Licenses'''
        page = request.args.get('page')
        BB = BrowseBooks('license', page)
        return BB.displayResult()


@ns3.route('/get-all-licenses-books')
@ns3.doc(
    params={
        "id": {
            "description": "id is the id of all-licenses",
            "required": True
        },
        'page': {
            'description': 'what page do you want to take?',
            'type': int,
            'default': 1
        }
    }
)
class GetValueLic(Resource):
    def get(self):
        '''Mengembalikan All Books sesuai id license'''
        subcat_id = request.args.get('id')
        page = request.args.get('page')
        BB = BrowseBooks(by='lic', page=page, id=subcat_id)
        return BB.displayResult()


# PDFDRIVE
@ns4.route('/get-books-by-search')
@ns4.doc(
    params={
        "keyword": {
            "description": "Define keywords!",
            "required": True
        },
        "pagecount": {
            "description": "number of book pages",
            "enum": [value for value in UPD.pagecount.values()],
            "default": [value for value in UPD.pagecount.values()][0]
        },
        "pubyear": {
            "description": "the year this book was published",
            "enum": [value for value in UPD.pubyear],
            "default": UPD.pubyear[0]
        },
        "exactmatch": {
            "description": "search that actually matches",
            "enum": [value for value in UPD.exactmatch],
            "default": UPD.exactmatch[0]
        },
        "page": {
            "description": "what page?",
            "type": int,
            "default": 1
        }
    }
)
class GetValuePD(Resource):
    def get(self):
        '''Mengembalikan All Books by search'''
        keyword = request.args.get('keyword')
        pc = request.args.get('pagecount')
        pagecount = ''.join(
            [key for key, val in UPD.pagecount.items() if val == pc])
        pubyear = request.args.get('pubyear')
        exactmatch = request.args.get('exactmatch')
        page = request.args.get('page')
        SS = Search(keyword, pagecount, pubyear,
                    exactmatch=exactmatch, page=page)
        return SS.displayResult()


@ns4.route('/get-all-categories')
class GetAllCat(Resource):
    def get(self):
        '''Mengembalikan All Categories'''
        SS = Search(categories_list=True)
        return SS.displayResult()


@ns4.route('/get-subcategories-by-id')
@ns4.doc(
    description='NOTE:\nTidak semua categori memiliki sub categori. Jadi, jika return status nya adalah 400/404 berarti categori tersebut tidak memiliki sub categori.',
    params={
        "categoryid": {
            "description": "ID taken from get all categories",
            "required": True
        }
    }
)
class GetAllSubCat(Resource):
    def get(self):
        '''Mengembalikan Sub Categories by id category'''
        category = request.args.get('categoryid')
        SS = Search(category=category, categories_list=True, subcat=True)
        return SS.displayResult()


@ns4.route('/get-books-by-categories-or-subcategories')
@ns4.doc(
    params={
        "cat_subcat_id": {
            "description": "Use IDs from Categories or SubCategories",
            "required": True
        },
        "page": {
            "description": "what page?",
            "type": int,
            "default": 1
        }
    }
)
class GetCatSubcat(Resource):
    def get(self):
        '''Mengembalikan All Books by id category atau id subcategory'''
        catsubcatid = request.args.get('cat_subcat_id')
        page = request.args.get('page')
        SS = Search(category=catsubcatid, page=page)
        return SS.displayResult()


# WIKIBOOKS
@ns5.route('/get-all-departements')
class GetAllDept(Resource):
    def get(self):
        '''Mengembalikan All Departement'''
        TWB = TakeWB(listDepartement=True)
        return TWB.displayResult()


@ns5.route('/get-all-featured-books-by-departement')
@ns5.doc(
    params={
        "departement": {
            "description": "department id taken from get all departments",
            "required": True
        }
    }
)
class GetAllFB(Resource):
    def get(self):
        '''Mengembalikan All Featured Books by departement'''
        departement = request.args.get('departement')
        TWB = TakeWB(departement=departement)
        return TWB.displayResult()


@ns5.route('/get-featured-books')
@ns5.doc(
    params={
        "departement": {
            "description": "department id taken from get all featured books by departements",
            "required": True
        }
    }
)
class GetFB(Resource):
    def get(self):
        '''Mengembalikan isi dari featured book'''
        departement = request.args.get('departement')
        TWB = TakeWB(id=departement)
        return TWB.displayResult()


@ns5.route('/get-books-by-search')
@ns5.doc(
    params={
        "keyword": {
            "description": "Searched Keywords",
            "required": True
        },
        "page": {
            "description": "what page?",
            "type": int,
            "default": 1
        },
        "pagesize": {
            "description": "number of books on one page",
            "type": int,
            "default": 20
        }
    }
)
class GetBooksSearch(Resource):
    def get(self):
        '''Mengembalikan All Books by search'''
        keyword = request.args.get('keyword')
        page = request.args.get('page')
        pagesize = request.args.get('pagesize')
        TWB = TakeWB(keyword=keyword, limit=pagesize, page=page)
        return TWB.displayResult()


@ns5.route('/download/pdf')
@ns5.doc(
    params={
        "title": {
            "description": "from id title",
            "required": True
        }
    }
)
class DownloadPDF(Resource):
    def get(self):
        '''Unduh PDF by id title'''
        title = request.args.get('title')
        download = Download(title)
        return download.req()


if __name__ == '__main__':
    app.run(debug=True)
