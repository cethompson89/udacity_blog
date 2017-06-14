import hmac
import string
import re
import random
import hashlib

import models


# create and test hash
def make_secure_val(val):
    secret = "8pY#P#oILap52dQ4F97qtZwRq5VvZCE&"
    return "%s|%s" % (val, hmac.new(secret, val).hexdigest())


def check_secure_val(secure_val):
    if secure_val:
        try:
            val = secure_val.split('|')[0]
        except:
            return None
        if secure_val == make_secure_val(val):
            return val


# test for acceptable user name, password, email
def valid_username(username):
    user_re = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    return user_re.match(username)


def valid_password(password):
    pass_re = re.compile(r"^.{3,20}$")
    return pass_re.match(password)


def valid_email(email):
    email_re = re.compile(r"^[\S]+@[\S]+.[\S]+$")
    return email_re.match(email)


def matching_users(username):
    # check if username already exists
    matching_users = models.User.all().filter("username = ", username).get()
    return matching_users


def check_details(username, password, verify, email):
    user_error, password_error, verify_error, email_error = ("", "", "", "")
    valid_details = True

    if valid_username(username) is None:
        user_error = "That's not a valid username."
        valid_details = False
    elif matching_users(username) is not None:
        user_error = "That user already exists."
        valid_details = False

    if valid_password(password) is None:
        password_error = "That wasn't a valid password."
        valid_details = False
        password = ""
        verify = ""

    if password != verify:
        verify_error = "Your passwords didn't match."
        valid_details = False
        password = ""
        verify = ""

    if email != "" and valid_email(email) is None:
        email_error = "That's not a valid email."
        valid_details = False

    return (valid_details, username, password, verify, email, user_error,
            password_error, verify_error, email_error)


# create and test password hashs
def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))


def make_pw_hash(username, password, salt=None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(username + password + salt).hexdigest()
    saved_hash = '%s|%s' % (h, salt)
    return saved_hash


def check_valid_pw(username, password, saved_hash):
    salt = saved_hash.split('|')[1]
    if make_pw_hash(username, password, salt) == saved_hash:
        return True
