import cv2
import mediapipe as mp
import pyautogui
import math
import time
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
SMOOTHING = 0.25
FINGER_CLOSED_RATIO = 0.75
CLICK_COOLDOWN = 0.5
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
screen_width, screen_height = pyautogui.size()
pyautogui.PAUSE = 0.01
previous_x = screen_width / 2
previous_y = screen_height / 2
last_click_time = 0
fist_detected = False
def distance(p1, p2):
    return math.sqrt(
        (p1.x - p2.x) ** 2 +
        (p1.y - p2.y) ** 2
    )
def finger_is_closed(landmarks, tip, pip):
    """
    Checks whether a finger is folded.
    tip = fingertip landmark
    pip = middle joint landmark
    """
    return distance(landmarks[tip], landmarks[0]) < \
           distance(landmarks[pip], landmarks[0]) * FINGER_CLOSED_RATIO

def is_fist(hand_landmarks):
    """
    Detects whether all four fingers are closed.
    """
    lm = hand_landmarks.landmark
    index_closed = finger_is_closed(lm, 8, 6)
    middle_closed = finger_is_closed(lm, 12, 10)
    ring_closed = finger_is_closed(lm, 16, 14)
    little_closed = finger_is_closed(lm, 20, 18)
    return (
        index_closed
        and middle_closed
        and ring_closed
        and little_closed
    )
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
if not cap.isOpened():
    print("ERROR: Could not open webcam.")
    exit()
while True:
    success, frame = cap.read()
    if not success:
        print("ERROR: Could not read webcam.")
        break
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)
    gesture = "NO HAND"
    if results.multi_hand_landmarks:
        hand = results.multi_hand_landmarks[0]
        lm = hand.landmark
        mp_draw.draw_landmarks(
            frame,
            hand,
            mp_hands.HAND_CONNECTIONS
        )
        current_fist = is_fist(hand)
        if current_fist:
            gesture = "FIST - CLICK"
            current_time = time.time()
            if (
                not fist_detected
                and current_time - last_click_time > CLICK_COOLDOWN
            ):
                pyautogui.click()
                last_click_time = current_time
            fist_detected = True
        else:
            fist_detected = False
            index_tip = lm[8]
            x = index_tip.x
            y = index_tip.y
            x = max(0.05,  min(0.95, x))
            y = max(0.05, min(0.95, y))
            target_x = x * screen_width
            target_y = y * screen_height
            current_x = (
                previous_x
                + (target_x - previous_x) * SMOOTHING
            )
            current_y = (
                previous_y
                + (target_y - previous_y) * SMOOTHING
            )
            pyautogui.moveTo(
                int(current_x),
                int(current_y)
            )
            previous_x = current_x
            previous_y = current_y
            gesture = "MOVE"
    else:
        fist_detected = False
    cv2.putText(
        frame,
        f"Gesture: {gesture}",
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 255, 255),
        2
    )
    cv2.putText(
        frame,
        "INDEX = MOVE | FIST = LEFT CLICK | Q/ESC = QUIT",
        (30, CAMERA_HEIGHT - 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )
    cv2.imshow("Hand Gesture Mouse", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q") or key == 27:
        break
cap.release()
cv2.destroyAllWindows()
hands.close()