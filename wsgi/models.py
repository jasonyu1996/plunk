from sqlalchemy import Column, String, Integer, DateTime, ForeignKey;
from sqlalchemy.ext.declarative import declarative_base;
from sqlalchemy.orm import relationship, backref;

BaseModel = declarative_base();

class Comment(BaseModel):
    __tablename__ = 'comment';

    id = Column(Integer, primary_key = True, autoincrement = True);
    post_id = Column(Integer, ForeignKey('post.id'));
    parent_id = Column(Integer, ForeignKey('comment.id'));
    poster_name = Column(String(50), nullable = False);
    poster_email = Column(String(80));
    contents = Column(String, nullable = False);
    time = Column(DateTime);

class Directory(BaseModel):
    __tablename__ = 'directory';

    id = Column(Integer, primary_key = True, autoincrement = True);
    parent_id = Column(Integer, ForeignKey('directory.id'));
    name = Column(String(20), nullable = False);

    children = relationship('Directory', backref = backref('parent', remote_side = [id]));
    posts = relationship('Post', backref = 'parent');

class Tag(BaseModel):
    __tablename__ = 'tag';

    id = Column(Integer, primary_key = True, autoincrement = True);
    name = Column(String(20), nullable = False);

class User(BaseModel):
    __tablename__ = 'user';

    id = Column(Integer, primary_key = True, autoincrement = True);
    name = Column(String(50), unique = True, nullable = False);
    password_md5 = Column(String(32), nullable = False);
    access_type = Column(Integer, nullable = False);

class Post(BaseModel):
    __tablename__ = 'post';

    id = Column(Integer, primary_key = True, autoincrement = True);
    id_name = Column(String(50), unique = True);

    visibility_mode = Column(Integer, nullable = False); # the visibility mode
    # 0 - visible for all visitors 
    # 1 - links hidden
    # 2 - invisible for unauthenticated users

    author_id = Column(Integer, ForeignKey('user.id'), nullable = False);
    parent_id = Column(Integer, ForeignKey('directory.id'));
    module = Column(String(50));
    title = Column(String(80));
    contents = Column(String, nullable = False);
    contents_html = Column(String, nullable = False);
    abstract_html = Column(String, nullable = False);
    time = Column(DateTime, nullable = False);

    comments = relationship('Comment', backref = 'post');
    author = relationship('User', uselist = False);

