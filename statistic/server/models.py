# stat/server/models.py


import datetime

from . import util

from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, \
    check_password_hash

db = SQLAlchemy()


def init_model(app):
    db.init_app(app)


class CommonColumnMixin(object):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_on = db.Column(db.DateTime(timezone=True), nullable=False, default=util.now())
    updated_on = db.Column(db.DateTime(timezone=True), nullable=False, default=util.now())


class CRUDMixin(object):
    USE_CACHE = False

    # basic CRUD

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        db.session.add(obj)
        db.session.flush([obj])

        missing = object()
        use_master = db.session.info.get('use_master', missing)
        db.session.info.update(use_master=True)
        db.session.refresh(obj)
        if use_master is not missing:
            db.session.info.update(use_master=use_master)
        else:
            del db.session.info['use_master']

        return obj

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if not getattr(self, k, None) == v:
                setattr(self, k, v)
        return self

    def delete(self):
        db.session.delete(self)
        db.session.flush([self])
        return self

    # misc
    def save(self):
        db.session.add(self)
        db.session.flush([self])
        return self

    def inc(self, field, n=1):
        value = getattr(self, field)
        setattr(self, field, value + n)
        return self

    def dec(self, field, n=1):
        value = getattr(self, field)
        setattr(self, field, value - n)
        return self

    @property
    def cache_key(self):
        return '%s:%s' % (type(self).__name__.lower(), self.id)

    @classmethod
    def get_one(cls, **kwargs):
        return cls.query.filter_by(**kwargs).first()

    @classmethod
    def exists(cls, **kwargs):
        return bool(cls.query.filter_by(**kwargs).first())

    @classmethod
    def get_or_create(cls, defaults=None, **kwargs):
        defaults = defaults or {}

        obj, created = cls.query.filter_by(**kwargs).set_use_master().first(), False
        if obj is None:
            obj, created = cls(**kwargs), True

            obj.update(**defaults).save()

        return obj, created

    @classmethod
    def update_or_create(cls, defaults=None, **kwargs):
        defaults = defaults or {}

        obj, created = cls.query.filter_by(**kwargs).set_use_master().first(), False
        if obj is None:
            obj, created = cls(**kwargs), True

        obj.update(**defaults).save()

        return obj, created

    @classmethod
    def list(cls, order_by, num, dir='desc', cursor=None, limit=None):
        raise NotImplementedError()


class Base(CommonColumnMixin, CRUDMixin, db.Model):
    __abstract__ = True

    def __repr__(self):
        return '<%s(id=%s)>' % (self.__class__.__name__, self.id)


class User(Base):

    __tablename__ = "users"

    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    channel_name = db.Column(db.String, nullable=True)
    show_date_begin_limit = db.Column(db.Date, nullable=False, default=datetime.datetime.utcnow().date())
    show_date_end_limit = db.Column(db.Date, nullable=False, default=datetime.datetime.utcnow().date())

    def __init__(self, email, password, is_admin=False):
        self.email = email
        self.password = generate_password_hash(password)
        self.is_admin = is_admin

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def __repr__(self):
        return '<User {0}>'.format(self.email)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class ChannelStatistic(Base):

    __tablename__ = 'channel_statistic'

    __table_args__ = (
        db.UniqueConstraint('date', 'channel_name'),
    )

    channel_name = db.Column(db.String, nullable=False)
    factor = db.Column(db.Float, nullable=False, default=1.)
    registered_num = db.Column(db.Integer, nullable=False, default=0)
    date = db.Column(db.Date, nullable=False, default=datetime.datetime.utcnow().date())
