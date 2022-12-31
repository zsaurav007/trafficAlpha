from flask import Blueprint, render_template
from flask_login import login_required, current_user

view = Blueprint('view', __name__)


@view.route('/')
@login_required
def home():
    return render_template("home.html", current_user=current_user)


@view.route('/settings', methods=['GET'])
@login_required
def settings():
    return render_template("settings.html")


@view.route('/analytics', methods=['GET'])
@login_required
def analytics():
    return render_template("video.html", page_type="Analytics", media_name="Dummy Video", area_name="Dhaka")


@view.route('/clips', methods=['GET'])
@login_required
def clips():
    return render_template("video.html", page_type="Recorded Clips", media_name="Dummy Clip", area_name="Dhaka")


@view.route('/live', methods=['GET'])
@login_required
def video():
    return render_template("video.html", page_type="Live", media_name="Dummy Live", area_name="Dhaka")
