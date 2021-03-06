# -*- coding: utf-8 -*-

import json

from base64 import b64encode

from flask import request
from flask import redirect
from flask import url_for
from flask import session
from flask import make_response

from radiople.libs.response import view_response
from radiople.libs.response import json_response

from radiople.libs.permission import ConsoleAuthorization
from radiople.libs.permission import Service

from radiople.model.user_token import UserTokenUsage
from radiople.model.role import Role

from radiople.service.crypto import password_service
from radiople.service.crypto import access_token_service
from radiople.service.user_auth import console_service as user_auth_service
from radiople.service.user_token import console_service as user_token_service
from radiople.service.broadcast import console_service as broadcast_service

from radiople.exceptions import NotFound
from radiople.exceptions import BadRequest
from radiople.exceptions import AccessDenied

from radiople.console.controller import bp_auth

from radiople.console.form.auth import AuthLoginForm


@bp_auth.route('/signin.html', methods=['GET'])
@ConsoleAuthorization(Role.ALL)
@view_response('auth/signin.html')
def signin_html():
    pass


@bp_auth.route('/signin', methods=['POST'])
@ConsoleAuthorization(Role.ALL)
@json_response()
def signin():
    form = AuthLoginForm(request.form)
    if not form.validate():
        raise BadRequest(form.error_message)

    user_auth = user_auth_service.get_by_email(form.data['email'])
    if not user_auth:
        raise NotFound("이메일 혹은 비밀번호가 옳바르지 않습니다.")

    if not password_service.match(
            user_auth.password, user_auth.salt, form.data['password']):
        raise NotFound("이메일 혹은 비밀번호가 옳바르지 않습니다.")

    broadcasts = broadcast_service.get_all_by_user_id(user_auth.user_id)
    broadcast_ids = [broadcast.id for broadcast in broadcasts]

    access_token, expires_at, hashed = access_token_service.issue(
        user_id=user_auth.user_id, broadcast_ids=broadcast_ids,
        service=Service.CONSOLE)

    user_token_service.insert(
        user_id=user_auth.user_id,
        usage=UserTokenUsage.CONSOLE,
        token=hashed,
        expires_at=expires_at,
    )

    response = make_response()
    response.set_cookie('access_token', access_token)
    response.set_cookie('broadcast_id', str(broadcasts[0].id))

    return response


@bp_auth.route('/signout', methods=['GET'])
def signout():
    response = make_response(redirect(url_for('bp_auth.signin_html')))
    response.set_cookie('access_token', expires=0)
    response.set_cookie('broadcast_id', expires=0)
    return response


@bp_auth.route('/current-broadcast', methods=['PUT'])
@ConsoleAuthorization(Role.ADMIN, Role.DJ)
def change_current_broadcast():
    broadcast_id = int(request.form.get('broadcast_id'))
    if broadcast_id not in request.auth.broadcast_ids:
        raise AccessDenied

    response = make_response()
    response.set_cookie('broadcast_id', str(broadcast_id))

    return response
