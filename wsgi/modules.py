import tornado.web;

def time_to_string(t):
    return t.strftime('%Y-%m-%d %H:%M:%S');

class PostListModule(tornado.web.UIModule):
    def render(self, posts, detailed = False, edit_link = False):
        if detailed:
            return self.render_string('modules/detailedpostlist.html', posts = posts, edit_link = edit_link);
        else:
            return self.render_string('modules/briefpostlist.html', posts = posts, edit_link = edit_link);

class PagerModule(tornado.web.UIModule):
    def render(self, page_url, page_number, is_last):
        return self.render_string('modules/pager.html', page_url = page_url, page_number = page_number, is_last = is_last);

class TimeModule(tornado.web.UIModule):
    def render(self, t):
        return time_to_string(t);

