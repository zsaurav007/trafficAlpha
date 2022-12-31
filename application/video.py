from flask import Blueprint, render_template
from flask_login import login_required, current_user

video = Blueprint('video', __name__)


@video.route('/video-data')
@login_required
def analytics_data():
    pass


@video.route('/video_feed', methods=['GET'])
@login_required
def video_feed():
    pass


@video.route('/start-record-clip')
def start_record_clip():
    pass


@video.route('/stop-record-clip')
def stop_record_clip():
    pass


@video.route('/is-recording')
def is_video_recoding():
    pass


@video.route('/create-clip', methods=['POST'])
def create_video():
    pass


@video.route('/check-camera', methods=['GET'])
def check_camera():
    pass
