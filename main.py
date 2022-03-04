import os
import glob
import threading
import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog
from playsound import playsound
from mss import mss, ScreenShotError

sec_interval = 3


class bell_state:
    seen = False
    ringed = False


# init mss
sct = mss()

# prompt a file
root = tk.Tk()
root.withdraw()

# ask for image file path
watching_img_path = filedialog.askopenfilename(
    initialdir=os.getcwd(),
    title='Select a bell image to watch',
    filetypes=(('image files', ['*.jpg', '*.png']), ('all files', '*.*'))
)

if not watching_img_path:
    exit()

watching_img = cv2.imread(watching_img_path)

# remove previous temporary images
fileList = glob.glob('./.screenshot[0-9_-]*.png')

for filePath in fileList:
    try:
        os.remove(filePath)
    except OSError:
        print('error deleting file ' + filePath)


def process():
    monitor_num = 1
    while True:
        try:
            # make & format screenshot
            monitor = sct.monitors[monitor_num]
            screenshot = sct.grab(monitor)
            screenshot = np.asarray(screenshot.pixels)
            screenshot_uint8 = screenshot.astype(np.uint8)

            # find bell
            result = cv2.matchTemplate(watching_img, screenshot_uint8, cv2.TM_SQDIFF_NORMED)

            # get minimum squared difference
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if min_val != 1.0:
                # extract coordinates of the best match
                mpx, mpy = min_loc

                # get size of the template
                trows, tcols = watching_img.shape[:2]

                scrap = {
                    'left': mpx,
                    'top': mpy,
                    'width': trows,
                    'height': tcols
                }
                bell = sct.grab(scrap)
                bell = np.asarray(bell)

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

            monitor_num += 1

            if monitor_num == len(sct.monitors):
                break
        except ScreenShotError:
            break
    threading.Timer(sec_interval, process).start()


threading.Timer(sec_interval, process).start()
