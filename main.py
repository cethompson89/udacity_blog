import os
import string
import re

import jinja2
import webapp2

template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

alphabet_int = dict(zip(string.ascii_lowercase, range(1, 27)))
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")




class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


class MainPage(Handler):
    def get(self):
        self.render("shopping_list.html")

class FizzBuzzHandler(Handler):
    def get(self):
        n = self.request.get("n",0)
        n = n and int(n)
        self.render("fizzbuzz.html", n=n)

class RotHandler(Handler):
    def get(self):
        self.render("rot13.html", text="")

    def post(self):
        text = self.request.get("text")
        text = rot13(text)
        self.render("rot13.html", text=text)

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
            self.redirect("/welcome?username=" + username)
        else:
            self.render("signup.html", username=username,
                        password=password, verify=verify, email=email, user_error=user_error, password_error=password_error, verify_error=verify_error, email_error=email_error)

class WelcomeHandler(Handler):
    def get(self):
        username = self.request.get("username")
        self.render("welcome.html", username=username)

def rot13(text):
    alp_int = dict(zip(string.ascii_lowercase, range(1, 27)))
    int_alp = dict(zip(range(1, 27), string.ascii_lowercase))
    output_text = ""

    for x in text:
        cap = False
        if x in string.ascii_uppercase:
            x = x.lower()
            cap = True
        if x in string.ascii_lowercase:
            x = alp_int[x]
            x = x + 13
            if x > 26:
                x = x - 26
            x = int_alp[x]
            if cap:
                x = x.upper()
        output_text = output_text + x
    return output_text


def valid_username(username):
    return USER_RE.match(username)


def valid_password(password):
    return PASS_RE.match(password)


def valid_email(email):
    return EMAIL_RE.match(email)


def check_details(username, password, verify, email):
    user_error, password_error, verify_error, email_error = ("", "", "", "")
    valid_details = True

    if valid_username(username) is None:
        user_error = "That's not a valid username."
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

    return valid_details, username, password, verify, email, user_error, password_error, verify_error, email_error




app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/fizzbuzz', FizzBuzzHandler),
    ('/rot13', RotHandler),
    ('/signup', SignHandler),
    ('/welcome', WelcomeHandler),
], debug=True)
