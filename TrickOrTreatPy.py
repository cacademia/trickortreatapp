import cv2
import mediapipe as mp
import numpy as np
import random
import pygame
import time

class Candy:
    def __init__(self, image_width, image_height, speed):
        self.x = random.randint(0, image_width)
        self.y = 0  # Start candies at the top of the screen
        self.speed = speed  # Adjust the speed as needed
        self.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    def move(self):
        self.y += self.speed

class HandTracker:
    def __init__(self, mode=False, max_hands=4, detection_confidence=0.25, model_complexity=1, tracking_confidence=0.25):
        self.mode = mode
        self.max_hands = max_hands
        self.detection_confidence = detection_confidence
        self.model_complexity = model_complexity
        self.tracking_confidence = tracking_confidence

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(self.mode, self.max_hands, self.model_complexity,
                                         self.detection_confidence, self.tracking_confidence)
        self.mp_draw = mp.solutions.drawing_utils

    def find_hands(self, image, draw=True):
        # Mirror the image horizontally
        image = cv2.flip(image, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.hands.process(image_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                if draw:
                    self.mp_draw.draw_landmarks(image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

        return image, results.multi_hand_landmarks

    def find_positions(self, image, hand_number=0, draw=True):
        landmarks_list = []
        results = self.hands.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[hand_number]
            for id, landmark in enumerate(hand.landmark):
                h, w, c = image.shape
                cx, cy = int(landmark.x * w), int(landmark.y * h)
                landmarks_list.append([id, cx, cy])

                if draw:
                    # cv2.circle(image, (cx, cy), 15, (255, 0, 255), cv2.FILLED)
                    pass

        return landmarks_list

def display_text(image, text, position, font_scale, color):
    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)[0]
    text_x = (image.shape[1] - text_size[0]) // 2
    cv2.putText(image, text, (text_x, position[1]), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 2)

def show_start_screen():
    # Create a black background
    black_screen = np.zeros((720, 1280, 3), dtype=np.uint8)

    message_lines = [
        "Dear my favorite trick or treater,",
        "",
        "I'm sorry that you haven't been able to do too much for Halloween this year",
        "because you've been so busy studying.",
        "I've been working on this, so that even for", 
        "five minutes, you can have just a bit of fun on Halloween :)",
        "I hope that you like it.",
        "",
        "P.S. I can't wait to see you again!",
        "Kind regards,",
        "Christian",
        "",
        "Last thing!  Use your hands to catch the candy!",
        "Good luck!  Press 'n' to move on."
    ]

    line_height = 40  # Adjust this value as needed for spacing between lines
    y_position = 150  # Initial y position

    while True:
        image = black_screen.copy()
        y = y_position
        for line in message_lines:
            display_text(image, line, (100, y), 1, (255, 255, 255))
            y += line_height
        cv2.imshow("Trick or Treat<3", image)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("n") or key == ord("N"):
            break

def main():
    # Initialize Pygame for audio playback
    pygame.mixer.init()
    pygame.mixer.music.load("Glue Song feat Clairo.wav")
    pygame.mixer.music.set_volume(0.25)
    pygame.mixer.music.play(-1)  # Play in an infinite loop

    cap = cv2.VideoCapture(0)
    tracker = HandTracker()

    show_start_screen()  # Show the initial screen

    cv2.namedWindow("Trick or Treat<3", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Trick or Treat<3", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    level = 1  # Start at level 1
    level_candy_goal = 10  # Initial candy goal for the current level
    level_candy_count = 0  # Initialize level candy count
    overall_candy_count = 0  # Initialize overall candy count
    candy_speed = random.uniform(5, 8)  # Initial candy speed

    candy_list = []

    show_level_message = True
    show_level_message_start_time = time.time()
    level_message_duration = 3.0  # Display level message for 3 seconds
    fade_duration = 1.0  # Duration for fading in and out

    while True:
        success, image = cap.read()
        image, landmarks = tracker.find_hands(image)

        if show_level_message:
            if time.time() - show_level_message_start_time < level_message_duration:
                alpha = min(1.0, (time.time() - show_level_message_start_time) / fade_duration)
                overlay = image.copy()
                display_text(overlay, f"House {level}.", (200, 200), 3, (255, 255, 255))  # White color
                cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, image)
            else:
                show_level_message = False
                show_level_message_start_time = time.time()

        if not show_level_message:
            # Check if the current level's candy goal has been reached
            if level_candy_count >= level_candy_goal:
                level += 1
                overall_candy_count += level_candy_count
                level_candy_count = 0  # Reset level candy count
                level_candy_goal = 5 * level  # Set the new candy goal for the next level
                candy_speed = random.uniform(7, 12)  # Randomize the candy speed for the next level (faster)
                show_level_message = True
                show_level_message_start_time = time.time()

            # Reduce candy drop rate over time
            if len(candy_list) < level_candy_goal:
                if random.random() < 0.1:  # 10% probability of adding a candy
                    candy_list.append(Candy(image.shape[1], image.shape[0], candy_speed))

            for candy in candy_list:
                candy.move()
                cv2.circle(image, (int(candy.x), int(candy.y)), 10, candy.color, -1)

                # Check for collision with candies
                if landmarks:
                    for hand_landmarks in landmarks:
                        landmarks_list = []

                        for landmark in hand_landmarks.landmark:
                            x, y = int(landmark.x * image.shape[1]), int(landmark.y * image.shape[0])
                            landmarks_list.append((x, y))

                        if landmarks_list:
                            min_x = min(landmarks_list, key=lambda x: x[0])[0]
                            max_x = max(landmarks_list, key=lambda x: x[0])[0]
                            min_y = min(landmarks_list, key=lambda x: x[1])[1]
                            max_y = max(landmarks_list, key=lambda x: x[1])[1]

                            for candy in candy_list:
                                if min_x < candy.x < max_x and min_y < candy.y < max_y:
                                    # Candy is caught, increase the score and remove the candy
                                    overall_candy_count += 1
                                    level_candy_count += 1
                                    candy_list.remove(candy)

                # Remove candies that have reached the bottom
                if candy.y > image.shape[0]:
                    candy_list.remove(candy)

        # Display the score, level candy count, candy goal, and overall candy count
        display_text(image, f"Overall Candy Count: {overall_candy_count}", (10, 30), 1, (255, 255, 255))  # White color
        display_text(image, f"Level Candy Count: {level_candy_count}", (10, 70), 1, (255, 255, 255))  # White color
        display_text(image, f"Candy Goal: {level_candy_goal}", (10, 110), 1, (255, 255, 255))  # White color

        cv2.imshow("Trick or Treat<3", image)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # Press 'Esc' to exit
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
