# -*- coding: utf-8 -*-
"""
ask_doubao.py — 桌宠调用脚本：用 Edge 打开网页版豆包（doubao.com），提问并取回回答。
用法: python ask_doubao.py <问题base64>
输出(stdout, 单行):
  ANSWER|<回答文件UTF-8路径>   成功
  NEED_LOGIN                  等登录超时
  ERROR|<原因>                失败
首次使用会弹出 Edge 窗口，需手动登录豆包一次（登录态保存在 profile 中，之后免登录）。
依赖：本机 python3 + `pip install selenium` + Edge + 本目录 msedgedriver.exe
"""
import sys, os, base64, time, subprocess, urllib.request

DEBUG_PORT = 9223
EDGE_EXE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
DOUBAO_URL = "https://www.doubao.com/chat/"
INPUT_SEL = "textarea[placeholder], div[contenteditable='true']"

def log(msg):
    try:
        with open(os.path.join(os.environ["APPDATA"], "DesktopPet", "doubao.log"), "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S") + " " + msg + "\n")
    except Exception:
        pass

def edge_alive():
    try:
        urllib.request.urlopen("http://127.0.0.1:" + str(DEBUG_PORT) + "/json/version", timeout=2)
        return True
    except Exception:
        return False

def ensure_edge(profile):
    """保活 Edge 不存在时用 subprocess 独立启动（带豆包 URL 直接加载）"""
    try:
        for f in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
            p = os.path.join(profile, f)
            if os.path.exists(p):
                os.remove(p)
    except Exception:
        pass
    subprocess.Popen([
        EDGE_EXE, "--user-data-dir=" + profile, "--remote-debugging-port=" + str(DEBUG_PORT),
        "--no-first-run", "--disable-search-engine-choice-screen",
        "--disable-blink-features=AutomationControlled",
        "--window-position=-32000,-32000", "--window-size=1280,900", "about:blank"],
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    for _ in range(50):
        if edge_alive():
            return True
        time.sleep(1)
    return edge_alive()

def wait_input(driver, timeout_s):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            el = driver.find_element("css selector", INPUT_SEL)
            if el is not None:
                return el
        except Exception:
            pass
        time.sleep(0.5)
    return None

def page_text(driver):
    try:
        return driver.execute_script("return document.body ? document.body.innerText : ''")
    except Exception:
        return ""

def send_question(driver, question):
    """发送问题并确认进入页面。先确认输入成功，Enter 无效则点发送按钮，最多重试 4 次"""
    for attempt in range(4):
        tb = wait_input(driver, 10)
        if tb is None:
            time.sleep(3)
            continue
        try:
            tb.click()
            time.sleep(0.3)
            tb.send_keys(question)
            time.sleep(0.8)
        except Exception as e:
            log("输入异常: " + str(e))
            time.sleep(3)
            continue

        # 发送：Enter，若输入框是 contenteditable 或 Enter 无效则点发送按钮兜底
        try:
            tb.send_keys(u"\ue007")
            time.sleep(0.5)
        except Exception:
            pass
        # 验证：问题出现在页面文本中（12 秒内）；出现则成功，否则点发送按钮再验证一次
        deadline = time.time() + 12
        ok = False
        while time.time() < deadline:
            time.sleep(0.5)
            if question in page_text(driver):
                ok = True
                break
        if not ok:
            try:
                btn = driver.find_element("css selector", "button[aria-label*='发送'], button[aria-label*='send']")
                btn.click()
            except Exception:
                pass
            deadline = time.time() + 8
            while time.time() < deadline:
                time.sleep(0.5)
                if question in page_text(driver):
                    ok = True
                    break
        if ok:
            return True
        log("发送后问题未出现（尝试 " + str(attempt + 1) + "）。页面文本尾部: " + page_text(driver)[-150:].replace("\n", " | "))
        time.sleep(8)
    return False

def try_extract_answer(full, before, question):
    """从最终页面文本中提取回答"""
    tail = ""
    qidx = full.rfind(question)
    if qidx >= 0:
        tail = full[qidx + len(question):]
    if not tail and len(full) > len(before):
        tail = full[len(before):]
    answer = tail
    for junk in ("快速", "解题答疑", "帮我写作", "图像生成", "音乐生成", "翻译", "PPT 生成", "视频生成", "更多",
                 "复制", "重新生成", "停止生成", "点赞", "踩", "举报", "检测到自动化"):
        if junk in answer:
            answer = answer.split(junk)[0]
    core = answer.strip()
    lines = answer.split("\n")
    while lines:
        last_line = lines[-1].strip()
        if len(last_line) <= 40 and not last_line.endswith(("。", "！", "：", ":", "；", ";", "～", "~")):
            lines.pop()
        else:
            break
    cleaned = "\n".join(lines).strip().lstrip(":： \n")
    return cleaned if cleaned else core.lstrip(":： \n")

def main():
    if len(sys.argv) < 2:
        print("ERROR|缺少问题参数")
        return
    try:
        question = base64.b64decode(sys.argv[1]).decode("utf-8")
    except Exception:
        print("ERROR|问题参数解码失败")
        return
    log("收到问题: " + question[:50])

    answer_file = os.path.join(os.environ["APPDATA"], "DesktopPet", "doubao_answer.txt")
    profile = os.path.join(os.environ["APPDATA"], "DesktopPet", "doubao_profile_edge")
    base = os.path.dirname(os.path.abspath(__file__))
    driver_path = os.path.join(base, "msedgedriver.exe")
    if not os.path.exists(driver_path):
        print("ERROR|缺少 msedgedriver.exe（请放在桌宠目录下）")
        return

    # 清理旧的 msedgedriver 残留
    try:
        os.system("taskkill /F /IM msedgedriver.exe >nul 2>nul")
    except Exception:
        pass

    # 总超时看门狗：防止浏览器/驱动异常导致永久挂起（240 秒强制退出）
    import threading
    def _watchdog():
        time.sleep(240)
        try:
            sys.stdout.write("ERROR|处理超时（浏览器异常），请重试\n")
            sys.stdout.flush()
        except Exception:
            pass
        os._exit(1)
    threading.Thread(target=_watchdog, daemon=True).start()

    # 保活 Edge：无则冷启动，有则复用
    if not edge_alive():
        if not os.path.exists(EDGE_EXE):
            print("ERROR|找不到 Edge")
            return
        # 清理半死/残留的保活 Edge（避免 profile 锁与端口占用导致新实例卡死；不影响用户日常 Edge）
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command",
                "Get-CimInstance Win32_Process -Filter \"Name='msedge.exe'\" | Where-Object { $_.CommandLine -like '*doubao_profile_edge*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"],
                timeout=20)
        except Exception:
            pass
        time.sleep(3)  # 等端口释放
        log("冷启动 Edge")
        if not ensure_edge(profile):
            print("ERROR|Edge 启动失败")
            return
    else:
        log("复用保活 Edge")

    from selenium import webdriver
    from selenium.webdriver.edge.options import Options
    from selenium.webdriver.edge.service import Service

    opts = Options()
    opts.add_experimental_option("debuggerAddress", "127.0.0.1:" + str(DEBUG_PORT))
    svc = Service(driver_path)
    driver = None
    try:
        driver = webdriver.Edge(service=svc, options=opts)
        driver.set_window_size(1280, 900)
        driver.set_page_load_timeout(30)
        try:
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            })
        except Exception:
            pass

        # 等待输入框（页面加载完成）；超时则重载一次
        # 连接后总是 get 重载：Selenium 阻塞等待页面加载完成，保证 JS 就绪（直接发送会因 JS 未绑定而无效）
        try:
            driver.get(DOUBAO_URL)
        except Exception:
            pass
        if wait_input(driver, 30) is None:
            try:
                driver.get(DOUBAO_URL)
            except Exception:
                pass
            if wait_input(driver, 30) is None:
                print("ERROR|页面加载超时（网络慢或页面异常）")
                return
        log("页面标题: " + str(driver.title))

        # 登录检测：未登录则把窗口移到可见位置让用户登录（登录后自动隐藏到屏外）
        def _need_login():
            try:
                return len(driver.find_elements("xpath", "//button[contains(text(),'登录')] | //a[contains(text(),'登录')]")) > 0
            except Exception:
                return False

        if _need_login():
            try:
                driver.set_window_position(150, 100)
                driver.set_window_size(1280, 900)
            except Exception:
                pass
            log("检测到未登录，已显示窗口等待登录")
            deadline = time.time() + 180
            while time.time() < deadline:
                if not _need_login():
                    break
                time.sleep(3)
            else:
                log("等待登录超时，窗口保留")
                print("NEED_LOGIN")
                return
            log("登录成功")
        # 隐藏到屏幕外（用户不可见）
        try:
            driver.set_window_position(-32000, -32000)
        except Exception:
            pass
        log("豆包窗口已隐藏")

        # 等页面 JS 就绪（冷启动时输入框 DOM 出现但 JS 可能未绑定，直接发送会无效）
        time.sleep(6)

        # 发送问题（含验证重试）
        if not send_question(driver, question):
            print("ERROR|发送问题失败（页面可能异常，稍后再试）")
            return
        before = page_text(driver)

        # 等待回答（最多 120 秒，6 秒无变化视为完成）
        last = before
        stable = 0
        deadline = time.time() + 120
        wind_risk = False
        while time.time() < deadline:
            time.sleep(0.5)
            cur = page_text(driver)
            if not cur:
                continue
            if "检测到自动化" in cur or "自动化软件" in cur:
                log("页面出现风控提示")
                wind_risk = True
                break
            if cur != last:
                last = cur
                stable = 0
            else:
                stable += 1
                if stable >= 12:
                    break
        if wind_risk:
            print("ERROR|豆包检测到自动化操作，本次未回答（偶发风控，稍后再试）")
            return
        if stable < 12:
            log("等待回答提前结束（可能风控或页面异常）")
            print("ERROR|豆包未完成回答（可能被风控，稍后再试）")
            return

        answer = try_extract_answer(last, before, question)
        if len(answer) < 5:
            print("ERROR|未获取到回答（可能被风控或页面异常）")
            return
        try:
            with open(answer_file, "w", encoding="utf-8") as f:
                f.write(answer)
        except Exception as e:
            print("ERROR|写入回答失败: " + str(e))
            return
        log("回答长度: " + str(len(answer)))
        print("ANSWER|" + answer_file)
    except Exception as e:
        log("异常: " + str(e))
        print("ERROR|" + str(e)[:150])
    finally:
        # 不调用 driver.quit()：避免关闭 Edge（保留可复用）；msedgedriver 由下次运行清理
        pass

if __name__ == "__main__":
    main()
