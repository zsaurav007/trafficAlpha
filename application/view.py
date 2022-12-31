from flask import Blueprint, render_template, flash, request, url_for, jsonify, redirect, session
from flask_login import login_required, current_user
from .dal import *
from .viewmodel import *
from werkzeug.utils import secure_filename
from . import UPLOAD_FOLDER, fernet
import os



view = Blueprint('view', __name__)


ALLOWED_EXTENSIONS = {'mp4'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@view.route('/')
@login_required
def home():
    #load areas
    #
    return render_template("home.html", current_user=current_user)


@view.route('/settings', methods=['GET'])
@login_required
def settings():
    area_models = get_all_areas()
    areas = format_area_list(area_models)
    tab = session.get('tab')
    if not tab:
        tab = 3
    rtsp_models = format_media_list(get_all_media_by_type(StreamType.rtsp))
    video_models = format_media_list(get_all_media_by_type(StreamType.video))

    return render_template("settings.html", tab=tab, areas=areas, rtsp_models=rtsp_models, video_models=video_models)


@view.route('/list-cameras')
@login_required
def list_cameras():
    area_id = request.args.get('area_id')
    print(area_id)
    area_id = fernet.decrypt(area_id).decode()
    area_id = int(area_id)
    if area_id:
        medias = get_media_by_area(area_id)
        medias = format_media_list(medias)
        return jsonify({
            'data': medias,
            'success': True
        })
    return jsonify({
        'success': False
    })

@view.route('/settings-create-area', methods=['POST'])
@login_required
def settings_create_area():
    if request.method == 'POST':
        name = request.form['area_name'].strip()
        description = request.form['des'].strip()
        lat = request.form['area_lat'].strip()
        lng = request.form['area_long'].strip()

        error = False
        if len(name) == 0:
            flash("Empty name!", category='error')
            error = True
        if len(description) == 0:
            description = name

        if not error:
            if not add_area(name, description, lat, lng):
                flash("Cannot add area, already exists or area not found!", category='error')
            else:
                flash("Area added successfully!", category='success')
    session['tab'] = 3
    return redirect(url_for('view.settings'))


@view.route('/settings-create-rtsp-link', methods=['POST'])
@login_required
def settings_create_rtsp_link():
    session['tab'] = 1
    if request.method == 'POST':
        rtsp_link = request.form['rtsp_link'].strip()
        rtsp_link_name = request.form['rtsp_name'].strip()
        area_id = request.form['area_id']
        area_id = fernet.decrypt(area_id).decode()
        area_id = int(area_id)
        lat = request.form['rtsp_lat'].strip()
        lng = request.form['rtsp_long'].strip()
        error = False
        if len(lat) == 0:
            flash("Forgot to select camera location?", category="error")
            error = True
        if not rtsp_link.lower().startswith("rtsp://"):
            flash("Invalid RTSP Link!", category='error')
            error = True
        if len(rtsp_link_name) == 0:
            flash("Empty RTSP name!", category='error')
            error = True

        if not error:
            if not add_media(rtsp_link_name, rtsp_link, StreamType.rtsp, area_id, lat, lng):
                flash("Cannot add rtsp link, already exists or area not found!", category='error')
            else:
                flash("RTSP Link added successfully!", category='success')
    return redirect(url_for('view.settings'))


@view.route('/settings-upload-video', methods=['POST'])
@login_required
def settings_upload_video():
    session['tab'] = 2
    if request.method == 'POST':
        error = False
        if 'file' not in request.files:
            flash('No file is added.', category="error")
            error = True
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', category="error")
            error = True
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filePath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filePath)
        video_name = request.form['video_name'].strip()
        area_id = request.form['area_id']
        area_id = fernet.decrypt(area_id).decode()
        area_id = int(area_id)
        lat = request.form['video_lat'].strip()
        lng = request.form['video_long'].strip()
        if len(lat) == 0:
            flash("Forgot to select video location?", category="error")
            error = True
        if len(video_name) == 0:
            flash("Empty Video name!", category='error')
            error = True

        if not error:
            if not add_media(video_name, filePath, StreamType.video, area_id, lat, lng):
                flash("Cannot add rtsp link, already exists or area not found!", category='error')
            else:
                flash("Video uploaded successfully!", category='success')
    return redirect(url_for('view.settings'))


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
