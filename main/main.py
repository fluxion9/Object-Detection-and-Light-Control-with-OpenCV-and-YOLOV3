import cv2
import numpy as np
import argparse
import time
import requests
import logging
import sys

cam_url = 'http://192.168.4.1/capture'

ap = argparse.ArgumentParser()
ap.add_argument('-c', '--use_webcam', required=False,
                help = 'use built-in camera feed')
ap.add_argument('-o', '--show', required=False,
                help = 'show output and boxes')
ap.add_argument('-L', '--logs', required=False,
                help = 'show logs on terminal')
args = ap.parse_args()

# net = cv2.dnn.readNet("yolov3-tiny.weights", "yolov3-tiny.cfg")

net = cv2.dnn.readNet('yolov4-tiny.weights', 'yolov4-tiny.cfg')

class LoggerWriter:
    def __init__(self, level):
        self.level = level

    def write(self, message):
        if message != '\n':
            self.level(message)

    def flush(self):
        pass

# Configure the logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create a logger object
logger = logging.getLogger()

if not args.logs == 'true':
    sys.stdout = LoggerWriter(logger.info)
    sys.stderr = LoggerWriter(logger.error)
else:
    logger.disabled = True

classes = []

with open("coco.txt", "r") as f:
    classes = [line.strip() for line in f.readlines()]

layer_names = net.getLayerNames()

colors = np.random.uniform(0, 255, size=(len(classes), 3))

def draw_prediction(img, class_id, confidence, x, y, x_plus_w, y_plus_h):

    label = str(classes[class_id])

    color = colors[class_id]

    cv2.rectangle(img, (x,y), (x_plus_w,y_plus_h), color, 2)

    cv2.putText(img, label, (x-10,y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

def get_output_layers(net):
    
    layer_names = net.getLayerNames()
    try:
        output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
    except:
        output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

    return output_layers

def Summary(inp):
    objects = set(inp)
    keys = []
    vals = []
    for obj in objects:
        keys.append(obj)
        vals.append(inp.count(obj))
    return dict(zip(keys, vals))

def handle_output(summaries):
    if summaries.__contains__('person'):
        try:
            res = requests.get("http://192.168.4.1/person")
        except requests.exceptions.RequestException as e:
            pass
    else:
        pass

def handle_darkness(lvalue):
    if lvalue < 13.0:
        try:
            res = requests.get("http://192.168.4.1/dark=1")
        except requests.exceptions.RequestException as e:
            pass
    else:
        try:
            res = requests.get("http://192.168.4.1/dark=0")
        except requests.exceptions.RequestException as e:
            pass

if args.use_webcam == 'true':
    src, option = cv2.VideoCapture(0), True
else:
    src, option = cam_url, False

font = cv2.FONT_HERSHEY_PLAIN
starting_time = time.time()
frame_id = 0

while True:
    if option:
        _, frame = src.read()
        frame_id += 1
        height, width, channels = frame.shape
    else:
        try:
            response = requests.get(src)
            frame_id += 1
            image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            height, width, channels = frame.shape
        except requests.exceptions.RequestException as e:
            print("No Camera or Valid Frame Found")
            continue
    
    # measuring brightness
    hsl = cv2.cvtColor(frame, cv2.COLOR_BGR2HLS)
    Lchanneld = hsl[:, :, 1]
    lvalueld = cv2.mean(Lchanneld)[0]

    # Detecting objects
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)

    net.setInput(blob)
    # outs = net.forward(output_layers)

    outs = net.forward(get_output_layers(net))

    # Showing informations on the screen
    class_ids = []
    confidences = []
    boxes = []
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            # if confidence > 0.2:
            if confidence > 0.1:
                # Object detected
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[3] * width)
                h = int(detection[3] * height)

                # Rectangle coordinates
                x = int(center_x - w / 1.8)
                y = int(center_y - h / 1.8)

                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.1, 0.5)


    objects = []
    accuracy = []

    for i in indexes:
        try:
            box = boxes[i]
        except:
            i = i[0]
            box = boxes[i]
        x = box[0]
        y = box[1]
        w = box[2]
        h = box[3]
        # print(classes[class_ids[i]], round(confidences[i]*100.0, 0))
        objects.append(classes[class_ids[i]])
        accuracy.append(round(confidences[i]*100.0, 0))
        if args.show == 'true':
            draw_prediction(frame, class_ids[i], confidences[i], round(x), round(y), round(x+w), round(y+h))
    
    
    summary = Summary(objects)

    print(summary)
    
    if args.use_webcam != 'true':
        handle_darkness(lvalueld)
        handle_output(summary)

    elapsed_time = time.time() - starting_time
    fps = frame_id / elapsed_time
    if args.show == 'true':
        cv2.putText(frame, "FPS: " + str(round(fps, 2)), (10, 50), font, 2, (255, 0, 0), 3)
        cv2.putText(frame, f'L value: {lvalueld:.2f}', (10, 450), font, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.imshow("Feed", frame)
        key = cv2.waitKey(1)
        if key == 27:
            break
if option:
    src.release()
cv2.destroyAllWindows()