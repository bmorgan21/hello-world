# coding: utf-8

import logging

from flask import Blueprint, render_template

logger = logging.getLogger(__name__)

bp = Blueprint('home', __name__)


@bp.route('/')
def index():
    return render_template('home/index.html')
