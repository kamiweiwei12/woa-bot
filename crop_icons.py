import subprocess
import cv2
import numpy as np
from PIL import Image
import io
import os

ADB_PATH = r"D:\MuMuPlayerGlobal\nx_device\12.0\shell\adb.exe"
DEVICE = "172.26.18.222:5555"

def screenshot():
    result = subprocess.run(
        [ADB_PATH, "-s", DEVICE, "exec-out", "screencap", "-p"],
        capture_output=True
    )
    img = Image.open(io.BytesIO(result.stdout))
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

os.makedirs("templates", exist_ok=True)

# 要保存的图标列表，按顺序点击
ICONS = [
    ("takeoff_icon",     "起飞图标（飞机斜向上侧面）"),
    ("landing_icon",     "降落图标（飞机斜向下侧面）"),
    ("maintenance_icon", "维修图标（飞机正面对称）"),
]

scale = 0.5
img = screenshot()
display = cv2.resize(img, (0,0), fx=scale, fy=scale)

clicked = []
current = [0]

def on_click(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN and current[0] < len(ICONS):
        rx, ry = int(x/scale), int(y/scale)
        clicked.append((rx, ry))
        name, desc = ICONS[current[0]]
        # 裁剪图标区域 40x30
        crop = img[ry-15:ry+15, rx-20:rx+20]
        path = f"templates/{name}.png"
        cv2.imwrite(path, crop)
        print(f"已保存 {path} ({rx},{ry})")
        cv2.circle(param, (x,y), 5, (0,255,0), -1)
        current[0] += 1
        if current[0] < len(ICONS):
            _, next_desc = ICONS[current[0]]
            print(f"请点击: {next_desc}")
        else:
            print("全部保存完成，按Q退出")
        cv2.imshow(win, param)

win = "点击图标保存模板，按Q退出"
cv2.namedWindow(win)
cv2.setMouseCallback(win, on_click, display)
cv2.imshow(win, display)

print(f"请点击: {ICONS[0][1]}")
cv2.waitKey(0)
cv2.destroyAllWindows()
