import cv2
from ultralytics import YOLO

model = YOLO("models/helmet.pt")
cap = cv2.VideoCapture("test2.mp4")

if not cap.isOpened():
    raise SystemExit("Video ochilmadi. test.mp4 manzilini tekshiring.")

try:
    while True:
        success, frame = cap.read()

        if not success:
            break

        result = model(frame, conf=0.5, classes=[0, 2], verbose=False)[0]
        frame = result.plot()

        # 2 — biz yuklagan modeldagi NO-Hardhat sinfi
        if any(int(box.cls.item()) == 2 for box in result.boxes):
            cv2.putText(
                frame, "WARNING: NO HELMET", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2
            )

        cv2.imshow("HelmetGuard - Video", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    cap.release()
    cv2.destroyAllWindows()