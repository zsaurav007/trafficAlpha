from flask import Blueprint, render_template, request, flash, \
    redirect, url_for, Response, request, session, jsonify, current_app
from flask_login import login_required, current_user
import cv2
import os
import time
import sys
import numpy as np
from scipy.spatial import distance as dist
from .dal import *
from .viewmodel import *
from . import RECORDS_FOLDER, CLIP_FOLDER

video = Blueprint('video', __name__)

INPUT_WIDTH = 640
INPUT_HEIGHT = 640
SCORE_THRESHOLD = 0.2
NMS_THRESHOLD = 0.4
CONFIDENCE_THRESHOLD = 0.4

track_analytics = {

}

is_record_clip = False


def build_model(is_cuda):
    net = cv2.dnn.readNet("best.onnx")
    if is_cuda:
        print("Attempty to use CUDA")
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA_FP16)
    else:
        print("Running on CPU")
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
    return net


def detect(image, net):
    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (INPUT_WIDTH, INPUT_HEIGHT), swapRB=True, crop=False)
    net.setInput(blob)
    preds = net.forward()
    return preds


def load_capture(fileName):
    capture = cv2.VideoCapture(fileName)
    return capture


def load_classes():
    class_list = []
    with open("classes.txt", "r") as f:
        class_list = [cname.strip() for cname in f.readlines()]
    return class_list


class_list = load_classes()


def wrap_detection(input_image, output_data):
    class_ids = []
    confidences = []
    boxes = []

    rows = output_data.shape[0]

    image_width, image_height, _ = input_image.shape

    x_factor = image_width / INPUT_WIDTH
    y_factor = image_height / INPUT_HEIGHT

    for r in range(rows):
        row = output_data[r]
        confidence = row[4]
        if confidence >= 0.4:

            classes_scores = row[5:]
            _, _, _, max_indx = cv2.minMaxLoc(classes_scores)
            class_id = max_indx[1]
            if classes_scores[class_id] > .25:
                confidences.append(confidence)

                class_ids.append(class_id)

                x, y, w, h = row[0].item(), row[1].item(), row[2].item(), row[3].item()
                left = int((x - 0.5 * w) * x_factor)
                top = int((y - 0.5 * h) * y_factor)
                width = int(w * x_factor)
                height = int(h * y_factor)
                box = np.array([left, top, width, height])
                boxes.append(box)

    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.25, 0.45)

    result_class_ids = []
    result_confidences = []
    result_boxes = []

    for i in indexes:
        result_confidences.append(confidences[i])
        result_class_ids.append(class_ids[i])
        result_boxes.append(boxes[i])

    return result_class_ids, result_confidences, result_boxes


def format_yolov5(frame):
    row, col, _ = frame.shape
    _max = max(col, row)
    result = np.zeros((_max, _max, 3), np.uint8)
    result[0:row, 0:col] = frame
    return result


colors = [(255, 255, 0), (0, 255, 0), (0, 255, 255), (255, 0, 0)]

is_cuda = len(sys.argv) > 1 and sys.argv[1] == "cuda"

net = build_model(is_cuda)


def is_in_saved(saved_items, box):
    cx = (box[0] + box[2]) / 2
    cy = (box[1] + box[3]) / 2
    min_dist = 5
    for item in saved_items:
        d = dist.euclidean([cx, cy], [(item[0] + item[2]) / 2, (item[1] + item[3]) / 2])
        if min_dist > d:
            return True
    return False


def gen_frames(capture, clip_id, playonly=0, sess=None):
    start = time.time_ns()
    frame_count = 0
    actual_frame_count = 0
    saved_items = []
    global is_record_clip
    frame_folder = "{}/{}".format(RECORDS_FOLDER, clip_id)
    frame_file_name = "{}/frame_{}_{}.jpg"
    if not os.path.exists(frame_folder):
        os.mkdir(frame_folder)
    saved_boxes = []
    num_stationary = 0
    avg_speed = 0
    while True:
        _, frame = capture.read()
        if frame is None:
            print("End of stream")
            break

        if playonly == 0:
            inputImage = format_yolov5(frame)
            outs = detect(inputImage, net)

            class_ids, confidences, boxes = wrap_detection(inputImage, outs[0])
            distances = []
            sub_distance = []
            for i in range(len(boxes)):
                sub_distance.append(10000)
            for i in range(len(boxes)):
                distances.append(sub_distance.copy())
            for i in range(len(boxes)):
                sub_distance = []
                for k in range(len(boxes)):
                    sub_distance.append(10000)
                for j in range(len(boxes)):
                    if i != j:
                        distances[i][j] = dist.euclidean(boxes[i], boxes[j])

            nearMiss = []
            for i in range(len(boxes)):
                nearMiss.append(0)
            for i in range(len(boxes)):
                m = min(distances[i])
                idx = distances[i].index(m)
                if m < 89:
                    nearMiss[idx] = 1
                else:
                    nearMiss[i] = 0

            frame_count += 1
            for vehicle in class_list:
                sess[vehicle] = 0
            #   my_analytics_data[vehicle] =

            speed_sum = 0
            speed_count = 0

            for (classid, confidence, box, j) in zip(class_ids, confidences, boxes, range(len(boxes))):
                color = colors[int(classid) % len(colors)]
                sess[class_list[classid]] = sess[class_list[classid]] + 1
                box_center_x = (box[0] + box[2]) / 2
                box_center_y = (box[1] + box[3]) / 2

                shortest_dis = 5
                current_id = -1
                speed = 0
                for idx, si in enumerate(saved_items):
                    dis = dist.euclidean([box_center_x, box_center_y], [si['x'], si['y']])
                    if shortest_dis > dis:
                        speed = (dis * 30) * 60 * 60 / 10000
                        current_id = idx
                        break
                if current_id == -1:
                    saved_items.append({
                        'x': box_center_x,
                        'y': box_center_y,
                        'speed': speed
                    })
                    current_id = len(saved_items) - 1;
                else:
                    saved_items[current_id] = {
                        'x': box_center_x,
                        'y': box_center_y,
                        'speed': speed
                    }
                if speed != 0:
                    speed_sum += speed
                    speed_count += 1

                if nearMiss[j] == 1:
                    color = (165, 85, 236)
                cv2.rectangle(frame, box, color, 2)
                cv2.rectangle(frame, (box[0], box[1] - 20), (box[0] + box[2], box[1]), color, -1)
                cv2.putText(frame, "{} - {}".format(class_list[classid], current_id), (box[0], box[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 0, 0))

            if frame_count >= 30:
                frame_count = 0
            avg_speed = speed_sum / speed_count if speed_count > 0 else 1
            incident_prob = round(sum(nearMiss) * 100 / (len(nearMiss) + 1))
            accident_prob = round(incident_prob / 10)

            sess['incident_prob'] = incident_prob
            sess['accident_prob'] = accident_prob
            sess['avg_speed'] = avg_speed
            sess['stationary_object'] = len(boxes) - speed_count

            actual_frame_count = actual_frame_count + 1
            if is_record_clip:
                ffn = frame_file_name.format(frame_folder, clip_id, actual_frame_count)
                cv2.imwrite(ffn, frame)

        ret1, buffer1 = cv2.imencode('.jpg', frame)
        myFrame = buffer1.tobytes()
        try:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + myFrame + b'\r\n')
        except GeneratorExit:
            is_record_clip = False
            return


@video.route('/video-data')
@login_required
def analytics_data():
    vid = request.args.get('vid')
    if vid:
        from .view import decode_int
        vid = decode_int(vid)
    global track_analytics
    if vid not in track_analytics:
        track_analytics[vid] = {}
    return jsonify(track_analytics[vid])


@video.route('/video_feed', methods=['GET'])
@login_required
def video_feed():
    vid = request.args.get('vid')
    if vid:
        from .view import decode_int
        vid = decode_int(vid)
    media = get_media_by_id(vid)
    play_only = request.args.get('playonly')
    if play_only is None:
        play_only = 0
    else:
        play_only = int(play_only)
    capture = load_capture(media.path)
    sess = {
    }
    global track_analytics
    track_analytics[vid] = sess

    return Response(gen_frames(capture, vid, playonly=play_only, sess=sess),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@video.route('/start-record-clip')
@login_required
def start_record_clip():
    global is_record_clip
    is_record_clip = True
    return jsonify({'success': True})


@video.route('/stop-record-clip')
@login_required
def stop_record_clip():
    global is_record_clip
    prev_state = is_record_clip
    is_record_clip = False
    return jsonify({'success': True, 'prev_state': prev_state})


@video.route('/is-recording')
@login_required
def is_video_recoding():
    global is_record_clip
    return jsonify({'success': is_record_clip})


@video.route('/create-clip', methods=['POST'])
@login_required
def create_video():
    if request.method == 'POST':
        vid = request.form.get('vid')
        if vid is None:
            return jsonify({"success": False})
        else:
            from .view import decode_int
            vid = decode_int(vid)
        img_array = []
        frame_dir = '{}/{}'.format(RECORDS_FOLDER, vid)
        import glob
        files = glob.glob("{}/*.jpg".format(frame_dir))
        files = sorted(files, key=os.path.getmtime)
        size = ()
        for filename in files:
            img = cv2.imread(filename)
            height, width, layers = img.shape
            size = (width, height)
            img_array.append(img)
        import random
        rand_value = random.randint(1, 10000)
        only_file_name = "clip-{}".format(rand_value)
        video_file_name = '{}/clip_{}_{}_.avi'.format(CLIP_FOLDER, vid, rand_value)
        out = cv2.VideoWriter(video_file_name,
                              cv2.VideoWriter_fourcc(*'DIVX'), 30, size)
        for i in range(len(img_array)):
            out.write(img_array[i])
        out.release()
        for filename in files:
            os.remove(filename)
        os.rmdir(frame_dir)
        med = get_media_by_id(vid)
        if med:
            res = add_media(name="Stream-{}-{}".format(med.name, only_file_name),
                            path=video_file_name,
                            area_id=med.area_id,
                            media_type=StreamType.clip,
                            lat=med.lat,
                            long=med.long)
            if res:
                return jsonify({"success": True})
    return jsonify({"success": False})


@video.route('/check-camera', methods=['GET'])
@login_required
def check_camera():
    result = False
    vid = request.args.get('vid')
    if vid:
        from .view import decode_int
        vid = decode_int(vid)
    else:
        return jsonify({"camera_stat": result})

    my_video = get_media_by_id(vid)
    capture = load_capture(my_video.path)

    while True:
        _, frame = capture.read()
        if frame is not None:
            result = True
            break
        break
    return jsonify({"camera_stat": result})


@video.route('/analytics', methods=['GET'])
@login_required
def analytics():
    vid = request.args.get('vid')
    media = None
    if vid:
        from .view import decode_int
        vid = decode_int(vid)
        media = get_media_by_id(vid)
        media = format_media(media)

    return render_template("video.html", media=media)


@video.route('/clips', methods=['GET'])
@login_required
def clips():
    medias = get_all_media_by_type(StreamType.clip)
    medias = format_media_list(medias)
    from . import SESSION_CLIP_KEY
    clip_id = session.get(SESSION_CLIP_KEY)
    media = None
    if clip_id:
        media = get_media_by_id(clip_id)
        media = format_media(media)
    return render_template("clip.html", media=media, medias=medias)


@video.route('/current-clip')
@login_required
def current_clip():
    from .view import decode_int
    clip_id = decode_int(request.args.get('clip_id'))
    from . import SESSION_CLIP_KEY
    session[SESSION_CLIP_KEY] = clip_id
    return jsonify({'success': True})


@video.route('/live', methods=['GET'])
@login_required
def play_video():
    vid = request.args.get('vid')
    media = None
    if vid:
        from .view import decode_int
        vid = decode_int(vid)
        media = get_media_by_id(vid)
        media = format_media(media)

    return render_template("video.html", media=media, record_clip=True)
