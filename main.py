import os
import hmac
import string
import re
import random
import hashlib


import jinja2
import webapp2

from google.appengine.ext import db

secret = "8pY#P#oILap52dQ4F97qtZwRq5VvZCE&"

template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

# aceptable charracters for verifying user data
alphabet_int = dict(zip(string.ascii_lowercase, range(1, 27)))
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")


# create google app entitiy
class BlogPost(db.Model):
    subject = db.StringProperty(required=True)
    blog = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)


class User(db.Model):
    username = db.StringProperty(required=True)
    email = db.StringProperty(required=False)
    password = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        secure_val = make_secure_val(val)
        self.response.headers.add_header('Set-Cookie',
                                         '%s=%s; Path=/' % (name, secure_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return check_secure_val(cookie_val)

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie("user_id")
        if uid:
            self.user = uid and User.get_by_id(int(uid))



class UserListHandler(Handler):
    def get(self):
        users = db.GqlQuery("SELECT * FROM User "
                            "ORDER BY created DESC ")

        self.render("userlist.html", users=users)


class MainPageHandler(Handler):
    def get(self):
        blogposts = db.GqlQuery("SELECT * FROM BlogPost "
                                "ORDER BY created DESC ")

        self.render("blogposts.html", blogposts=blogposts)


class NewPostHandler(Handler):
    def get(self):
        self.render("newpost.html", subject="", content="")

    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")

        subject_error = ""
        blog_error = ""

        if subject and content:
            a = BlogPost(subject=subject, blog=content)
            a.put()
            i = a.key().id()
            self.redirect("/%d" % i)
        else:
            if not subject:
                subject_error = "Please add a subject"
            if not content:
                blog_error = "Please add a blog post"
            self.render("newpost.html", subject=subject, content=content,
                        subject_error=subject_error, blog_error=blog_error)


class PermalinkHandler(Handler):
    def get(self, blog_id):
        s = BlogPost.get_by_id(int(blog_id))
        self.render("blogposts.html", blogposts=[s])


class SignHandler(Handler):
    def get(self):
        self.render("signup.html", username="", password="", verify="", email="")

    def post(self):
        username = self.request.get("username")
        password = self.request.get("password")
        verify = self.request.get("verify")
        email = self.request.get("email")

        redirect, username, password, verify, email, user_error, password_error, verify_error, email_error = check_details(username, password, verify, email)

        if redirect:
            # hash password
            password = make_pw_hash(username, password)
            # save details to database
            a = User(username=username, password=password, email=email)
            a.put()
            i = "%d" % (a.key().id())
            self.set_secure_cookie("user_id", i)
            self.redirect("/welcome")
        else:
            self.render("signup.html", username=username,
                        password=password, verify=verify, email=email, user_error=user_error, password_error=password_error, verify_error=verify_error, email_error=email_error)


class LoginHandler(Handler):
    def get(self):
        self.render("login.html", username="", password="", login_error="")

    def post(self):
        username = self.request.get("username")
        password = self.request.get("password")

        user = User.all().filter("username =", username).get()
        if user and valid_pw(username, password, user.password):
            i = "%d" % (user.key().id())
            self.set_secure_cookie("user_id", i)
            self.redirect("/welcome")
        else:
            login_error = "That is not a valid user/password"
            self.render("login.html", username=username, password=password, login_error=login_error)


class WelcomeHandler(Handler):
    def get(self):
        if self.user:
            self.render("welcome.html", username=self.user.username)
        else:
            self.redirect("/signup")


# test for acceptable user name, password, email
def valid_username(username):
    return USER_RE.match(username)


def valid_password(password):
    return PASS_RE.match(password)


def valid_email(email):
    return EMAIL_RE.match(email)


def matching_users(username):
    # check if username already exists
    matching_users = User.all()
    matching_users = matching_users.filter("username = ", username).get()
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


# create and test hash
def make_secure_val(val):
    return "%s|%s" % (val, hmac.new(secret, val).hexdigest())


def check_secure_val(secure_val):
    if secure_val:
        val = secure_val.split('|')[0]
        if secure_val == make_secure_val(val):
            return val


# create and test password hashs
def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))


def make_pw_hash(username, password, salt=None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(username + password + salt).hexdigest()
    saved_hash = '%s|%s' % (h, salt)
    return saved_hash


def valid_pw(username, password, saved_hash):
    salt = saved_hash.split('|')[1]
    if make_pw_hash(username, password, salt) == saved_hash:
        return True


app = webapp2.WSGIApplication([
    ('/', MainPageHandler),
    ('/newpost', NewPostHandler),
    ('/(\d+)', PermalinkHandler),
    ('/signup', SignHandler),
    ('/welcome', WelcomeHandler),
    ('/users', UserListHandler),
    ('/login', LoginHandler),
], debug=True)
