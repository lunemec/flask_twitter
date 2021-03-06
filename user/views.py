import traceback

from flask import jsonify, g, request, render_template, current_app
from flask_restful import Resource

from .auth import auth
from .control import list_users, get_user, create_user
from .exceptions import UserNotFound, UnspecifiedError, InvalidArguments, UserAlreadyExists

__all__ = ('UserToken', 'UserDetail', 'UserListing', 'user_listing', 'user_detail')


def handle_unexpected_exception(f):
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.exception('Unexpected error while processing request.',  extra={'headers': request.headers})
            return {'status_code': 500, 'info': str(e)}, 500
    return wrapper


class UserDetail(Resource):
    decorators = [handle_unexpected_exception]

    @auth.login_required
    def get(self, user_id):
        try:
            data = get_user(user_id)
            return {'status_code': 200, 'data': data}
        except UserNotFound:
            return {'status_code': 404}, 404
        except UnspecifiedError as e:
            return {'status_code': 500, 'info': str(e)}, 500

    def post(self):
        if request.json is not None:
            username = request.json.get('username')
            password = request.json.get('password')
        else:
            return {'status_code': 400, 'info': 'JSON data not provided.'}, 400
        try:
            user_id = create_user(username, password)
        except InvalidArguments:
            return {'status_code': 400, 'info': 'Username or password not provided.'}, 400
        except UserAlreadyExists:
            return {'status_code': 400, 'info': 'User already exists.'}, 400
        except UnspecifiedError as e:
            return {'status_code': 500, 'info': str(e)}, 500

        return {'status_code': 200, 'id': user_id}


class UserToken(Resource):
    decorators = [handle_unexpected_exception, auth.login_required]

    def get(self):
        token = g.user.generate_auth_token()
        return {'status_code': 200, 'token': token.decode('ascii')}


class UserListing(Resource):
    decorators = [handle_unexpected_exception]

    def get(self):
        return {'status_code': 200, 'data': list_users()}


@handle_unexpected_exception
@auth.login_required
def user_listing():
    return render_template('user_listing.html', users=list_users()), 200


@handle_unexpected_exception
@auth.login_required
def user_detail(user_id):
    return render_template('user_detail.html', user=get_user(user_id)), 200
