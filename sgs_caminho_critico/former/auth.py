from fastapi import Depends, Security
from fastapi.security import HTTPBasic, HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.api_key import APIKeyCookie
import session as session
import former.persistence.auth as persistence
from ldap3 import Server, Connection, ALL
import hashlib
import requests
import re
from agz_error_handlers import AgilizaUnauthorized

basic = HTTPBasic()
bearer = HTTPBearer()

basic_multi = HTTPBasic(auto_error=False)
bearer_multi = HTTPBearer(auto_error=False)

api_key_cookie = APIKeyCookie(name="BBSSOToken", auto_error=False)


async def bearer_auth_logic(token):
    hash_object = hashlib.sha512(token.encode())
    sha512_token = hash_object.hexdigest()
    result = persistence.get_id_owner_from_token(sha512_token)
    if result is not None:
        token_id, owner = result
        session.set_var_value(var='token_id', value=token_id)
        session.set_var_value(var='auth', value='bearer')
        session.set_var_value(var='requester', value=owner)
        return True
    else:
        return False


async def bearer_auth(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    if await bearer_auth_logic(credentials.credentials) is False:
        raise AgilizaUnauthorized(info="Token não foi autorizado")


async def basic_auth_logic(username: str, password: str):
    """Verificacao de papeis LDAP."""
    ldap_server = Server("aplic.ldapbb.bb.com.br", get_info=ALL, port=636, use_ssl=True)
    ldap_conn = Connection(ldap_server, user=f"uid={username},ou=funcionarios,ou=usuarios,ou=acesso,O=BB,C=BR", password=f"{password}")

    if not ldap_conn.bind():
        print("bind error", ldap_conn.result)
        return False

    try:
        ldap_conn.search(
            search_base="ou=aplicacao,ou=grupos,ou=acesso,o=bb,c=br",
            search_filter=f"(uniquemember=uid={username},ou=funcionarios,ou=usuarios,ou=acesso,o=bb,c=br)",
            search_scope="SUBTREE",
            attributes=['uid']
        )
    except Exception:
        return False

    papers = re.findall('cn=(.+?),', str(ldap_conn.entries))
    ldap_conn.unbind()
    session.set_var_value(var='auth', value='basic')
    session.set_var_value(var='requester', value=username)
    session.set_var_value(var='papers', value=papers)
    return True


async def basic_auth(credentials: HTTPBasic = Depends(basic)):
    if await basic_auth_logic(
            credentials.username,
            credentials.password) is False:
        raise AgilizaUnauthorized(info="Usuário e senha não autorizados")


async def multi_auth(basic_credentials: HTTPBasic = Depends(basic_multi),
                     bearer_credentials: HTTPBearer = Depends(bearer_multi)):
    try:
        basic_success = await basic_auth_logic(
            basic_credentials.username,
            basic_credentials.password)
    except Exception:
        basic_success = False

    if basic_success is False:
        try:
            bearer_succes = await bearer_auth_logic(
                bearer_credentials.credentials)
        except Exception:
            bearer_succes = False
        if bearer_succes is False:
            raise AgilizaUnauthorized(info="Acesso negado")


async def bbssotoken_auth(api_key_cookie: str = Security(api_key_cookie)):
    if api_key_cookie is None:
        return False
    try:
        cookies = dict()
        cookies['BBSSOToken'] = api_key_cookie
        r = requests.get(
            "https://sso.intranet.bb.com.br/sso/identity/json/attributes",
            cookies=cookies,
            verify=False)
        if r.status_code != 200:
            raise AgilizaUnauthorized(info="Cookie de sessão não é válido")
        papers = []
        response = r.json()
        for role in response['roles']:
            paper = role.split(",")[0]
            papers.append(paper[3:])
        for attribute in response['attribute']:
            if attribute['name'] == "uid":
                session.set_var_value(var='requester', value=attribute['value'])
            elif attribute['name'] == "bb-filtergroup":
                for value in attribute['values']:
                    paper = value.split(",")[0]
                    papers.append(paper[3:])

        session.set_var_value(var='papers', value=papers)
        return True
    except Exception:
        return False


async def user_auth(basic_credentials: HTTPBasic = Depends(basic_multi),
                    cookie_credencial: str = Depends(bbssotoken_auth)):
    if cookie_credencial is False:
        if basic_credentials is None:
            raise AgilizaUnauthorized(info="Acesso Negado")

        basic_success = await basic_auth_logic(
            basic_credentials.username,
            basic_credentials.password)
        if basic_success is False:
            raise AgilizaUnauthorized(info="Acesso Negado")
