import cv2

STREAM_URL = "http://192.168.1.104:81/stream"
cap = cv2.VideoCapture(STREAM_URL)
if not cap.isOpened():
    print("Не удалось открыть поток. Проверь IP и что камера включена.")
    raise SystemExit

print("Поток открыт. 'q' , чтобы выйти.")
while True:
    ok, frame = cap.read()
    if not ok:
        print("Кадр не пришёл, переподключаюсь...")
        cap.release()
        cap = cv2.VideoCapture(STREAM_URL)
        continue
    cv2.imshow("ESP32-CAM", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
cap.release()
cv2.destroyAllWindows()