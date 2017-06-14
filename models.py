from google.appengine.ext import db
from helpers import make_pw_hash, check_valid_pw

# **************   create google app entities   *********************


class User(db.Model):
    username = db.StringProperty(required=True)
    email = db.StringProperty(required=False)
    password = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

    @classmethod
    def create_user(cls, username, password, email=None):
        pw_hash = make_pw_hash(username, password)  # hash pw
        a = cls(username=username, password=pw_hash, email=email)
        a.put()
        return "%d" % (a.key().id())

    @classmethod
    def validate_user(cls, username, password):
        user = cls.all().filter("username =", username).get()
        if user and check_valid_pw(username, password, user.password):
            return "%d" % (user.key().id())


class BlogPost(db.Model):
    subject = db.StringProperty(required=True)
    blog = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    user = db.ReferenceProperty(User, collection_name='blog_user')
    likes = db.IntegerProperty(required=False)
    deleted = db.BooleanProperty(default=False)

    def get_comments(self):
        q = (Comment.all().filter("blogpost =", self).
             filter("deleted =", False))
        q.order("created")
        return q

    def like_post(self, user):
        if self.user.key().id() != user.key().id():
            a = (BlogLikes.all().filter("blogpost =", self).
                 filter("user =", user).get())
            if not a:  # only action is it's not there
                a = BlogLikes(blogpost=self, user=user)
                a.put()
                self.likes += 1
                self.put()

    def unlike_post(self, user):
        if self.user.key().id() != user.key().id():
            a = (BlogLikes.all().filter("blogpost =", self).
                 filter("user =", user).get())
            if a:
                a.delete()
                self.likes += -1
                self.put()


class Comment(db.Model):
    blogpost = db.ReferenceProperty(BlogPost, collection_name='blogpost')
    user = db.ReferenceProperty(User, collection_name='comment_user')
    comment = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    likes = db.IntegerProperty(required=False)
    deleted = db.BooleanProperty(default=False)

    def like_comment(self, user):
        if self.user.key().id() != user.key().id():
            a = (CommentLikes.all().filter("comment =", self).
                 filter("user =", user).get())
            if not a:  # only action is it's not there
                a = CommentLikes(comment=self, user=user)
                a.put()
                self.likes += 1
                self.put()

    def unlike_comment(self, user):
        if self.user.key().id() != user.key().id():
            a = (CommentLikes.all().filter("comment =", self).
                 filter("user =", user).get())
            if a:
                a.delete()
                self.likes += -1
                self.put()


class BlogLikes(db.Model):
    blogpost = db.ReferenceProperty(BlogPost)
    user = db.ReferenceProperty(User, collection_name='post_liked_by')


class CommentLikes(db.Model):
    comment = db.ReferenceProperty(Comment)
    user = db.ReferenceProperty(User, collection_name='comment_liked_by')
