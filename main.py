from pathlib import Path
import cv2
from ultralytics import YOLO


def main():
    weights = Path(__file__).parent / "models" / "helmet.pt"

    if not weights.is_file():
        raise SystemExit("models/helmet.pt topilmadi")

    model = YOLO(str(weights))
    cap = cv2.VideoCapture(0)

    try:
        if not cap.isOpened():
            raise SystemExit("Kamera ochilmadi")

        while True:
            success, frame = cap.read()

            if not success:
                break

            result = model(
                frame,
                conf=0.5,
                classes=[0, 2],
                verbose=False
            )[0]

            frame = result.plot()

            # 2 — ushbu modeldagi NO-Hardhat sinfi
            if any(int(box.cls.item()) == 2 for box in result.boxes):
                cv2.putText(
                    frame,
                    "WARNING: NO HELMET",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )

            cv2.imshow("HelmetGuard - Q to quit", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()