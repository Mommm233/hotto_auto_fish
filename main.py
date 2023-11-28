# coding=utf-8
import numpy as np
import cv2
import pyautogui
import pygetwindow as gw
import time
import ctypes
import sys
import keyboard
import json
import threading
import random

class MoveDirection(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.run_flag = False
        self.yellow_mid = None
        self.white_mid = None
        self.last_yellow_mid = None
        self.last_white_mid = None
        self.delay = 0
    
    def update(self, yellow_left, yellow_right, white_left, white_right):
        if self.white_mid != None:
            self.last_white_mid = self.white_mid
            self.last_yellow_mid = self.yellow_mid

        self.white_mid = (white_left + white_right) // 2
        self.yellow_mid = (yellow_left + yellow_right) // 2
        x = abs(self.yellow_mid - self.white_mid)
        if yellow_left < self.white_mid < yellow_right:
            self.delay = 0.1 * x / 12
        else:
            self.delay = 0.1 * x / 24
        
    def stop(self):
        self.yellow_mid = None
        self.white_mid = None

    def run(self):
        while self.run_flag:
            if self.white_mid == None or self.yellow_mid == None:
                time.sleep(0.5)
                continue
            elif self.last_yellow_mid == self.yellow_mid and self.last_white_mid == self.white_mid:
                continue

            if self.white_mid <= self.yellow_mid:
                key = 'd'
            elif self.white_mid > self.yellow_mid:
                key = 'a'

            pyautogui.keyDown(key)
            time.sleep(self.delay + random.uniform(0.05, 0.1))
            pyautogui.keyUp(key)



# np.set_printoptions(threshold=np.inf)

def get_img_gray(img_rect):
    left = img_rect[0] + window_object.left
    top = img_rect[1] + window_object.top

    img = pyautogui.screenshot(region=(left, top, img_rect[2], img_rect[3]))
    img = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    return img_gray

def get_x_tuple(gray_np_1d, vmin, vmax, len):
    left, right = None, None
    i, j = 0, gray_np_1d.shape[0] - 1
    for i in range(gray_np_1d.shape[0]):
        if vmin <= gray_np_1d[i] <= vmax:
            if len * vmin <= gray_np_1d[i:i+len].sum() <= len * vmax:
                left = i + len // 2
                break
    for j in range(gray_np_1d.shape[0] - 1, -1, -1):
        if vmin <= gray_np_1d[j] <= vmax:
            if len * vmin <= gray_np_1d[j-len+1:j+1].sum() <= len * vmax:
                right = j - len // 2
                break
    return (left, right)
        
def simulate_process_bar(len, yellow_left, yellow_right, white_left, white_right):
    size = simulate_setting['len']
    white_x = int((white_left + white_right) // 2 * size / len)
    yellow_left = int(yellow_left * size / len)
    yellow_right = int(yellow_right * size / len)
    s = ' ' * size
    s = s[:yellow_left] + '<' + s[yellow_left + 1:yellow_right] + '>' + s[yellow_right + 1:]
    s = s[:white_x] + '|' + s[white_x + 1:]
    print(f'[{s}]', end='\r')

def get_screenshot(left, top, width, height):
    screenshot = pyautogui.screenshot(region=(left, top, width, height))
    screenshot_np = np.array(screenshot)
    screenshot_rgb = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2RGB)
    screenshot_gray = cv2.cvtColor(screenshot_rgb, cv2.COLOR_BGR2GRAY)
    return screenshot_gray

def move(yellow_left, yellow_right, white_left, white_right):
    white_mid = (white_left + white_right) // 2
    yellow_mid = (yellow_left + yellow_right) // 2
    if white_mid <= yellow_mid:
        key = 'd'
    elif white_mid > yellow_mid:
        key = 'a'

    pyautogui.keyDown(key)
    time.sleep(0.2)
    pyautogui.keyUp(key)

def keyboard_press(key):
    pyautogui.keyDown(key)
    pyautogui.keyUp(key)

def mouse_click():
    [x, y] = pyautogui.position()
    pyautogui.click(x, y, button='left')

def img_match(original, template):
    res = cv2.matchTemplate(original, template, cv2.TM_CCORR_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    return max_val > threshold

def wait_stop():
    if keyboard.is_pressed(key_combinations['stop']):
        print("程序运行结束！")
        return True
    return False

def wait_restart():
    if keyboard.is_pressed(key_combinations['restart']):
        return True
    return False

def check_placement_and_bait():
    while not wait_stop():
        if wait_restart():
            global restart
            restart = True
            return False

        placement_original = get_img_gray(placement_rect)
        if img_match(placement_original, placement_template):
            print('检测到鱼钩落点！')
            bait_original = get_img_gray(bait_rect)
            have_bait = False
            for bait_template in bait_templates:
                if img_match(bait_original, bait_template):
                    have_bait = True
                    break
            if not have_bait:
                print('没有鱼饵！')
                return False
            else:
                print('已装备鱼饵！')
            keyboard_press('1')
            return True

        time.sleep(0.5)
    return False

def check_bite():
    while not wait_stop():
        if wait_restart():
            global restart
            restart = True
            return False
        
        bite_original = get_img_gray(bite_rect)
        if img_match(bite_original, bite_template):
            print('鱼上钩！')
            return True
    return False

def check_splider():
    print('抓捕中...')

    start_t = time.time()
    while not wait_stop():
        if wait_restart():
            global restart
            restart = True
            return False
        
        process_bar_gray = get_img_gray(process_bar_rect)
        process_bar_gray_np_1d = np.mean(np.array(process_bar_gray), axis=0).astype(np.uint8)
        yellow_left, yellow_right= get_x_tuple(process_bar_gray_np_1d, yellow_vmin, yellow_vmax, 20)
        white_left, white_right = get_x_tuple(process_bar_gray_np_1d, white_vmin, white_vmax, 1)
        if yellow_left == None or white_left == None:
            continue
        
        if simulate_setting['mode'] == 1:
            simulate_process_bar(process_bar_gray_np_1d.shape[0], yellow_left, yellow_right, white_left, white_right)

        movedirection.update(yellow_left, yellow_right, white_left, white_right)
        
        endurance_gray = get_img_gray(endurance_rect)
        endurance_binary = endurance_gray // 218
        if np.sum(endurance_binary) == 0:
            print('抓到了！')
            movedirection.stop()
            time.sleep(0.5)
            keyboard_press('1')
            time.sleep(2)
            mouse_click()
            return True
        end_t = time.time()
        if end_t - start_t > limit_time:
            print("超时")
            movedirection.stop()
            return True

    return False

def running():
    global restart
    restart = False
    print('自动钓鱼\n' + '    开始钓鱼: Ctrl + F\n' + '    结束钓鱼: Ctrl + Q\n' + '    重新开始: Ctrl + S\n')
    keyboard.wait(key_combinations['start'])

    #window_object.activate()
    while not wait_stop():
        print('\033c', end='')
        print('自动钓鱼\n' + '    开始钓鱼: Ctrl + F\n' + '    结束钓鱼: Ctrl + Q\n' + '    重新开始: Ctrl + S\n')
        print('程序开始运行!')

        if not check_placement_and_bait():
            break
        if not check_bite():
            break
        time.sleep(1)
        if not check_splider():
            break

    movedirection.stop()

    if restart:
        print('正在重新开始...')
        time.sleep(1)
        running()
    print('程序即将退出...')
    time.sleep(3)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == "__main__":
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)

    with open(r'C:\Users\wengym\Desktop\AutoFinshing\config.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    rects = data['rects']
    paths = data['paths']
    key_combinations = data['key_combinations']

    simulate_setting = data['simulate_setting']
    limit_time = data['limit_time']
    threshold = data['threshold']

    restart = False

    window_object = gw.getWindowsWithTitle(data['window_title'])[0]

    placement_rect = rects['placement_rect']   # 鱼钩落点
    bait_rect = rects['bait_rect']    # 鱼饵
    bite_rect = rects['bite_rect']    # 鱼上钩
    process_bar_rect = rects['process_bar_rect']    # 进度条
    endurance_rect = rects['endurance_rect']   # 鱼耐力
    yellow_vmin = data['yellow_vmin']
    yellow_vmax = data['yellow_vmax']
    white_vmin = data['white_vmin']
    white_vmax = data['white_vmax']

    # 鱼钩模板
    placement_template = cv2.imread(paths[0], cv2.IMREAD_GRAYSCALE)
    # 鱼饵模板
    bait_templates = []
    for x in paths[1]:
        bait_templates.append(cv2.imread(x, cv2.IMREAD_GRAYSCALE))
    # 鱼上钩模板
    bite_template = cv2.imread(paths[2], cv2.IMREAD_GRAYSCALE)

    movedirection = MoveDirection()
    movedirection.run_flag = True
    movedirection.start()
    try:
        running()
        movedirection.run_flag = False
        movedirection.join()

    except Exception as e:
        movedirection.run_flag = False
        movedirection.join()
        print(str(e))
        with open(r'C:\Users\wengym\Desktop\AutoFinshing\error.log', 'w', encoding='utf-8') as f:
            f.write(str(e) + '\n')

