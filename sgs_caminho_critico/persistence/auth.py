# # from fastapi_sqlalchemy import db
# from db import Tokens
#
#
# def get_id_owner_from_token(token):
#     result = db.session.query(Tokens.id, Tokens.owner).filter(
#         Tokens.token == token).first()
#     return result
#
#
# def token_has_agilebook_permission(token_id: int, name: str):
#     result_db = db.session.query(Tokens.id).filter(Tokens.agilebook_name == name).first()
#     if result_db is None:
#         return False
#     else:
#         return True
