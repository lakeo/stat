# stat/server/user/views.py


#################
#### imports ####
#################

from flask import render_template, Blueprint, url_for, \
    redirect, flash, request
from flask.ext.login import login_user, logout_user, login_required

from statistic.server.user.forms import LoginForm

from statistic.server import util

import logging

logger = logging.getLogger(__name__)
################
#### config ####
################

user_blueprint = Blueprint('user', __name__, )


################
#### routes ####
################

@user_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    from statistic.server.models import User

    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            logger.info('user login: userid=%s, ip=%s' % (user.id, util.get_ip()))
            return redirect(url_for('main.home'))
        else:
            flash('Invalid email and/or password.', 'danger')
            return render_template('user/login.html', form=form)
    return render_template('user/login.html', title='Please Login', form=form)


@user_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You were logged out. Bye!', 'success')
    return redirect(url_for('user.login'))

