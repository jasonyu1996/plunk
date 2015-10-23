import hashlib;
import time;
import collections;
import datetime;
import pytz;
import json;

from sqlalchemy import and_;

import tornado.web;
import tornado.escape;
import markdown2;
import models;
import abstract;
import modules;

FullPost = collections.namedtuple('FullPost', 'id title contents_html author_name time');
DetailedPost = collections.namedtuple('DetailedPost', 'id title abstract_html author_name time');
BriefPost = collections.namedtuple('BriefPost', 'id title author_name time');
EditablePost = collections.namedtuple('EditablePost', 'id title id_name visibility_mode contents time');

def get_full_post_query(session):
        return session.query(models.Post.id, models.Post.title, \
                models.Post.contents_html, models.User.name, models.Post.time);

def get_detailed_post_query(session):
        return session.query(models.Post.id, models.Post.title, \
                models.Post.abstract_html, models.User.name, models.Post.time);
    
def get_brief_post_query(session):
        return session.query(models.Post.id, models.Post.title, \
                models.User.name, models.Post.time);

def get_brief_post_list(session, offset, limit):
    return [BriefPost(*entry) \
            for entry \
            in get_brief_post_query(session).\
            filter(and_(models.Post.visibility_mode == 0, models.User.id == models.Post.author_id)).\
            order_by(models.Post.time.desc()).offset(offset).limit(limit)];

def get_brief_hidden_post_list(session, offset, limit):
    return [BriefPost(*entry) \
            for entry \
            in get_brief_post_query(session).\
            filter(and_(models.Post.visibility_mode != 0, models.User.id == models.Post.author_id)).\
            order_by(models.Post.time.desc()).offset(offset).limit(limit)];

def get_detailed_post_list(session, offset, limit):
    return [DetailedPost(*entry) \
            for entry \
            in get_detailed_post_query(session).\
            filter(and_(models.Post.visibility_mode == 0, models.User.id == models.Post.author_id)).\
            order_by(models.Post.time.desc()).offset(offset).limit(limit)];

class BaseHandler(tornado.web.RequestHandler):
    def get_app_config(self):
        if not hasattr(self, '__conf'):
            self.__conf = self.application.load_config();
        return self.__conf;
    def on_finish(self):
        self.application.db_session.remove();
    def get_current_user(self):
        try:
            user_id = int(self.get_secure_cookie('user_id'));
            self.set_secure_cookie('user_id', str(user_id), expires = time.time() + self.application.cookie_expire_secs);
            return self.application.db_session.query(models.User.id, models.User.name).filter(models.User.id == user_id).one();
        except:
            return None;
    def render(self, path, **param):
        tornado.web.RequestHandler.render(self, path,
                conf = self.get_app_config(), **param);

class PostViewHandler(BaseHandler):
    def get(self, id):
        try:
            id = int(id);
            if self.current_user is None: # not authenticated
                post = FullPost(*get_full_post_query(self.application.db_session).filter(and_(models.Post.id == id, models.Post.visibility_mode != 2)).one()); # cannot view it
            else:
                post = FullPost(*get_full_post_query(self.application.db_session).filter(models.Post.id == id).one());
        except:
            self.send_error(404);
            return;
        self.render('postview.html', post = post);


class PostViewByNameHandler(BaseHandler):
    def get(self, id_name):
        try:
            if self.current_user is None: # not authenticated
                post = FullPost(*get_full_post_query(self.application.db_session).filter(and_(models.Post.id_name == id_name, models.Post.visibility_mode != 2)).one()); # cannot view it
            else:
                post = FullPost(*get_full_post_query(self.application.db_session).filter(models.Post.id_name == id_name).one());
        except:
            self.send_error(404);
            return;
        self.render('postview.html', post = post);

class LoginHandler(BaseHandler):
    def get(self):
        self.render('login.html', next_url = self.get_argument('next', '/'));
    def post(self):
        user_name = self.get_argument('username', None);
        password = self.get_argument('password', None);
        if user_name is None or password is None:
            self.send_error(404);
        else:
            try:
                user = self.application.db_session.query(models.User).filter(models.User.name == user_name).one();
            except:
                self.send_error(404);
            try:
                if hashlib.md5(password.encode('utf-8')).hexdigest() == user.password_md5:
                    self.set_secure_cookie('user_id', str(user.id), expires = time.time() + self.application.cookie_expire_secs);
                else:
                    self.send_error(404);
                    return;
            except:
                return;
            self.redirect(self.get_argument('next', '/'));

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('user_id');
        self.redirect('/');

def is_last_visible_post(pid, session):
    try:
        last_pid = session.query(models.Post.id).filter(models.Post.visibility_mode == 0).order_by(models.Post.time).limit(1).one().id;
    except:
        return True;
    return pid == last_pid;

def is_last_invisible_post(pid, session):
    try:
        last_pid = session.query(models.Post.id).filter(models.Post.visibility_mode != 0).order_by(models.Post.time).limit(1).one().id;
    except:
        return True;
    return pid == last_pid;

class ArchiveHandler(BaseHandler):
    def get(self):
        posts = get_brief_post_list(self.application.db_session, \
                0, self.get_app_config()['brief_post_no_per_page']);
        self.render('archive.html', posts = posts, page_number = 1, \
                is_last = len(posts) == 0 or is_last_visible_post(posts[-1].id, self.application.db_session));

class ArchivePagerHandler(BaseHandler):
    def get(self, page_number):
        try:
            page_number = int(page_number);
        except:
            self.send_error(404);
            return;
        if page_number <= 0:
            self.send_error(404);
            return;
        posts = get_brief_post_list(self.application.db_session, \
                (page_number - 1) * self.get_app_config()['brief_post_no_per_page']);
        self.render('archive.html', posts = posts, \
                page_number = page_number,\
                is_last = len(posts) == 0 or is_last_visible_post(posts[-1].id, self.application.db_session));

class HomeHandler(BaseHandler):
    def get(self):
 #       posts = self.application.db_session.query(models.Post).order_by(models.Post.time.desc()).limit(self.get_app_config()['detailed_post_no_per_page']).all();
#        self.render('home.html', posts = posts, page_number = 1);
        try:
            posts = get_detailed_post_list(self.application.db_session, \
                     0, self.get_app_config()['detailed_post_no_per_page']);
            self.render('home.html', posts = posts, page_number = 1, \
                    is_last = len(posts) == 0 or is_last_visible_post(posts[-1].id, self.application.db_session));
        except Exception as e:
            self.write(str(e));

class HomePagerHandler(BaseHandler):
    def get(self, page_number):
        try:
            page_number = int(page_number);
        except:
            self.send_error(404);
            return;
        if page_number <= 0:
            self.send_error(404);
            return;
#        p = self.application.db_session.query(models.Post.id, models.User.name).filter(models.Post.author_id == models.User.id).first();
#        print(p);
#        posts = self.application.db_session.query(models.Post).order_by(models.Post.time.desc()).offset((page_number - 1) * self.get_app_config()['detailed_post_no_per_page']).limit(self.get_app_config()['detailed_post_no_per_page']).all();
        posts = get_detailed_post_list(self.application.db_session, \
            (page_number - 1) * self.get_app_config()['detailed_post_no_per_page'], \
            self.get_app_config()['detailed_post_no_per_page']);
        self.render('home.html', posts = posts, page_number = page_number, \
                 is_last = len(posts) == 0 or is_last_visible_post(posts[-1].id, self.application.db_session));

class PostEditHandler(BaseHandler):
    def __get_time(self):
        time_type = self.get_argument('timetype', '');
        if time_type == 'custo':
            return time.strptime(self.get_argument('time', ''), '%Y-%m-%d %H:%M:%S');
        elif time_type == 'old':
            return None;
        else:
            return datetime.datetime.now(pytz.timezone(self.get_app_config()['timezone']));

    def __get_visibility_mode(self): # get the visibility mode from the argument
        s = self.get_argument('vismode', '');
        if s == 'visible':
            return 0;
        elif s == 'hidden':
            return 1;
        else:
            return 2;

    @tornado.web.authenticated
    def __get_settings(self):
        time = self.__get_time();
        settings = {
                'title': self.get_argument('title', ''),
                'contents': self.get_argument('contents', ''),
                'author_id': self.current_user.id,
                'visibility_mode': self.__get_visibility_mode()
                };
        if time is not None:
            settings['time'] = time;
        id_name = self.get_argument('idname', '');
        if id_name is not None and id_name != '':
            settings['id_name'] = id_name;
        settings['contents_html'] = str(markdown2.markdown(settings['contents']));
        settings['abstract_html'] = abstract.gen_html_abstract(settings['contents_html'], 300);
        return settings;

    @tornado.web.authenticated
    def get(self, post_id):
        if post_id == '': #add new post
            self.render('postedit.html', post = None);
        else:
            try:
                post_id = int(post_id);
                post = EditablePost(*self.application.db_session.query(models.Post.id, models.Post.title, models.Post.id_name, \
                        models.Post.visibility_mode, models.Post.contents, models.Post.time).filter(models.Post.id == post_id).one());
            except:
                self.send_error(404);
                return;
            self.render('postedit.html', post = post);

    @tornado.web.authenticated
    def post(self, post_id):
        if post_id == '': #add new post
            try:
                post = models.Post(**self.__get_settings());
            except Exception as e:
                self.write(str(e));
                return;
            self.application.db_session.add(post);
            self.application.db_session.commit();
#            print(title);
#            print(contents);
#            print(contents_html);

#            post = models.Post(title = title, contents = contents, contents_html = contents_html, author_id = self.current_user.id, time = datetime.datetime.now());
#            self.application.db_session.add(post);
#            self.application.db_session.commit();
            self.redirect('/');
        else: #update old post
            try:
                pid = int(post_id);
                post = self.application.db_session.query(models.Post).filter(models.Post.id == pid).one();
            except:
                self.send_error(404);# pid error
                return;
            for attr, val in self.__get_settings().items():
                setattr(post, attr, val);
            self.application.db_session.add(post);
            self.application.db_session.commit();
            self.redirect('/');

class MasterHomeHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('master.html');

class PostDeleteHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, post_id):
        try:
            post_id = int(post_id);  
            post = BriefPost(*get_brief_post_query(self.application.db_session).filter(models.Post.id == post_id).one());
        except:
            self.send_error(404);
            return;
        self.render('postdelete.html', post = post, status = 0);

    @tornado.web.authenticated
    def post(self, post_id):
        try:
            post_id = int(post_id);
            post = BriefPost(*get_brief_post_query(self.application.db_session).filter(models.Post.id == post_id).one());
        except:
            self.send_error(404);
            return;
        if post.title == self.get_argument('title', ''):
            self.application.db_session.query(models.Post).filter(models.Post.id == post_id).delete();
            self.application.db_session.commit();
            self.render('postdelete.html', post = post, status = 1);
        else:
            self.render('postdelete.html', post = post, status = -1);

# settings page
class SettingsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('settings.html', nav_list_json = \
                json.dumps(self.get_app_config()['nav_bar_items']));

    @tornado.web.authenticated
    def post(self):
        conf = self.get_argument('conf', '');
        if conf == '':
            self.write('Failed!');
        else:
            try:
                self.application.dump_config(json.loads(conf));
            except:
                self.write('Failed!');
                return;
            self.write('Succeeded!');
#        conf = self.get_app_config();
#        conf['blog_name'] = self.get_argument('blogname', '');
#        conf['blog_subname'] = self.get_argument('blogsubname', '');
#        conf['timezone'] = self.get_argument('timezone', '')
#        self.application.dump_config(conf);
#        self.redirect('/master/');

# comment
class CommentHandler(BaseHandler):
    def get(self):
        try:
            pid = int(self.get_argument('pid', ''));
            cid = int(self.get_argument('cid', ''));
        except:
            self.send_error(400);
            return;
        if cid == -1:
            cdata = self.application.db_session.query(models.Comment.id, models.Comment.contents, models.Comment.time, models.Comment.poster_name, models.Comment.poster_email).filter(models.Comment.post_id == pid).order_by(models.Comment.time).all();
        else:
            cdata = self.application.db_session.query(models.Comment.id, models.Comment.contents, models.Comment.time, models.Comment.poster_name, models.Comment.poster_email).filter(models.Comment.parent_id == cid).order_by(models.Comment.time).all();
        cdata_json = [
                {
                    'id': str(c.id),
                    'time': modules.time_to_string(c.time),
                    'poster_name': c.poster_name,
                    'poster_email': c.poster_email,
                    'contents': c.contents
                    } for c in cdata
                ];
        self.write(json.dumps(cdata_json));
    
    def add_comment(self):
        try:
            pid = int(self.get_argument('pid', ''));
            cid = int(self.get_argument('cid', ''));
            cdata = json.loads(self.get_argument('post', ''));
            cdata['poster_name'] = tornado.escape.xhtml_escape(cdata['poster_name']);
            cdata['poster_email'] = tornado.escape.xhtml_escape(cdata['poster_email']);
            cdata['contents'] = markdown2.markdown(cdata['contents'], safe_mode = 'escape');
            if cid == -1:
                co = models.Comment(post_id = pid, poster_name = cdata['poster_name'], poster_email = cdata['poster_email'], time = datetime.datetime.now(pytz.timezone(self.get_app_config()['timezone'])), contents = cdata['contents']);
            else:
                co = models.Comment(parent_id = cid, poster_name = cdata['poster_name'], poster_email = cdata['poster_email'], time = datetime.datetime.now(pytz.timezone(self.get_app_config()['timezone'])), contents = cdata['contents']);
            self.application.db_session.add(co);
            self.application.db_session.commit();
        except:
            self.send_error(400);
            return;

   #     del cdata['pid'];
   #     del cdata['cid'];
        cdata['id'] = str(co.id);
        cdata['time'] = modules.time_to_string(co.time);

        self.write(json.dumps(cdata));

    def dfs_delete(self, cid):
        self.__visited_posts_seq.append(cid);
        try:
            for tid in self.application.db_session.query(models.Comment.id).filter(models.Comment.parent_id == cid).all():
                if not self.dfs_delete(tid.id):
                    return False;
        except:
            return False;
        return True;

    def delete_comment(self):
        if self.current_user is None:
            self.send_error(403); # not authenticated: forbidden
            return;
        try:
            cid = int(self.get_argument('cid', ''));
            self.__visited_posts_seq = [];
            if not self.dfs_delete(cid):
                self.send_error(500);
                return;
            for c in reversed(self.__visited_posts_seq):
                self.application.db_session.query(models.Comment).filter(models.Comment.id == c).delete();
            self.application.db_session.commit();
        except:
            self.send_error(501);
            return;
        self.write('Success');
    
    def post(self):
        op = self.get_argument('operation', 'add');
        if op == 'add':
            self.add_comment();
        elif op == 'del':
            self.delete_comment();
        else:
            self.send_error(400);

class HiddenListHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        posts = get_brief_hidden_post_list(self.application.db_session, \
                0, self.get_app_config()['brief_post_no_per_page']);
        self.render('hiddenlist.html', posts = posts, page_number = 1, \
                is_last = len(posts) == 0 or is_last_invisible_post(posts[-1].id, self.application.db_session));

class HiddenListPagerHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, page_number):
        try:
            page_number = int(page_number);
        except:
            self.send_error(404);
            return;
        if page_number <= 0:
            self.send_error(404);
            return;
        posts = get_brief_hidden_post_list(self.application.db_session, \
                (page_number - 1) * self.get_app_config()['brief_post_no_per_page']);
        self.render('hiddenlist.html', posts = posts, \
                page_number = page_number,\
                is_last = len(posts) == 0 or is_last_invisible_post(posts[-1].id, self.application.db_session));

