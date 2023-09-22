from ebooksdirectory import Utility as UEBD, MatchingEBD
from hathitrust import Utility as UHT, Select
from freetechbooks import BrowseBooks, Utility as UFCB

from flask_restx import Api, Resource
from flask import Flask, Response, request


app = Flask(__name__)
api = Api(app, version='1.0', title='API Crawl', description='Masih Pemula')

ns1 = api.namespace('ebooksdirectory',
                    description='API Crawling web e-booksdirectory')
ns2 = api.namespace('hathitrust',
                    description='API Crawling web hathitrust')
ns3 = api.namespace(
    'freetechbooks', description='API Crawling web freetechbooks')

# EBOOKSDIRECTORY


@ns1.route('/get-books')
@ns1.doc(
    params={
        "filters": {
            "description": "Define filters",
            "enum": [value for value in UEBD.filters],
            "default": UEBD.filters[0]
        },
        "category": {
            "description": "If filters is categories then you are required to select this. If it's not categories don't choose this",
            "enum": [value for value in UEBD.cat]
        },
        "countpage": {
            "description": "How many pages will you take?",
            "type": int
        }
    }
)
class GetValueEBD(Resource):
    def get(self):
        try:
            filters = request.args.get('filters')
            category = request.args.get('category')
            nop = request.args.get('countpage')
            match = MatchingEBD(filters, category, nop)
            return match.match()
        except Exception as ex:
            resp, code = UEBD.returnError(ex)
            return Response(response=resp, status=code)


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
        try:
            keyword = request.args.get('keyword')
            value = request.args.get('types')
            type = ''.join(
                [key for key, val in UHT.types.items() if val == value])
            page = request.args.get('page')
            pagesize = request.args.get('pagesize')
            match = Select(keyword, type, page, pagesize)
            return match.displaysResults()
        except Exception as ex:
            resp, code = UHT.returnError(ex)
            return Response(response=resp, status=code)


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
        try:
            page = request.args.get('page')
            BB = BrowseBooks('all', page=page)
            return BB.displayResult()
        except Exception as ex:
            resp, code = UFCB.returnError(ex)
            return Response(response=resp, status=code)


@ns3.route('/get-all-subcategories')
class GetAllSubCat(Resource):
    def get(self):
        try:
            BB = BrowseBooks('category')
            return BB.displayResult()
        except Exception as ex:
            resp, code = UFCB.returnError(ex)
            return Response(response=resp, status=code)


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
        try:
            subcat_id = request.args.get('id')
            page = request.args.get('page')
            BB = BrowseBooks(by='asc', page=page, id=subcat_id)
            return BB.displayResult()
        except Exception as ex:
            resp, code = UFCB.returnError(ex)
            return Response(response=resp, status=code)


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
        try:
            page = request.args.get('page')
            BB = BrowseBooks('author', page)
            return BB.displayResult()
        except Exception as ex:
            resp, code = UFCB.returnError(ex)
            return Response(response=resp, status=code)


@ns3.route('/get-all-authors-books')
@ns3.doc(
    params={
        "id": {
            "description": "id is the id of all-sub-categories",
            "required": True
        }
    }
)
class GetValueAuthors(Resource):
    def get(self):
        try:
            subcat_id = request.args.get('id')
            BB = BrowseBooks(id=subcat_id)
            return BB.displayResult()
        except Exception as ex:
            resp, code = UFCB.returnError(ex)
            return Response(response=resp, status=code)


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
        try:
            page = request.args.get('page')
            BB = BrowseBooks('publisher', page)
            return BB.displayResult()
        except Exception as ex:
            resp, code = UFCB.returnError(ex)
            return Response(response=resp, status=code)


@ns3.route('/get-all-publishers-books')
@ns3.doc(
    params={
        "id": {
            "description": "id is the id of all-sub-categories",
            "required": True
        }
    }
)
class GetValuePubs(Resource):
    def get(self):
        try:
            subcat_id = request.args.get('id')
            BB = BrowseBooks(id=subcat_id)
            return BB.displayResult()
        except Exception as ex:
            resp, code = UFCB.returnError(ex)
            return Response(response=resp, status=code)


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
        try:
            page = request.args.get('page')
            BB = BrowseBooks('license', page)
            return BB.displayResult()
        except Exception as ex:
            resp, code = UFCB.returnError(ex)
            return Response(response=resp, status=code)


@ns3.route('/get-all-licenses-books')
@ns3.doc(
    params={
        "id": {
            "description": "id is the id of all-sub-categories",
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
        try:
            subcat_id = request.args.get('id')
            page = request.args.get('page')
            BB = BrowseBooks(by='lic', page=page, id=subcat_id)
            return BB.displayResult()
        except Exception as ex:
            resp, code = UFCB.returnError(ex)
            return Response(response=resp, status=code)


if __name__ == '__main__':
    app.run(debug=True)
