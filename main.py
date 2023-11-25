# coding=utf-8
import numpy as np
import cv2
import pyautogui
import pygetwindow as gw
import time
import random
import ctypes
import sys
import keyboard
import json

np.set_printoptions(threshold=np.inf)

def get_img_gray(img, img_rect):
    top_left_x = img_rect[0]
    top_left_y = img_rect[1]
    bottom_right_x = top_left_x + img_rect[2]
    bottom_right_y = top_left_y + img_rect[3]
    img_gray = img[
        top_left_y:bottom_right_y, top_left_x:bottom_right_x
    ].copy()
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
    if yellow_left + 10 < white_mid < yellow_right - 10:
        return
    yellow_mid = (yellow_left + yellow_right) // 2
    if white_mid <= yellow_mid:
        key = 'd'
    elif white_mid > yellow_mid:
        key = 'a'

    pyautogui.keyDown(key)
    time.sleep(random.uniform(0.1, 0.5) * move_speed + move_speed_ratio * abs(white_mid - yellow_mid))
    pyautogui.keyUp(key)

def keyboard_press(key):
    pyautogui.keyDown(key)
    pyautogui.keyUp(key)

def mouse_click():
    x, y = pyautogui.position()
    pyautogui.click(x, y, button='left')

def img_match(original, template):
    res = cv2.matchTemplate(original, template, cv2.TM_CCORR_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    return max_val > threshold

def wait_stop():
    if keyboard.is_pressed(stop_key_combination):
        print("程序运行结束！")
        return True
    return False

def wait_restart():
    if keyboard.is_pressed(restart_key_combination):
        return True
    return False

def check_placement_and_bait(window_object, placement_rect, bait_rect, placement_template, bait_template):
    left, top, width, height = window_object.left, window_object.top, window_object.width, window_object.height
    while not wait_stop():
        if wait_restart():
            global restart
            restart = True
            return False
        window_screenshot_gary = get_screenshot(left, top, width, height)
        placement_original = get_img_gray(window_screenshot_gary, placement_rect)

        if img_match(placement_original, placement_template):
            print('检测到鱼钩落点！')
            bait_original = get_img_gray(window_screenshot_gary, bait_rect)
            if not img_match(bait_original, bait_template):
                print('没有鱼饵！')
                print('程序即将退出...')
                time.sleep(3)
                sys.exit(0)
            else:
                print('已装备鱼饵！')
            keyboard_press('1')
            return True

        time.sleep(0.5)
    return False

def check_bite(window_object, bite_rect, bite_template):
    left, top, width, height = window_object.left, window_object.top, window_object.width, window_object.height
    while not wait_stop():
        if wait_restart():
            global restart
            restart = True
            return False
        window_screenshot_gary = get_screenshot(left, top, width, height)
        bite_original = get_img_gray(window_screenshot_gary, bite_rect)

        if img_match(bite_original, bite_template):
            print('鱼上钩！')
            return True
        # time.sleep(0.1)
    return False

def check_splider(window_object, menu_bar_rect, endurance_rect, process_bar_rect):
    left, top, width, height = window_object.left, window_object.top, window_object.width, window_object.height
    print('抓捕中...')

    start_t = time.time()
    while not wait_stop():
        if wait_restart():
            global restart
            restart = True
            return False
        window_screenshot_gary = get_screenshot(left, top, width, height)
        menu_bar_gray = get_img_gray(window_screenshot_gary, menu_bar_rect)
        endurance_gray = get_img_gray(menu_bar_gray, endurance_rect)
        endurance_binary = endurance_gray // 218

        if np.sum(endurance_binary) == 0:
            print('抓到了！')
            keyboard_press('1')
            time.sleep(2)
            mouse_click()
            return True
        
        process_bar_gray = get_img_gray(menu_bar_gray, process_bar_rect)
        process_bar_gray_np_1d = np.mean(np.array(process_bar_gray), axis=0).astype(np.uint8)

        yellow_left, yellow_right= get_x_tuple(process_bar_gray_np_1d, 184, 190, 10)
        white_left, white_right = get_x_tuple(process_bar_gray_np_1d, 252, 258, 1)
        if yellow_left == None or white_left == None:
            continue
        if simulate_setting['mode'] == 1:
            simulate_process_bar(process_bar_gray_np_1d.shape[0], yellow_left, yellow_right, white_left, white_right)
        move(yellow_left, yellow_right, white_left, white_right)
        time.sleep(0.1)

        end_t = time.time()
        if end_t - start_t > limit_time:
            print("超时")
            return True
    return False

def running():
    global restart
    restart = False
    print('自动钓鱼\n' + '    开始钓鱼: Ctrl + F\n' + '    结束钓鱼: Ctrl + Q\n' + '    重新开始: Ctrl + S\n')
    keyboard.wait(key_combinations['start'])

    window_object = gw.getWindowsWithTitle(window_title)[0]

    menu_bar_rect = rects['menu_bar_rect']
    placement_rect = rects['placement_rect']   # 鱼钩落点
    bait_rect = rects['bait_rect']    # 鱼饵
    bite_rect = rects['bite_rect']    # 鱼上钩
    process_bar_rect = rects['process_bar_rect']
    endurance_rect = rects['endurance_rect']   # 鱼耐力

    placement_template = cv2.imread(paths[0], cv2.IMREAD_GRAYSCALE)
    bait_template = cv2.imread(paths[1], cv2.IMREAD_GRAYSCALE)
    bite_template = cv2.imread(paths[2], cv2.IMREAD_GRAYSCALE)

    window_object.activate()
    while not wait_stop():
        print('\033c', end='')
        print('自动钓鱼\n' + '    开始钓鱼: Ctrl + F\n' + '    结束钓鱼: Ctrl + Q\n' + '    重新开始: Ctrl + S\n')
        print('程序开始运行!')

        if not check_placement_and_bait(
                window_object, 
                placement_rect, 
                bait_rect,
                placement_template, 
                bait_template
        ):
            break
        if not check_bite(
                window_object, 
                bite_rect, 
                bite_template
        ):
            break
        time.sleep(1)
        if not check_splider(
            window_object,
            menu_bar_rect, 
            endurance_rect, 
            process_bar_rect,
        ):
            break
        time.sleep(2)

    if restart:
        print('正在重新开始...')
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
    window_title = data['window_title']
    rects = data['rects']
    paths = data['paths']
    key_combinations = data['key_combinations']
    stop_key_combination = key_combinations['stop']
    restart_key_combination = key_combinations['restart']
    simulate_setting = data['simulate_setting']
    limit_time = data['limit_time']
    move_speed = data['move_speed']
    move_speed_ratio =data['move_speed_ratio']
    threshold = data['threshold']

    restart = False
    
    try:
        running()
    except Exception as e:
        with open(r'C:\Users\wengym\Desktop\AutoFinshing\error.log', 'w', encoding='utf-8') as f:
            f.write(str(e) + '\n')


