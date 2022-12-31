from flask import Blueprint, render_template, request, flash, \
    redirect, url_for, Response, request
from flask_login import login_required, current_user
import cv2
import os
import time
import sys
import numpy as np
from scipy.spatial import distance as dist
from .dal import *
from .viewmodel import *

video = Blueprint('video', __name__)

INPUT_WIDTH = 640
INPUT_HEIGHT = 640
SCORE_THRESHOLD = 0.2
NMS_THRESHOLD = 0.4
CONFIDENCE_THRESHOLD = 0.4


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
            if (classes_scores[class_id] > .25):
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


def gen_frames(capture, clip_id, playonly=0):
    start = time.time_ns()
    frame_count = 0
    actual_frame_count = 0

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
        # for vehicle in class_list:
        #   my_analytics_data[vehicle] = 0
        for (classid, confidence, box, j) in zip(class_ids, confidences, boxes, range(len(boxes))):
            color = colors[int(classid) % len(colors)]
            # my_analytics_data[class_list[classid]] = my_analytics_data[class_list[classid]] + 1
            if nearMiss[j] == 1:
                color = (165, 85, 236)
            cv2.rectangle(frame, box, color, 2)
            cv2.rectangle(frame, (box[0], box[1] - 20), (box[0] + box[2], box[1]), color, -1)
            cv2.putText(frame, "{}".format(class_list[classid]), (box[0], box[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 0, 0))

        if frame_count >= 30:
            end = time.time_ns()
            fps = 1000000000 * frame_count / (end - start)
            frame_count = 0
            start = time.time_ns()
        incidentProb = round(sum(nearMiss) * 100 / (len(nearMiss) + 1))
        accidnetProb = round(incidentProb / 10)

        # my_analytics_data['accidnetProb'] = accidnetProb
        # my_analytics_data['incidentProb'] = incidentProb

        actual_frame_count = actual_frame_count + 1
        # if is_record_clip:
        # ffn = frame_file_name.format(frame_folder, clip_id, actual_frame_count)
        # suc = cv2.imwrite(ffn, frame)

    ret1, buffer1 = cv2.imencode('.jpg', frame)
    myFrame = buffer1.tobytes()
    yield (b'--frame\r\n'
           b'Content-Type: image/jpeg\r\n\r\n' + myFrame + b'\r\n')


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


@video.route('/analytics', methods=['GET'])
@login_required
def analytics():
    vid = request.args.get('vid')
    if not vid:
        vid = 1
    return render_template("video.html", media_name="Dummy Video", area_name="Dhaka", media=None)


@video.route('/clips', methods=['GET'])
@login_required
def clips():
    return render_template("video.html", media_name="Dummy Clip", area_name="Dhaka", media=None)


@video.route('/live', methods=['GET'])
@login_required
def play_video():
    return render_template("video.html", media_name="Dummy Live", area_name="Dhaka", media=None)
