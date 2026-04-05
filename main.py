import subprocess, time, random, cv2, numpy as np, pytesseract, io, threading, datetime, sys, os, re
from PIL import Image
import tkinter as tk
from tkinter import scrolledtext

# ── 路径（支持打包后运行）────────────────────────────
def resource_path(rel):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)

# ── 配置 ──────────────────────────────────────────────
pytesseract.pytesseract.tesseract_cmd = resource_path(r"Tesseract-OCR\tesseract.exe")
ADB_PATH = r"D:\MuMuPlayerGlobal\nx_device\12.0\shell\adb.exe"
DEVICE   = "172.26.18.222:5555"

TPL_TAKEOFF     = cv2.imread(resource_path("templates/takeoff_icon.png"))
TPL_LANDING     = cv2.imread(resource_path("templates/landing_icon.png"))
TPL_MAINTENANCE = cv2.imread(resource_path("templates/maintenance_icon.png"))
TPL_DEICE       = cv2.imread(resource_path("templates/deice_icon.png"))

# ── GUI 颜色 ──────────────────────────────────────────
BG, PANEL, ACCENT = "#1a1a2e", "#16213e", "#0f3460"
GREEN, YELLOW, RED, WHITE, GRAY = "#4ecca3", "#f5a623", "#e94560", "#eaeaea", "#888888"

# ── ADB / 截图 ────────────────────────────────────────
def adb_run(cmd_list):
    subprocess.run([ADB_PATH, "-s", DEVICE] + cmd_list, capture_output=True,
                   creationflags=subprocess.CREATE_NO_WINDOW)

def screenshot():
    r = subprocess.run([ADB_PATH, "-s", DEVICE, "exec-out", "screencap", "-p"],
                       capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    return cv2.cvtColor(np.array(Image.open(io.BytesIO(r.stdout))), cv2.COLOR_RGB2BGR)

def tap_area(x1, y1, x2, y2):
    x = random.randint(x1, x2) + random.randint(-2, 2)
    y = random.randint(y1, y2) + random.randint(-2, 2)
    adb_run(["shell", "input", "tap", str(x), str(y)])
    time.sleep(random.uniform(0.7, 1.2) + random.uniform(-0.5, 0.5))

def click_yellow_btn(): tap_area(100, 960, 355, 1000)

def scroll_down():
    x1 = random.randint(1600, 1640); x2 = x1 + random.randint(-20, 20)
    adb_run(["shell", "input", "swipe", str(x1), str(random.randint(750,850)),
             str(x2), str(random.randint(150,250)), str(random.randint(400,700))])
    time.sleep(random.uniform(1.2, 1.8))

def scroll_up():
    x1 = random.randint(1600, 1640); x2 = x1 + random.randint(-20, 20)
    adb_run(["shell", "input", "swipe", str(x1), str(random.randint(150,250)),
             str(x2), str(random.randint(800,1000)), str(random.randint(400,700))])
    time.sleep(random.uniform(1.2, 1.8))

def random_swipe():
    x1,y1 = random.randint(500,1400), random.randint(200,900)
    x2 = max(500,min(1400, x1+random.randint(-300,300)))
    y2 = max(200,min(900,  y1+random.randint(-200,200)))
    xm = (x1+x2)//2+random.randint(-80,80); ym = (y1+y2)//2+random.randint(-80,80)
    dur = random.randint(300,800)
    adb_run(["shell","input","swipe",str(x1),str(y1),str(xm),str(ym),str(dur//2)])
    time.sleep(0.05)
    adb_run(["shell","input","swipe",str(xm),str(ym),str(x2),str(y2),str(dur//2)])
    time.sleep(random.uniform(0.3,0.8))

# ── 货币 OCR ──────────────────────────────────────────
# 1920×1080 截图坐标（根据截图实测）
# 银色硬币数字区域
_SILVER_ROI = (950, 21, 1075, 55)   # x1,y1,x2,y2
# 绿色货币数字区域
_GREEN_ROI  = (1078, 13, 1255, 58)

def _ocr_number(img, roi):
    x1,y1,x2,y2 = roi
    crop = img[y1:y2, x1:x2]
    big  = cv2.resize(crop, (0,0), fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(big, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY)
    text = pytesseract.image_to_string(thresh, config="--psm 7 -l eng digits").strip()
    digits = re.sub(r'[^\d]', '', text)
    return int(digits) if digits else None

def read_currency(img):
    """返回 (silver, green)，任一失败返回 None"""
    s = _ocr_number(img, _SILVER_ROI)
    g = _ocr_number(img, _GREEN_ROI)
    if s is not None and g is not None:
        return s, g
    return None

# ── OCR ───────────────────────────────────────────────
def read_btn_text(img):
    btn = img[957:1000, 74:373]
    big = cv2.resize(btn,(0,0),fx=3,fy=3)
    gray = cv2.cvtColor(big, cv2.COLOR_BGR2GRAY)
    _,thresh = cv2.threshold(gray,80,255,cv2.THRESH_BINARY)
    return pytesseract.image_to_string(thresh, config="--psm 7 -l chi_sim").strip()

def has_yellow_btn(img):
    hsv = cv2.cvtColor(img[957:1000,74:373], cv2.COLOR_BGR2HSV)
    return np.sum(cv2.inRange(hsv, np.array([20,150,150]), np.array([35,255,255]))) > 2000

def is_green_at(img, x, y, r=8):
    reg = img[max(0,y-r):y+r, max(0,x-r):x+r]
    if reg.size == 0: return False
    hsv = cv2.cvtColor(reg, cv2.COLOR_BGR2HSV)
    return np.sum(cv2.inRange(hsv, np.array([40,100,100]), np.array([80,255,255]))) > 50

def has_red_at(img, x1, y1, x2, y2):
    hsv = cv2.cvtColor(img[y1:y2,x1:x2], cv2.COLOR_BGR2HSV)
    m1 = cv2.inRange(hsv, np.array([0,150,150]),   np.array([10,255,255]))
    m2 = cv2.inRange(hsv, np.array([170,150,150]), np.array([180,255,255]))
    return np.sum(m1)+np.sum(m2) > 100

def has_pink_red_at(img, x1, y1, x2, y2):
    """检测粉红/玫瑰红系（低饱和度红色），用于地勤不足警告"""
    hsv = cv2.cvtColor(img[y1:y2,x1:x2], cv2.COLOR_BGR2HSV)
    # 覆盖粉红背景(低饱和)和深玫瑰红文字(中饱和)，色相 0-15 和 165-180
    m1 = cv2.inRange(hsv, np.array([0,  30, 150]), np.array([15, 255, 255]))
    m2 = cv2.inRange(hsv, np.array([165, 30, 150]), np.array([180,255, 255]))
    return np.sum(m1)+np.sum(m2) > 200

# ── 扫描 ──────────────────────────────────────────────
def find_icons(img, template):
    if template is None: return []
    region = img[:, 1570:1680]
    res = cv2.matchTemplate(region, template, cv2.TM_CCOEFF_NORMED)
    locs = np.where(res >= 0.68)
    if len(locs[0]) == 0: return []
    pts = sorted(zip(locs[0], locs[1]))
    filtered = []
    for py,px in pts:
        if all(abs(py-fy)>30 for fy,fx in filtered): filtered.append((py,px))
    th,tw = template.shape[:2]
    return [(px+1570+tw//2, py+th//2) for py,px in filtered]

def has_alert(img, cx, cy):
    ay = cy-38
    reg = img[max(0,ay-20):ay+20, max(0,cx-15):cx+15]
    hsv = cv2.cvtColor(reg, cv2.COLOR_BGR2HSV)
    return np.sum(cv2.inRange(hsv, np.array([20,150,150]), np.array([35,255,255]))) > 50

def find_available_stand(img):
    stands = [(311,931),(406,931),(501,931),(591,931),(686,931)]
    avail = []
    for i,(sx,sy) in enumerate(stands):
        card = img[sy-30:sy+30, sx-42:sx+42]
        if card.size == 0: continue
        gray = cv2.cvtColor(card, cv2.COLOR_BGR2GRAY)
        mean = np.mean(gray)
        hsv  = cv2.cvtColor(card, cv2.COLOR_BGR2HSV)
        has_green = np.sum(cv2.inRange(hsv, np.array([40,80,80]), np.array([80,255,255]))) > 100
        if mean > 80 and not has_green:
            avail.append((sx,sy))
    return random.choice(avail) if avail else None

# ── 发呆 ──────────────────────────────────────────────
_idle_start = time.time(); _idle_budget = random.uniform(30,60); _idle_used = 0.0

def maybe_idle(log_fn=None):
    global _idle_start, _idle_budget, _idle_used
    now = time.time()
    if now - _idle_start > 300:
        _idle_start = now; _idle_budget = random.uniform(30,60); _idle_used = 0.0; return
    if _idle_used >= _idle_budget: return
    if random.random() < 0.15:
        t = min(random.uniform(1.0,5.0), _idle_budget-_idle_used)
        if t > 0.5:
            msg = f"[发呆 {t:.1f}s]"
            if log_fn: log_fn(msg)
            time.sleep(t); _idle_used += t

# ── 分支 ──────────────────────────────────────────────
def takeoff_branch(log):
    log("  → 起飞分支")
    last_btn = ""; repeat = 0; t0 = time.time()
    for step in range(10):
        if time.time()-t0 > 40: log("    超时退出"); break
        img = screenshot(); btn = read_btn_text(img)
        log(f"    起飞[{step}] 按钮:'{btn}'")
        if btn == last_btn:
            repeat += 1
            if repeat >= 2: log("    按钮重复，退出"); adb_run(["shell","input","keyevent","4"]); break
        else: repeat = 0; last_btn = btn

        if any(k in btn for k in ["升级合约","升级"]) and "奖励" not in btn:
            log("    检测到升级合约弹窗，点击领取奖励并升级")
            tap_area(820,670,970,705); time.sleep(1.5); last_btn=""; repeat=0
        elif any(k in btn for k in ["滑行至跑道","滑行","跑道","疹行","跑起","至跑","行至"]):
            log("    检测到滑行至跑道，点击黄键再确认")
            if not has_yellow_btn(img):
                log("    无黄色按钮，跳过"); adb_run(["shell","input","keyevent","4"]); break
            click_yellow_btn(); time.sleep(1.5)
            tap_area(618, 656, 905, 705); time.sleep(1.5); last_btn=""; repeat=0
        elif any(k in btn for k in ["奖励"]):
            log("    点击领取奖励按钮")
            click_yellow_btn(); time.sleep(3.0)
            for _ in range(5):
                log("    点击奖励弹窗（领取/升级）")
                tap_area(820,670,970,705); time.sleep(1.5)
                img3 = screenshot()
                # 检测"领取奖励并延期"按钮
                popup_crop = img3[656:705, 618:905]
                popup_big  = cv2.resize(popup_crop, (0,0), fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
                popup_gray = cv2.cvtColor(popup_big, cv2.COLOR_BGR2GRAY)
                _, popup_thresh = cv2.threshold(popup_gray, 140, 255, cv2.THRESH_BINARY)
                popup_text = pytesseract.image_to_string(popup_thresh, config="--psm 7 -l chi_sim").strip()
                log(f"    弹窗检测:'{popup_text}'")
                if any(k in popup_text for k in ["领取奖励并延期","领取","延期"]):
                    log("    检测到领取奖励并延期，点击")
                    tap_area(618, 656, 905, 705); time.sleep(1.5)
                    img3 = screenshot()
                btn3 = read_btn_text(img3)
                log(f"    奖励后按钮:'{btn3}'")
                if not any(k in btn3 for k in ["升级","取消","奖励"]):
                    break
            last_btn=""; repeat=0
        elif not has_yellow_btn(img):
            log("    无黄色按钮，起飞分支结束"); break
        else:
            log(f"    点击按钮:'{btn}'"); click_yellow_btn()
        time.sleep(random.uniform(1.0,2.0))

def landing_branch(log):
    log("  → 降落分支")
    last_btn = ""; repeat = 0; t0 = time.time()
    for step in range(8):
        if time.time()-t0 > 40: log("    超时退出"); adb_run(["shell","input","keyevent","4"]); break
        img = screenshot(); btn = read_btn_text(img)
        log(f"    降落[{step}] 按钮:'{btn}'")

        # 检测小游戏弹窗：OCR 识别弹窗标题区域
        mg_crop = img[730:788, 486:603]
        mg_big  = cv2.resize(mg_crop, (0,0), fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        mg_gray = cv2.cvtColor(mg_big, cv2.COLOR_BGR2GRAY)
        mg_inv  = cv2.bitwise_not(mg_gray)
        _, mg_thresh = cv2.threshold(mg_inv, 180, 255, cv2.THRESH_BINARY)
        mg_text = pytesseract.image_to_string(mg_thresh, config="--psm 7 -l chi_sim").strip()
        log(f"    小游戏检测:'{mg_text}'")
        if "小游戏" in mg_text or "小游" in mg_text:
            log("    检测到小游戏弹窗，点击 ⓘ 关闭")
            tap_area(415, 878, 450, 908)
            time.sleep(1.0)
            continue

        if btn == last_btn:
            repeat += 1
            if repeat >= 2: log("    按钮重复，退出"); adb_run(["shell","input","keyevent","4"]); break
        else: repeat = 0; last_btn = btn

        if any(k in btn for k in ["延长合约","延长","延期"]):
            log("    检测到延长合约，点击确认")
            tap_area(618, 656, 905, 705); time.sleep(1.5)
            last_btn=""; repeat=0; continue
        elif any(k in btn for k in ["滑行至跑道","滑行","跑道","疹行","跑起","至跑","行至"]):
            log("    检测到滑行至跑道，点击黄键再确认")
            if not has_yellow_btn(img):
                log("    无黄色按钮，跳过"); adb_run(["shell","input","keyevent","4"]); return True
            click_yellow_btn(); time.sleep(1.5)
            tap_area(618, 656, 905, 705); time.sleep(1.5)
            last_btn=""; repeat=0; continue
        elif any(k in btn for k in ["停机位","机位","停机"]):
            popup = img[455:500,255:450]
            if np.mean(cv2.cvtColor(popup,cv2.COLOR_BGR2GRAY)) < 55:
                log("    点击选择停机位按钮"); click_yellow_btn(); time.sleep(1.2); img = screenshot()
            stand = find_available_stand(img)
            if stand:
                log(f"    选择空置机位 {stand}")
                tap_area(stand[0]-30,stand[1]-20,stand[0]+30,stand[1]+20)
                time.sleep(0.8); log("    点击确认"); click_yellow_btn(); time.sleep(1)
            else:
                log("    无空置机位，跳过此飞机")
                adb_run(["shell","input","keyevent","4"]); return False
        elif not has_yellow_btn(img):
            log("    无黄色按钮，降落分支结束"); break
        else:
            log(f"    点击按钮:'{btn}'"); click_yellow_btn()
        time.sleep(random.uniform(1.0,2.0))
    return True

def ground_branch(log):
    log("  → 地勤分支")
    img = screenshot(); btn = read_btn_text(img)
    log(f"    按钮:'{btn}'")
    if not any(k in btn for k in ["地勤","指派","指泊","指半","指闭","惑人","地惑","人员","保障","开始"]):
        log("    不是地勤界面，跳过"); return False
    for i in range(15):
        img2 = screenshot()
        if is_green_at(img2,900,695): log(f"    滑块到位（{i}次点击）"); break
        plus = img2[670:705,955:985]
        if np.mean(cv2.cvtColor(plus,cv2.COLOR_BGR2GRAY)) < 60:
            log("    加号不可用，人数不足，跳过")
            adb_run(["shell","input","keyevent","4"]); return False
        log(f"    点击加号 ({i+1})"); tap_area(960,680,980,700)
    else:
        log("    滑块未到位，跳过"); adb_run(["shell","input","keyevent","4"]); return False
    log("    点击机坪代理开关"); tap_area(940,773,956,787); time.sleep(0.8)
    img3 = screenshot()
    if not is_green_at(img3,948,780):
        log("    机坪代理未开启，跳过"); adb_run(["shell","input","keyevent","4"]); return False
    log("    机坪代理已开启，点击指派地勤人员"); click_yellow_btn(); return True

def deice_branch(log):
    log("  → 除冰分支")
    last_btn = ""; repeat = 0; t0 = time.time()
    for step in range(8):
        if time.time()-t0 > 40: log("    超时退出"); break
        img = screenshot(); btn = read_btn_text(img)
        log(f"    除冰[{step}] 按钮:'{btn}'")
        if btn == last_btn:
            repeat += 1
            if repeat >= 2: log("    按钮重复，退出"); adb_run(["shell","input","keyevent","4"]); break
        else: repeat = 0; last_btn = btn

        if not has_yellow_btn(img):
            log("    无黄色按钮，除冰分支结束"); break
        else:
            log(f"    点击按钮:'{btn}'"); click_yellow_btn()
        time.sleep(random.uniform(1.0, 2.0))

# ── 主循环 ────────────────────────────────────────────
def bot_loop(gui):
    loop = 0
    while gui.running:
        loop += 1
        while gui.paused: time.sleep(0.5)
        gui.log(f"\n{'─'*40}")
        gui.log(f"[第{loop}轮] {datetime.datetime.now().strftime('%H:%M:%S')} 开始扫描")
        gui.set_action("滚动到顶部...")
        scroll_up()
        scroll_up()
        scroll_up()
        found_any = False

        # 读取货币
        try:
            cur = read_currency(screenshot())
            if cur:
                gui.log(f"  货币识别: 银={cur[0]:,}  绿={cur[1]:,}")
                gui.update_currency(cur[0], cur[1])
            else:
                gui.log("  货币识别: 失败")
        except Exception as e:
            gui.log(f"  货币识别异常: {e}")

        for scroll_i in range(3):
            if not gui.running: break
            gui.set_action(f"扫描第{scroll_i+1}屏...")
            time.sleep(0.5)
            img = screenshot()
            processed = True
            while processed and gui.running:
                processed = False
                for tpl, ptype, pname in [
                    (TPL_TAKEOFF,     "起飞", "takeoff"),
                    (TPL_LANDING,     "降落", "landing"),
                    (TPL_MAINTENANCE, "地勤", "ground"),
                    (TPL_DEICE,       "除冰", "deice"),
                ]:
                    for cx,cy in find_icons(img, tpl):
                        if not gui.running: break
                        alert_y = cy-38
                        if alert_y < 20: continue
                        if not has_alert(img,cx,cy): continue
                        img2 = screenshot()
                        if not has_alert(img2,cx,cy):
                            gui.log(f"  确认截图无感叹号，跳过 ({cx},{alert_y})")
                            continue
                        found_any = True
                        processed = True
                        gui.log(f"  ✈ 发现 [{ptype}] 飞机，感叹号位置 ({cx},{alert_y})")
                        gui.set_action(f"处理 {ptype} 飞机...")
                        tap_area(cx-5,alert_y-5,cx+5,alert_y+5)
                        time.sleep(1.5)
                        if ptype == "起飞":
                            takeoff_branch(gui.log)
                        elif ptype == "降落":
                            landing_branch(gui.log)
                        elif ptype == "地勤":
                            ground_branch(gui.log)
                        elif ptype == "除冰":
                            deice_branch(gui.log)
                        gui.inc_stat(pname)
                        gui.log(f"  ✓ [{ptype}] 处理完成")
                        # 处理完立即重新截图
                        time.sleep(0.5)
                        img = screenshot()
                        break  # 重新从头扫描
                    if processed: break

            if scroll_i < 2 and gui.running:
                gui.log(f"  向下滚动列表..."); scroll_down()

        if not found_any:
            gui.log(f"[第{loop}轮] 无待处理飞机，随机浏览地图")
            gui.set_action("随机浏览地图...")
            for _ in range(random.randint(2,4)):
                if not gui.running: break
                random_swipe()
                maybe_idle(gui.log)
            time.sleep(random.uniform(2.0,4.0))
        else:
            maybe_idle(gui.log)
        time.sleep(random.uniform(1.5,2.5))

# ── GUI ───────────────────────────────────────────────
class WoaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("World of Airports Bot")
        self.root.configure(bg=BG)
        self.root.geometry("720x680")
        self.root.resizable(False, False)
        self.running = False
        self.paused  = False
        # 计时器状态
        self._timer_running = False
        self._elapsed = 0.0
        self._timer_start = None
        # 统计
        self._takeoff_count = 0
        self._silver_base = None
        self._green_base  = None
        self._silver_cur  = 0
        self._green_cur   = 0
        self._build_ui()
        self._tick()

    def _build_ui(self):
        tk.Label(self.root, text="✈  World of Airports Bot",
                 font=("Helvetica",18,"bold"), bg=BG, fg=GREEN).pack(pady=(16,2))

        self.status_var = tk.StringVar(value="● 待机")
        tk.Label(self.root, textvariable=self.status_var,
                 font=("Helvetica",10), bg=BG, fg=GRAY).pack()

        # 当前动作
        af = tk.Frame(self.root, bg=PANEL); af.pack(fill="x", padx=20, pady=(8,0))
        tk.Label(af, text="当前动作", font=("Helvetica",8), bg=PANEL, fg=GRAY).pack(anchor="w", padx=10, pady=(4,0))
        self.action_var = tk.StringVar(value="—")
        tk.Label(af, textvariable=self.action_var, font=("Helvetica",11,"bold"),
                 bg=PANEL, fg=YELLOW, wraplength=660, justify="left").pack(anchor="w", padx=10, pady=(0,6))

        # 统计面板：计时 + 起飞 + 银币 + 绿币
        sf = tk.Frame(self.root, bg=BG); sf.pack(fill="x", padx=20, pady=(6,0))

        # 计时器卡片
        tf = tk.Frame(sf, bg=PANEL, width=160, height=72); tf.pack(side="left", padx=4, expand=True, fill="x"); tf.pack_propagate(False)
        tk.Label(tf, text="运行时间", font=("Helvetica",8), bg=PANEL, fg=GRAY).pack(pady=(6,0))
        self.timer_var = tk.StringVar(value="00:00:00")
        tk.Label(tf, textvariable=self.timer_var, font=("Consolas",16,"bold"), bg=PANEL, fg=WHITE).pack()

        # 起飞次数
        cf = tk.Frame(sf, bg=PANEL, width=160, height=72); cf.pack(side="left", padx=4, expand=True, fill="x"); cf.pack_propagate(False)
        tk.Label(cf, text="起飞次数", font=("Helvetica",8), bg=PANEL, fg=GRAY).pack(pady=(6,0))
        self.takeoff_var = tk.StringVar(value="0")
        tk.Label(cf, textvariable=self.takeoff_var, font=("Helvetica",18,"bold"), bg=PANEL, fg=GREEN).pack()

        # 银币收入
        svf = tk.Frame(sf, bg=PANEL, width=160, height=72); svf.pack(side="left", padx=4, expand=True, fill="x"); svf.pack_propagate(False)
        tk.Label(svf, text="⊙ 银币收入", font=("Helvetica",8), bg=PANEL, fg=GRAY).pack(pady=(6,0))
        self.silver_var = tk.StringVar(value="+0")
        tk.Label(svf, textvariable=self.silver_var, font=("Helvetica",16,"bold"), bg=PANEL, fg="#c0c0c0").pack()

        # 绿币收入
        gvf = tk.Frame(sf, bg=PANEL, width=160, height=72); gvf.pack(side="left", padx=4, expand=True, fill="x"); gvf.pack_propagate(False)
        tk.Label(gvf, text="G 绿币收入", font=("Helvetica",8), bg=PANEL, fg=GRAY).pack(pady=(6,0))
        self.green_var = tk.StringVar(value="+0")
        tk.Label(gvf, textvariable=self.green_var, font=("Helvetica",16,"bold"), bg=PANEL, fg="#4ecca3").pack()

        # 计时器按钮行
        tbf = tk.Frame(self.root, bg=BG); tbf.pack(pady=(8,0))
        self.timer_start_btn = tk.Button(tbf, text="⏱ 开始计时", width=10, font=("Helvetica",10,"bold"),
            bg=GREEN, fg=BG, relief="flat", command=self.timer_start)
        self.timer_start_btn.pack(side="left", padx=6)
        self.timer_pause_btn = tk.Button(tbf, text="⏸ 暂停计时", width=10, font=("Helvetica",10,"bold"),
            bg=ACCENT, fg=WHITE, relief="flat", state="disabled", command=self.timer_pause)
        self.timer_pause_btn.pack(side="left", padx=6)
        self.timer_reset_btn = tk.Button(tbf, text="↺ 归零", width=10, font=("Helvetica",10,"bold"),
            bg="#444466", fg=WHITE, relief="flat", command=self.timer_reset)
        self.timer_reset_btn.pack(side="left", padx=6)

        # 日志
        lf = tk.Frame(self.root, bg=PANEL); lf.pack(fill="both", expand=True, padx=20, pady=(8,0))
        tk.Label(lf, text="详细日志", font=("Helvetica",8), bg=PANEL, fg=GRAY).pack(anchor="w", padx=8, pady=(4,0))
        self.log_box = scrolledtext.ScrolledText(lf, bg="#0d0d1a", fg=WHITE,
            font=("Consolas",8), bd=0, relief="flat", state="disabled", height=14)
        self.log_box.pack(fill="both", expand=True, padx=8, pady=(0,8))

        # Bot 控制按钮
        bf = tk.Frame(self.root, bg=BG); bf.pack(pady=10)
        self.start_btn = tk.Button(bf, text="▶  开始", width=10, font=("Helvetica",11,"bold"),
            bg=GREEN, fg=BG, relief="flat", command=self.start)
        self.start_btn.pack(side="left", padx=8)
        self.pause_btn = tk.Button(bf, text="⏸  暂停", width=10, font=("Helvetica",11,"bold"),
            bg=ACCENT, fg=WHITE, relief="flat", state="disabled", command=self.toggle_pause)
        self.pause_btn.pack(side="left", padx=8)
        self.stop_btn = tk.Button(bf, text="■  终止", width=10, font=("Helvetica",11,"bold"),
            bg=RED, fg=WHITE, relief="flat", state="disabled", command=self.stop)
        self.stop_btn.pack(side="left", padx=8)

    # ── 计时器逻辑 ──
    def _tick(self):
        if self._timer_running:
            elapsed = self._elapsed + (time.time() - self._timer_start)
            h = int(elapsed // 3600)
            m = int((elapsed % 3600) // 60)
            s = int(elapsed % 60)
            self.timer_var.set(f"{h:02d}:{m:02d}:{s:02d}")
        self.root.after(500, self._tick)

    def timer_start(self):
        if self._timer_running: return
        self._timer_running = True
        self._timer_start = time.time()
        self.timer_start_btn.config(state="disabled")
        self.timer_pause_btn.config(state="normal")

    def timer_pause(self):
        if self._timer_running:
            self._elapsed += time.time() - self._timer_start
            self._timer_running = False
            self.timer_pause_btn.config(text="▶ 继续计时")
        else:
            self._timer_running = True
            self._timer_start = time.time()
            self.timer_pause_btn.config(text="⏸ 暂停计时")

    def timer_reset(self):
        self._timer_running = False
        self._elapsed = 0.0
        self._timer_start = None
        self._silver_base = None
        self._green_base  = None
        self._takeoff_count = 0
        self.timer_var.set("00:00:00")
        self.takeoff_var.set("0")
        self.silver_var.set("+0")
        self.green_var.set("+0")
        self.timer_start_btn.config(state="normal")
        self.timer_pause_btn.config(state="disabled", text="⏸ 暂停计时")

    # ── 货币更新 ──
    def update_currency(self, silver, green):
        def _do():
            if self._silver_base is None:
                self._silver_base = silver
                self._green_base  = green
            ds = silver - self._silver_base
            dg = green  - self._green_base
            self.silver_var.set(f"{'+' if ds>=0 else ''}{ds:,}")
            self.green_var.set(f"{'+' if dg>=0 else ''}{dg:,}")
        self.root.after(0, _do)

    # ── 日志 / 状态 ──
    def log(self, msg):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        def _do():
            self.log_box.config(state="normal")
            self.log_box.insert("end", f"[{ts}] {msg}\n")
            self.log_box.see("end")
            self.log_box.config(state="disabled")
        self.root.after(0, _do)

    def set_action(self, msg): self.root.after(0, lambda: self.action_var.set(msg))
    def set_status(self, msg): self.root.after(0, lambda: self.status_var.set(msg))

    def inc_stat(self, key):
        if key == "takeoff":
            def _do():
                self._takeoff_count += 1
                self.takeoff_var.set(str(self._takeoff_count))
            self.root.after(0, _do)

    # ── Bot 控制 ──
    def start(self):
        if self.running: return
        self.running = True; self.paused = False
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal")
        self.stop_btn.config(state="normal")
        self.set_status("● 运行中")
        self.log("=== 脚本启动 ===")
        threading.Thread(target=self._run, daemon=True).start()

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.pause_btn.config(text="▶  继续"); self.set_status("⏸ 已暂停"); self.log("[暂停]")
        else:
            self.pause_btn.config(text="⏸  暂停"); self.set_status("● 运行中"); self.log("[继续]")

    def stop(self):
        self.running = False; self.paused = False
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled", text="⏸  暂停")
        self.stop_btn.config(state="disabled")
        self.set_status("● 待机"); self.set_action("—"); self.log("=== 脚本终止 ===")

    def _run(self):
        try:
            bot_loop(self)
        except Exception as e:
            self.log(f"[错误] {e}")
            import traceback; self.log(traceback.format_exc())
            self.stop()

if __name__ == "__main__":
    root = tk.Tk()
    app = WoaGUI(root)
    root.mainloop()
