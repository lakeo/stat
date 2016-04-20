# stat/server/__init__.py


#################
#### imports ####
#################

import os

from flask import Flask, render_template
from flask.ext.login import LoginManager
from flask_bootstrap import Bootstrap

import logging.config
import statistic.server.config as config
from statistic.server.models import init_model
################
#### config ####
################

app = Flask(
    __name__,
    template_folder='../client/templates',
    static_folder='../client/static'
)

logging.config.dictConfig(config.LOGGING_CONFIG)

if 'APP_SETTINGS' in os.environ:
    app_settings = os.environ['APP_SETTINGS']
else:
    app_settings = 'statistic.server.config.DevelopmentConfig'

app.config.from_object(app_settings)


####################
#### extensions ####
####################

login_manager = LoginManager()
login_manager.init_app(app)
bootstrap = Bootstrap(app)
init_model(app)

###################
### blueprints ####
###################

from statistic.server.user.views import user_blueprint
from statistic.server.main.views import main_blueprint
from statistic.server.admin.views import init_admin_page

app.register_blueprint(user_blueprint)
app.register_blueprint(main_blueprint)
init_admin_page(app)

###################
### flask-login ####
###################

from statistic.server.models import User

login_manager.login_view = "user.login"
login_manager.login_message_category = 'danger'


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.id == int(user_id)).first()


########################
#### error handlers ####
########################

@app.errorhandler(403)
def forbidden_page(error):
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def page_not_found(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error_page(error):
    return render_template("errors/500.html"), 500

if __name__ == '__main__':
    from flask.ext.debugtoolbar import DebugToolbarExtension
    toolbar = DebugToolbarExtension(app)
    app.run(host='0.0.0.0', port=5000, debug=True)
