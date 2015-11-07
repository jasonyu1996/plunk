#!/usr/bin/python3

import os.path;
import tornado.httpserver;
import tornado.ioloop;
import tornado.options;
import tornado.web;
import tornado.wsgi;

from tornado.options import define, options;

from sqlalchemy import create_engine;
from sqlalchemy.orm import sessionmaker, scoped_session;

import handlers;
import modules;
import config;

define('port', default=8000, help='run on the given port', type=int);
#define('db_host', default='localhost', help='the database host', type=str);
#define('db_port', default=3306, help='the database port', type=int);

class PlunkApplication(tornado.wsgi.WSGIApplication):
    def __init__(self, db_host, db_port, db_name, db_user, db_pwd, data_dir, **param):
        handler_list = [
                ('/', handlers.HomeHandler),
                ('/post/(\w+)', handlers.PostViewHandler),
                ('/post/s/(\w+)', handlers.PostViewByNameHandler),
                ('/login/', handlers.LoginHandler),
                ('/logout/', handlers.LogoutHandler),
                ('/archive/', handlers.ArchiveHandler),
                ('/archive/page/(\w+)', handlers.ArchivePagerHandler),
                ('/page/(\w+)', handlers.HomePagerHandler),
                ('/master/', handlers.MasterHomeHandler),
                ('/master/edit/(\w*)', handlers.PostEditHandler),
                ('/master/delete/(\w+)', handlers.PostDeleteHandler),
                ('/master/settings/', handlers.SettingsHandler),
                ('/master/hidden/', handlers.HiddenListHandler),
                ('/master/hidden/page/(\w+)', handlers.HiddenListPagerHandler),
                ('/i/comment/', handlers.CommentHandler)
                ];
        ui_modules = {
                'PostList': modules.PostListModule,
                'Pager': modules.PagerModule,
                'Time': modules.TimeModule
                };

        tornado.web.Application.__init__(self, handlers = handler_list, ui_modules = ui_modules, **param);
        self.__engine = create_engine('mysql+mysqlconnector://%s:%s@%s:%d/%s' % (db_user, db_pwd, db_host, db_port, db_name), pool_size = 20, pool_recycle = 18000);
        self.db_session = scoped_session(sessionmaker(bind = self.__engine));
        self.cookie_expire_secs = 1800;

        self.data_dir = data_dir;

    def load_config(self):
        return config.load_config(os.path.join(self.data_dir, 'config.cnf'));

    def dump_config(self, conf):
        config.dump_config(conf, os.path.join(self.data_dir, 'config.cnf'));

app_settings = {
        'cookie_secret': '8NyFhHwZQGawg8vw0tHq76J7hhcs80tuosycaRQO5hw=',
        'template_path': os.path.join(os.path.dirname(__file__), 'templates/'),
#        'xsrf_cookies': True,
        'static_path': os.path.join(os.path.dirname(__file__), 'static/'),
        'login_url': '/login/'
        };

