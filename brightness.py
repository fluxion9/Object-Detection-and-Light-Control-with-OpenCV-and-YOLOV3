import cv2
import numpy as np
import argparse
import requests

cam_url = 'http://192.168.4.1/capture'

ap = argparse.ArgumentParser()
ap.add_argument('-c', '--use_webcam', required=False,
                help = 'use built-in camera feed')
args = ap.parse_args()


if args.use_webcam == 'true':
    src, option = cv2.VideoCapture(0), True
else:
    src, option = cam_url, False

font = cv2.FONT_HERSHEY_PLAIN

while True:
    if option:
        _, frame = src.read()
        height, width, channels = frame.shape
    else:
        try:
            response = requests.get(src)
            image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            height, width, channels = frame.shape
        except requests.exceptions.RequestException as e:
            print("No Camera or Valid Frame Found")
            continue
    hsl = cv2.cvtColor(frame, cv2.COLOR_BGR2HLS)
    Lchanneld = hsl[:, :, 1]
    lvalueld = cv2.mean(Lchanneld)[0]
    # print(lvalueld)
    cv2.putText(frame, f'L value: {lvalueld:.2f}', (10, 450), font, 1, (0, 255, 0), 2, cv2.LINE_AA)
    cv2.imshow("Feed", frame)
    key = cv2.waitKey(1)
    if key == 27:
        break
if option:
    src.release()
cv2.destroyAllWindows()