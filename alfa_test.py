import cv2
import threading
from ultralytics import YOLO

STREAM_URL = "http://192.168.1.104:81/stream"

model = YOLO("yolov8n.pt")
class FreshFrame:
    def __init__(self, url):
        self.cap = cv2.VideoCapture(url)
        self.lock = threading.Lock()
        self.frame = None
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()
    def _loop(self):
        while self.running:
            ok, f = self.cap.read()
            if not ok:
                self.cap.release()
                self.cap = cv2.VideoCapture(STREAM_URL)
                continue
            with self.lock:
                self.frame = f
    def read(self):
        with self.lock:
            return None if self.frame is None else self.frame.copy()
    def stop(self):
        self.running = False
        self.cap.release()
stream = FreshFrame(STREAM_URL)
print("Поехали. 'q' в окне — выход.")
frame_i = 0
last = None 
while True:
    frame = stream.read()
    if frame is None:
        continue
    frame_i += 1
    if frame_i % 2 == 0:
        last = model(frame, classes=[0], conf=0.4,
                     imgsz=640, verbose=False)[0]

    annotated = last.plot(img=frame) if last is not None else frame
    cv2.imshow("KPP - detection", annotated)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

stream.stop()
cv2.destroyAllWindows()