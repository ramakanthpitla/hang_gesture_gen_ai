import cv2
import mediapipe as mp
import pyautogui
import numpy as np

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Screen size for cursor mapping
screen_width, screen_height = pyautogui.size()
smooth_factor = 3  # Lower value = faster response

# Store previous cursor position
prev_x, prev_y = 0, 0

# Start video capture
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Flip the frame for natural hand movement
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Get landmark positions
            landmarks = hand_landmarks.landmark
            index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            index_pip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_PIP]
            middle_tip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
            middle_pip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_PIP]
            ring_tip = landmarks[mp_hands.HandLandmark.RING_FINGER_TIP]
            pinky_tip = landmarks[mp_hands.HandLandmark.PINKY_TIP]
            thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
            thumb_ip = landmarks[mp_hands.HandLandmark.THUMB_IP]
            wrist = landmarks[mp_hands.HandLandmark.WRIST]

            # Convert normalized coordinates to screen position
            x = np.interp(index_tip.x, [0, 1], [0, screen_width])
            y = np.interp(index_tip.y, [0, 1], [0, screen_height])

            # Smooth the cursor movement
            curr_x = prev_x + (x - prev_x) / smooth_factor
            curr_y = prev_y + (y - prev_y) / smooth_factor

            # **Cursor Movement (Only Index Finger Up)**
            if (index_tip.y < index_pip.y and  # Index raised
                middle_tip.y > middle_pip.y and  # Middle down
                ring_tip.y > middle_pip.y and  # Ring down
                pinky_tip.y > middle_pip.y):  # Pinky down
                pyautogui.moveTo(curr_x, curr_y, duration=0.01)

            # Update previous cursor position
            prev_x, prev_y = curr_x, curr_y

            # **Click (Thumbs Up Only)**
            if (thumb_tip.y < wrist.y and  # Thumb raised
                index_tip.y > index_pip.y and  # Index down
                middle_tip.y > middle_pip.y and  # Middle down
                ring_tip.y > middle_pip.y and  # Ring down
                pinky_tip.y > middle_pip.y):  # Pinky down
                pyautogui.click()

            # **Scroll Up (Only Index & Middle Up)**
            if (index_tip.y < index_pip.y and  # Index raised
                middle_tip.y < middle_pip.y and  # Middle raised
                ring_tip.y > middle_pip.y and  # Ring down
                pinky_tip.y > middle_pip.y):  # Pinky down
                pyautogui.scroll(40)  # Increased scroll speed

            # **Scroll Down (Only Index & Middle Down)**
            if (index_tip.y > index_pip.y and  # Index down
                middle_tip.y > middle_pip.y and  # Middle down
                ring_tip.y > middle_pip.y and  # Ring down
                pinky_tip.y > middle_pip.y):  # Pinky down
                pyautogui.scroll(-40)  # Increased scroll speed

    # Display the frame
    cv2.imshow("Virtual Mouse", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
