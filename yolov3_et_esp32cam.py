import cv2
import numpy as np
import time
import requests

url = 'http://192.168.43.231/cam-hi.jpg'

net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")

# net = cv2.dnn.readNet("yolov3-tiny.weights", "yolov3-tiny.cfg")

classes = []
with open("yolov3.txt", "r") as f:
    classes = [line.strip() for line in f.readlines()]
layer_names = net.getLayerNames()

colors = np.random.uniform(0, 255, size=(len(classes), 3))

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


font = cv2.FONT_HERSHEY_PLAIN

starting_time = time.time()

frame_id = 0

while True:
    try:
        response = requests.get(url)
        frame_id += 1
    except requests.exceptions.RequestException as e:
        response = None

    image_array = np.asarray(bytearray(response.content), dtype=np.uint8)

    frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    height, width = frame.shape[:2]

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
            if confidence > 0.5:
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

    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

    objects = []
    accuracy = []

    for i in range(len(boxes)):
        if i in indexes:
            x, y, w, h = boxes[i]
            label = str(classes[class_ids[i]])
            confidence = confidences[i]
            objects.append(classes[class_ids[i]])
            accuracy.append(round(confidences[i]*100.0, 0))
            color = colors[class_ids[i]]
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, label + " " + str(round(confidence, 2)), (x, y + 30), font, 2, color, 2)
    
    print(Summary(objects))


    elapsed_time = time.time() - starting_time
    fps = frame_id / elapsed_time
    cv2.putText(frame, "FPS: " + str(round(fps, 2)), (10, 50), font, 2, (0, 0, 0), 3)
    cv2.imshow("Image", frame)
    key = cv2.waitKey(1)
    if key == 27:
        break
cv2.destroyAllWindows()