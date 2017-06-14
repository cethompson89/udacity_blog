import models
from handlers.base import Handler
from helpers import check_details
from decorators import login_required

# **************   Individual page handlers   *********************


class UserListHandler(Handler):
    # used to check users in app
    @login_required
    def get(self):
        users = models.User.all().order("-created")
        self.render("userlist.html", users=users)


class MainPageHandler(Handler):
    # homepage
    def get(self):
        blogposts = models.BlogPost.all().filter("deleted =", False)
        blogposts.order("-created")
        self.render("blogposts.html", blogposts=blogposts)


class PermalinkHandler(Handler):
    # page for specific blogpost
    def get(self, blog_id):
        blogpost = models.BlogPost.get_by_id(int(blog_id))
        if blogpost:
            blog_comments = blogpost.get_comments()
            self.render("blogposts.html", blogposts=[blogpost],
                        blog_comments=blog_comments, single=True,
                        blog_id=blog_id)
        else:
            self.redirect("/")

    def post(self, blog_id):  # post comment
        comment = self.request.get("comment")
        blog_id = self.request.get("blog_id")
        blogpost = models.BlogPost.get_by_id(int(blog_id))
        comment_error = ""

        if comment and self.user:
            a = models.Comment(blogpost=blogpost, user=self.user,
                               comment=comment, likes=0)
            a.put()
            self.redirect("/%s" % blog_id)
        else:
            blog_comments = blogpost.get_comments()
            if not comment:
                comment_error = "Yo, Robobuddy - you gotta add some text"
            if not self.user:
                comment_error = ("Yo Robobuddy - log in so we know you're " +
                                 "not a treacherous human")
            self.render("blogposts.html", blogposts=[blogpost],
                        blog_comments=blog_comments, single=True,
                        blog_id=blog_id, comment=comment,
                        comment_error=comment_error)


class NewPostHandler(Handler):
    @login_required
    def get(self):
        blog_id = self.request.GET.get('blog_id')  # if editting post
        subject = ""
        content = ""

        if blog_id:  # editing post
            a = models.BlogPost.get_by_id(int(blog_id))
            # check users match
            if a and a.user.key().id() == self.user.key().id():
                subject = a.subject
                content = a.blog
            else:
                blog_id = ""
        else:
            blog_id = ""

        self.render("newpost.html", subject=subject, content=content,
                    blog_id=blog_id)

    @login_required
    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")
        blog_id = self.request.get("blog_id")
        subject_error = ""
        content_error = ""

        if self.request.get("delete"):  # check for delete
            if blog_id:
                a = models.BlogPost.get_by_id(int(blog_id))
                # check users match
                if a and a.user.key().id() == self.user.key().id():
                    a.deleted = True
                    a.put()
            self.redirect("/")
        else:
            if subject and content:
                if blog_id:  # editing post
                    a = models.BlogPost.get_by_id(int(blog_id))
                    # check users match
                    if a and a.user.key().id() == self.user.key().id():
                        (a.subject, a.blog) = (subject, content)
                else:
                    a = models.BlogPost(subject=subject, blog=content,
                                        user=self.user, likes=0)
                a.put()
                i = a.key().id()
                self.redirect("/%d" % i)

            else:
                if not subject:
                    subject_error = "Please add a subject"
                if not content:
                    content_error = "Please add a blog post"
                self.render("newpost.html", subject=subject, content=content,
                            subject_error=subject_error,
                            content_error=content_error)


class CommentHandler(Handler):
    @login_required
    def get(self):
        comment_id = self.request.GET.get("comment_id")
        a = models.Comment.get_by_id(int(comment_id))
        # check users match
        if a and a.user.key().id() == self.user.key().id():
            content = a.comment
            self.render("comment.html", comment_id=comment_id, content=content)
        else:
            self.redirect("/")

    @login_required
    def post(self):
        comment_id = self.request.get("comment_id")
        content = self.request.get("content")
        content_error = ""

        a = models.Comment.get_by_id(int(comment_id))
        # check users match
        if a and a.user.key().id() == self.user.key().id():
            i = a.blogpost.key().id()
            if self.request.get("delete"):  # check for delete
                a.deleted = True
                a.put()
                self.redirect("/%d" % i)
            elif content:
                a.comment = content
                a.put()
                self.redirect("/%d" % i)
            else:
                content_error = "Please add content"
                self.render("comment.html", commend_id=comment_id,
                            content=content, content_error=content_error)
        else:
            self.redirect("/")


class LikeHandler(Handler):
    # if post is liked add like to datastore and redirect
    @login_required
    def get(self):
        blog_id = self.request.GET.get('blog_id')
        comment_id = self.request.GET.get('comment_id')
        unlike = self.request.GET.get('unlike')

        if blog_id:
            blogpost = models.BlogPost.get_by_id(int(blog_id))
            if blogpost:  # check it exists
                if unlike:
                    blogpost.unlike_post(self.user)
                else:
                    blogpost.like_post(self.user)
            self.redirect("/%s" % blog_id)
        elif comment_id:
            comment = models.Comment.get_by_id(int(comment_id))
            if comment:
                blog_id = comment.blogpost.key().id()
                if unlike:
                    comment.unlike_comment(self.user)
                else:
                    comment.like_comment(self.user)
                self.redirect("/%s" % blog_id)
            else:
                self.redirect("/")
        else:
            self.redirect("/")


class SignHandler(Handler):
    def get(self):
        self.render("signup.html", username="", password="", verify="",
                    email="")

    def post(self):
        username = self.request.get("username")
        password = self.request.get("password")
        verify = self.request.get("verify")
        email = self.request.get("email")

        (redirect, username, password, verify,
         email, user_error, password_error,
         verify_error, email_error) = check_details(username, password,
                                                    verify, email)

        if redirect:
            i = models.User.create_user(username=username, password=password,
                                        email=email)
            self.login(i)
            self.redirect("/welcome")
        else:
            self.render("signup.html", username=username, password=password,
                        verify=verify, email=email, user_error=user_error,
                        password_error=password_error,
                        verify_error=verify_error, email_error=email_error)


class LoginHandler(Handler):
    def get(self):
        redirect_msg = self.request.GET.get('redirect')
        self.render("login.html", username="", password="", login_error="",
                    redirect_msg=redirect_msg)

    def post(self):
        username = self.request.get("username")
        password = self.request.get("password")

        i = models.User.validate_user(username, password)
        if i:
            self.login(i)
            self.redirect("/welcome")
        else:
            login_error = "That is not a valid user/password"
            self.render("login.html", username=username,
                        password=password, login_error=login_error)


class LogoutHandler(Handler):
    def get(self):
        self.logout()
        self.redirect("/login")


class WelcomeHandler(Handler):
    @login_required
    def get(self):
        self.render("welcome.html", username=self.user.username)
