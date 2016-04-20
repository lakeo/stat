# stat/server/tests/base.py


from flask.ext.testing import TestCase

from statistic.server.runner import app
from statistic.server.models import db
from statistic.server.models import User


class BaseTestCase(TestCase):

    def create_app(self):
        app.config.from_object('statistic.server.config.DevelopmentConfig')
        return app

