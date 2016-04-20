import json
from datetime import datetime

from flask_admin import Admin
from flask.ext import login
from flask_admin.contrib.sqla import ModelView
from flask_admin.model import typefmt
from jinja2 import Markup
from flask import abort

from statistic.server.models import ChannelStatistic, User
from statistic.server.models import db

import logging

logger = logging.getLogger(__name__)


class AdminAccessMixin(object):
    def is_accessible(self):
        user = login.current_user
        return user.is_authenticated and user.is_admin


def datetime_formatter(view, value):
    return value.strftime('%Y-%m-%d %H:%M')


# formatters
def bool_formatter(view, value):
    return Markup('<input type="checkbox" disabled %s>' % ('checked' if value else ''))


class BaseModelMixin(object):
    column_default_sort = 'created_on', True
    can_delete = False
    page_size = 60

    column_type_formatters = dict(typefmt.BASE_FORMATTERS)
    column_type_formatters.update({
        datetime: datetime_formatter,
        bool: bool_formatter,
        dict: lambda view, value: json.dumps(value, ensure_ascii=False),
        list: lambda view, value: json.dumps(value, ensure_ascii=False),
    })

    def inaccessible_callback(self, name, **kwargs):
        if not self.is_accessible():
            abort(403)

    def on_model_change(self, form, model, is_created):
        info = 'user {user} try to update model {model}, new value are {value}'.format(user=login.current_user.id,
                                                                                       model=model.__class__,
                                                                                       value=vars(model))
        logger.info(info)

    def on_model_delete(self, model):
        info = 'user {user} try to delete model {model}, old value are {value}'.format(user=login.current_user.id,
                                                                                       model=model.__class__,
                                                                                       value=vars(model))
        logger.info(info)


class ChannelStatisticView(AdminAccessMixin, BaseModelMixin, ModelView):
    can_delete = False
    can_edit = False
    can_create = True

    column_default_sort = 'date', True
    column_searchable_list = ('channel_name', )

    column_list = ('id', 'channel_name', 'date', 'registered_num', 'factor',)
    column_filters = ('date', 'channel_name', 'registered_num', 'factor')
    column_labels = {
        'registered_num': '注册数量',
        'date': '日期',
        'factor': '调整系数',
        'created_on': '创建时间',
        'updated_on': '修改时间',
        'channel_name': '渠道名称',
    }

    column_editable_list = ('factor',)


class UsersView(AdminAccessMixin, BaseModelMixin, ModelView):
    can_delete = False
    can_edit = True
    can_create = True

    column_default_sort = 'updated_on', True
    column_searchable_list = ('email', 'channel_name')

    column_list = ('id', 'email', 'channel_name', 'show_date_begin_limit', 'show_date_end_limit', 'is_admin', 'created_on', 'updated_on')
    column_filters = ('email', 'channel_name', 'is_admin', 'show_date_begin_limit', 'show_date_end_limit')
    column_labels = {
        'email': '邮箱',
        'channel_name': '渠道名称',
        'show_date_begin_limit': '开放起始时间',
        'show_date_end_limit': '开放结束时间',
        'created_on': '创建时间',
        'updated_on': '修改时间',
        'is_admin': '是否为管理员',
    }

    column_choices = {
        'is_admin': [
            (True, '是'),
            (False, '否'),
        ],
    }


def init_admin_page(app):
    admin = Admin(app, name='admin', endpoint='admin', template_mode='bootstrap3',)
    admin.add_view(UsersView(User, db.session, name='用户管理', endpoint='adminuser'))
    admin.add_view(ChannelStatisticView(ChannelStatistic, db.session, name='渠道激活统计',))
