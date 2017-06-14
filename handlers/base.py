import jinja2
import webapp2

import models
from helpers import make_secure_val, check_secure_val
from main import template_dir


jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    # modified to always pass user and liked posts/comments to render
    def render(self, template, **kw):
        self.write(self.render_str(template, user=self.user,
                                   liked_posts=self.liked_posts,
                                   liked_comments=self.liked_comments,
                                   **kw))

    def set_secure_cookie(self, name, val):
        secure_val = make_secure_val(val)
        self.response.headers.add_header('Set-Cookie',
                                         '%s=%s; Path=/' % (name, secure_val))

    def remove_cookie(self, name):
        self.response.headers.add_header('Set-Cookie',
                                         '%s=; Path=/' % name)

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie("user_id", user)

    def logout(self):
        self.remove_cookie("user_id")

    def get_liked_posts(self):
        liked_posts = (models.BlogLikes.all().filter("user =", self.user).
                       fetch(100))
        i = []
        for post in liked_posts:
            i.append(post.blogpost.key().id())
        return i

    def get_liked_comments(self):
        liked_comments = (models.CommentLikes.all().
                          filter("user =", self.user).fetch(100))
        i = []
        for comment in liked_comments:
            i.append(comment.comment.key().id())
        return i

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie("user_id")
        if uid:
            self.user = uid and models.User.get_by_id(int(uid))
            self.liked_posts = self.get_liked_posts()
            self.liked_comments = self.get_liked_comments()
        else:
            self.user = None
            self.liked_posts = None
            self.liked_comments = None
