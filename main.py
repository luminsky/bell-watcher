import os
import threading
import cv2
import numpy as np
import pyautogui
import tkinter as tk
from tkinter import filedialog
from playsound import playsound
from mss import mss, ScreenShotError

sec_interval = 0.5

bell_state = {
    'seen': False,
    'ringed': False
}

# init mss
sct = mss()

# prompt a file
root = tk.Tk()
root.withdraw()

watching_img_path = filedialog.askopenfilename(
    initialdir=os.getcwd(),
    title='Select a bell image to watch',
    filetypes=(('image files', ['*.jpg', '*.png']), ('all files', '*.*'))
)

if not watching_img_path:
    exit()


def process():
    i = 1
    while True:
        try:
            monitor = sct.monitors[i]

            # find bell
            bell_coords = pyautogui.locateOnScreen(watching_img_path, confidence=0.5, grayscale=True)

            if bell_coords:
                scrap = {
                    'left': bell_coords[0],
                    'top': bell_coords[1],
                    'width': bell_coords[2],
                    'height': bell_coords[3]
                }
                bell = np.asarray(sct.grab(scrap))

                # create hsv
                hsv = cv2.cvtColor(bell, cv2.COLOR_BGR2HSV)

                # define masks
                # lower mask (0-10)
                lower_red = np.array([0, 50, 50])
                upper_red = np.array([10, 255, 255])
                mask0 = cv2.inRange(hsv, lower_red, upper_red)

                # upper mask (170-180)
                lower_red = np.array([170, 50, 50])
                upper_red = np.array([180, 255, 255])
                mask1 = cv2.inRange(hsv, lower_red, upper_red)

                # join masks & check
                mask = mask0 + mask1
                has_red = np.sum(mask)

                red = (has_red > 0) & bell_state.seen

                if red & (not bell_state.ringed):
                    print('bell got red dot')
                    playsound('ring.wav')

                if red | (not bell_state.seen):
                    print('bell found')
                    bell_state.ringed = True
                else:
                    print('bell in sight')
                    bell_state.ringed = False

                bell_state.seen = True
            else:
                if bell_state.seen:
                    print('bell lost')
                else:
                    print('bell not in sight')

                bell_state.seen = False
                bell_state.ringed = False

            i += 1

            if i == len(sct.monitors):
                break
        except ScreenShotError:
            break
    threading.Timer(sec_interval, process).start()


threading.Timer(sec_interval, process).start()
