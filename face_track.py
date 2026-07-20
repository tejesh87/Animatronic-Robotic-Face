import cv2
import serial
import time

# Replace 'COM3' with your Arduino Nano's COM port
arduino = serial.Serial('COM9', 9600)
time.sleep(2)  # wait for Arduino to initialize

# Open webcam
# Open webcam
cap = cv2.VideoCapture(0)

# Make window fullscreen
cv2.namedWindow("Face Tracking", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("Face Tracking", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)


# Load face detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        # Calculate face center
        faceX = x + w // 2
        faceY = y + h // 2

        # Map to servo range (safe: 10-170°)
        servoX = int((faceX / frame.shape[1]) * 160 + 10)
        servoY = int((faceY / frame.shape[0]) * 160 + 10)

        # Send angles to Arduino
        data = f"{servoX},{servoY}\n"
        arduino.write(data.encode())

        # Draw rectangle around face
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

    cv2.imshow("Face Tracking", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
arduino.close()
