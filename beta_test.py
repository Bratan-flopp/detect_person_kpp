import cv2
import time
import threading
import requests
from ultralytics import YOLO

STREAM_URL = "http://192.168.1.104:81/stream"
NTFY_TOPIC = "kpp_test" 
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

EXIT_TIMEOUT = 3.0

model = YOLO("yolov8n.pt")


def notify(text):
    def _send():
        try:
            requests.post(NTFY_URL, data=text.encode("utf-8"), timeout=5)
        except Exception as e:
            print("ntfy error:", e)
    threading.Thread(target=_send, daemon=True).start()


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

last_seen = {}
inside = set()

while True:
    frame = stream.read()
    if frame is None:
        continue

    now = time.time()

    results = model.track(frame, classes=[0], conf=0.4, imgsz=480,
                          #classes=[0] человек,conf=0.4 меньше ложных срабатываний imgsz=480 размер сжимается кадр перед подачей в модель. persist=True - стабильный id
                          persist=True, verbose=False)[0]
    annotated = results.plot(img=frame)

    current_ids = set() # кто в кадре
    
    if results.boxes.id is not None:
        current_ids = set(results.boxes.id.cpu().numpy().astype(int).tolist())

    for tid in current_ids:
        last_seen[tid] = now
        if tid not in inside:
            inside.add(tid)
            msg = f"Вошёл: ID {tid}"
            print(msg)
            notify(msg)

    for tid in list(inside):
        if tid not in current_ids:
            if now - last_seen.get(tid, 0) > EXIT_TIMEOUT:
                inside.discard(tid)
                msg = f"Вышел: ID {tid}"
                print(msg)
                notify(msg)

    cv2.putText(annotated, f"V pomeschenii: {len(inside)}",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    ids_str = ",".join(str(i) for i in sorted(inside))
    cv2.putText(annotated, f"IDs: {ids_str}",
                (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    cv2.imshow("KPP", annotated)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

stream.stop()
cv2.destroyAllWindows()