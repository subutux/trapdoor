from passlib.hash import pbkdf2_sha512
from . import db

import logging
log = logging.getLogger('trapdoor.core.authentication')
log.addHandler(logging.NullHandler())

def user_add(session, user, password, superuser=False,
             permission=None):
    
    pass_hash = pbkdf2_sha512.encrypt(password)
    if superuser:
        superuser = 1
    else:
        superuser = 0
    
    user = db.models.User(login=user, password=pass_hash,
                          is_superuser=superuser,permission=permission)
    session.add(user)
    session.commit()
def permission_add(session,group):
    # check first uf permission already exists
    perm = session.query(db.models.Permission).filter_by(name=group).first()
    if perm == None:
        permission = db.models.Permission(name=group)
    else:
        log.warn("Permission '{}' already exists. Using that one.".format(group))
        permission = perm
    return permission

def get_user(session,user):
    return session.query(db.models.User).filter_by(login=user).first()

def update_user_password(session,user,password):
    pass_hash = pbkdf2_sha512.encrypt(password)
    user.password = pass_hash
    session.add(user)
    session.commit()
def verify_password(user,password):
    if pbkdf2_sha512.verify(password,user.password):
        print("OK")
    else:
        log.error("Password does not match!")