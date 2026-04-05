"""
调试工具：截图后显示坐标，框选区域查看 OCR 结果
- 鼠标移动：显示当前坐标
- 左键拖拽：框选区域，显示坐标范围 + OCR 识别结果
- 按 S：重新截图
- 按 Q：退出
"""
import subprocess, cv2, numpy as np, pytesseract, io, sys, os
from PIL import Image

ADB_PATH = r"D:\MuMuPlayerGlobal\nx_device\12.0\shell\adb.exe"
DEVICE   = "172.26.18.222:5555"

def resource_path(rel):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)

pytesseract.pytesseract.tesseract_cmd = resource_path(r"Tesseract-OCR\tesseract.exe")

SCALE = 0.6  # 显示缩放比例

def screenshot():
    r = subprocess.run([ADB_PATH, "-s", DEVICE, "exec-out", "screencap", "-p"],
                       capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    return cv2.cvtColor(np.array(Image.open(io.BytesIO(r.stdout))), cv2.COLOR_RGB2BGR)

img_orig = screenshot()
img_display = cv2.resize(img_orig, (0,0), fx=SCALE, fy=SCALE)

drawing = False
x0, y0, x1, y1 = 0, 0, 0, 0
overlay = img_display.copy()

def to_orig(x, y):
    return int(x / SCALE), int(y / SCALE)

def ocr_region(ox1, oy1, ox2, oy2):
    crop = img_orig[oy1:oy2, ox1:ox2]
    if crop.size == 0:
        return "（区域为空）"
    big  = cv2.resize(crop, (0,0), fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(big, cv2.COLOR_BGR2GRAY)
    inv  = cv2.bitwise_not(gray)
    _, th = cv2.threshold(inv, 180, 255, cv2.THRESH_BINARY)
    t1 = pytesseract.image_to_string(th, config="--psm 7 -l chi_sim").strip()
    _, th2 = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY)
    t2 = pytesseract.image_to_string(th2, config="--psm 7 -l chi_sim").strip()
    return f"反色: [{t1}]  正色: [{t2}]"

def mouse_cb(event, x, y, flags, param):
    global drawing, x0, y0, x1, y1, overlay

    ox, oy = to_orig(x, y)

    if event == cv2.EVENT_MOUSEMOVE:
        tmp = overlay.copy()
        # 十字线
        cv2.line(tmp, (x, 0), (x, tmp.shape[0]), (0,255,255), 1)
        cv2.line(tmp, (0, y), (tmp.shape[1], y), (0,255,255), 1)
        cv2.putText(tmp, f"({ox},{oy})", (x+6, y-6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 1)
        if drawing:
            cv2.rectangle(tmp, (x0,y0), (x,y), (0,255,0), 1)
        cv2.imshow(WIN, tmp)

    elif event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        x0, y0 = x, y

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        x1, y1 = x, y
        ox0, oy0 = to_orig(x0, y0)
        ox1b, oy1b = to_orig(x1, y1)
        rx1, ry1 = min(ox0,ox1b), min(oy0,oy1b)
        rx2, ry2 = max(ox0,ox1b), max(oy0,oy1b)
        result = ocr_region(rx1, ry1, rx2, ry2)
        print(f"\n框选原始坐标: x1={rx1} y1={ry1} x2={rx2} y2={ry2}")
        print(f"img[{ry1}:{ry2}, {rx1}:{rx2}]")
        print(f"OCR结果: {result}")
        # 在图上画出框选区域
        overlay = img_display.copy()
        sx0,sy0 = int(rx1*SCALE), int(ry1*SCALE)
        sx1,sy1 = int(rx2*SCALE), int(ry2*SCALE)
        cv2.rectangle(overlay, (sx0,sy0), (sx1,sy1), (0,255,0), 2)
        label = f"[{rx1},{ry1}]-[{rx2},{ry2}]"
        cv2.putText(overlay, label, (sx0, sy0-6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0,255,0), 1)
        cv2.imshow(WIN, overlay)

WIN = "调试工具 | 拖拽框选区域 | S=重新截图 | Q=退出"
cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WIN, int(img_orig.shape[1]*SCALE), int(img_orig.shape[0]*SCALE))
cv2.setMouseCallback(WIN, mouse_cb)
cv2.imshow(WIN, img_display)
overlay = img_display.copy()

print("就绪，拖拽框选区域查看坐标和OCR结果")
while True:
    k = cv2.waitKey(20) & 0xFF
    if k == ord('q'):
        break
    elif k == ord('s'):
        print("重新截图...")
        img_orig = screenshot()
        img_display = cv2.resize(img_orig, (0,0), fx=SCALE, fy=SCALE)
        overlay = img_display.copy()
        cv2.imshow(WIN, overlay)
        print("截图完成")

cv2.destroyAllWindows()
