import cv2
from ultralytics import YOLO

model = YOLO("models/helmet.pt")

image = cv2.imread("test.jpg")

if image is None:
    raise SystemExit("test.jpg topilmadi")

result = model(image, conf=0.5, classes=[0, 2])[0]
frame = result.plot()

cv2.imshow("HelmetGuard - Image Test", frame)

cv2.waitKey(0)
cv2.destroyAllWindows()