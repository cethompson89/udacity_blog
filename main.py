import os
import string
import re

import jinja2
import webapp2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

alphabet_int = dict(zip(string.ascii_lowercase, range(1, 27)))
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")

# create google app entitiy
class BlogPost(db.Model):
    subject = db.StringProperty(required=True)
    blog = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


class MainPageHandler(Handler):
    def get(self):
        blogposts = db.GqlQuery("SELECT * FROM BlogPost "
                                "ORDER BY created DESC ")

        self.render("blogposts.html", blogposts=blogposts)

class NewPostHandler(Handler):
    def get(self):
        self.render("newpost.html", subject="", blog="")

    def post(self):
        subject = self.request.get("subject")
        blog = self.request.get("blog")

        subject_error = ""
        blog_error = ""

        if subject and blog:
            a = BlogPost(subject=subject, blog=blog)
            a.put()
            self.redirect("/")
        else:
            if not subject:
                subject_error = "Please add a subject"
            if not blog:
                blog_error = "Please add a blog post"
            self.render("newpost.html", subject=subject, blog=blog,
                        subject_error=subject_error, blog_error=blog_error)


app = webapp2.WSGIApplication([
    ('/', MainPageHandler),
    ('/newpost', NewPostHandler),
], debug=True)
