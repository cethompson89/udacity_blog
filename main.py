import os
import webapp2

root_dir = os.path.dirname(__file__)
template_dir = os.path.join(root_dir, "templates")

import handlers.blog as blog

app = webapp2.WSGIApplication([
    ('/', blog.MainPageHandler),
    ('/newpost', blog.NewPostHandler),
    ('/(\d+)', blog.PermalinkHandler),
    ('/signup', blog.SignHandler),
    ('/welcome', blog.WelcomeHandler),
    ('/users', blog.UserListHandler),
    ('/login', blog.LoginHandler),
    ('/logout', blog.LogoutHandler),
    ('/like', blog.LikeHandler),
    ('/comment', blog.CommentHandler),
], debug=True)
