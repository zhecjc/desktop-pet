# -*- coding: utf-8 -*-
"""
ask_doubao.py — 桌宠调用脚本：用 Edge 打开网页版豆包（doubao.com），提问并取回回答。
用法: python ask_doubao.py <问题base64>
输出(stdout, 单行):
  ANSWER|<回答文件UTF-8路径>   成功
  NEED_LOGIN                  需要登录（窗口已显示等待登录）
  ERROR|<原因>                失败

流程要点：
- Edge 窗口默认启动在屏幕外（-32000,-32000），用户全程看不到豆包界面；
- 附带防后台节流参数，保证窗口在屏幕外时页面仍正常渲染、输入/发送/回答照常工作；
- 检测到未登录时自动把窗口移到可见位置供扫码/登录，登录后自动隐藏并重载页面；
- 同一保活会话连续提问 = 多轮上下文（可追问）；
- 输入用 send_keys，失败自动切换 JS 原生 setter 重试；Enter 无效则点发送按钮；
- 关闭旧保活 Edge 时先优雅关闭（保留会话 cookie），再兜底强杀。

依赖：本机 python3 + `pip install selenium` + Edge + 本目录 msedgedriver.exe
"""
import sys, os, base64, time, subprocess, urllib.request, threading

DEBUG_PORT = 9223
EDGE_EXE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
DOUBAO_URL = "https://www.doubao.com/chat/"
INPUT_SEL = "textarea[placeholder]"
PROFILE_NAME = "doubao_profile_edge"

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

def stop_keepalive_edge():
    """优雅关闭旧保活 Edge（保留登录态）：先发 WM_CLOSE，超时再强杀。不影响用户日常 Edge。"""
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='msedge.exe'\" | "
          "Where-Object { $_.CommandLine -like '*" + PROFILE_NAME + "*' }")
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps + " | ForEach-Object { $_.ProcessId }"],
            capture_output=True, text=True, timeout=20)
        pids = [p.strip() for p in (out.stdout or "").splitlines() if p.strip().isdigit()]
        for pid in pids:
            try:
                subprocess.run(["taskkill", "/PID", pid, "/T"],
                               capture_output=True, timeout=10)
            except Exception:
                pass
        time.sleep(6)
        subprocess.run(["powershell", "-NoProfile", "-Command",
            ps + " | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"],
            timeout=20)
    except Exception:
        pass
    time.sleep(2)

def ensure_edge(profile):
    """保活 Edge 不存在时冷启动（带豆包 URL 直接加载，窗口在屏幕外）"""
    for f in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
        p = os.path.join(profile, f)
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass
    subprocess.Popen([
        EDGE_EXE, "--user-data-dir=" + profile, "--remote-debugging-port=" + str(DEBUG_PORT),
        "--no-first-run", "--disable-search-engine-choice-screen",
        "--disable-blink-features=AutomationControlled",
        # 防止窗口在屏幕外/被遮挡时 Chromium 暂停渲染与定时器，保证问答正常
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-background-timer-throttling",
        "--disable-background-networking",
        "--window-position=-32000,-32000", "--window-size=1280,900", "about:blank"],
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    for _ in range(60):
        if edge_alive():
            return True
        time.sleep(1)
    return edge_alive()

def page_text(driver):
    try:
        return driver.execute_script("return document.body ? document.body.innerText : ''")
    except Exception:
        return ""

def find_input(driver, timeout_s=10):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            el = driver.find_element("css selector", INPUT_SEL)
            if el is not None and el.is_displayed():
                return el
        except Exception:
            pass
        time.sleep(0.5)
    return None

def need_login(driver):
    """判断当前是否未登录（豆包登录按钮文本在 span 内，需用 contains(.) 或 class 判断）"""
    try:
        for b in driver.find_elements("css selector", "button, a"):
            try:
                if not b.is_displayed():
                    continue
            except Exception:
                continue
            cls = (b.get_attribute("class") or "")
            txt = (b.get_attribute("innerText") or "").strip()
            if "login-btn" in cls.lower() or txt == "登录" or "登录" in txt[:8]:
                return True
    except Exception:
        pass
    return False

def send_question(driver, question):
    """发送问题并确认进入页面：send_keys -> 校验 value -> JS setter 兜底 -> Enter -> 点发送按钮兜底"""
    for attempt in range(4):
        tb = find_input(driver, 10)
        if tb is None:
            log("输入框未找到（尝试 " + str(attempt + 1) + "）")
            # 输入框都找不到说明页面已异常，提前判定失败，交给上层重启浏览器
            return False
        # 清空输入框残留内容（复用会话时上次失败的问题可能还留在框里）
        try:
            tb.click()
            time.sleep(0.2)
            tb.send_keys(u"\ue009", "a")  # Ctrl+A
            tb.send_keys(u"\ue017")       # Delete
            time.sleep(0.2)
        except Exception:
            pass

        # 输入：优先 send_keys，校验 value 为空则用 JS 原生 setter
        typed = False
        try:
            tb.click()
            time.sleep(0.3)
            tb.send_keys(question)
            time.sleep(0.8)
            val = driver.execute_script("return arguments[0].value", tb) or ""
            if val == question:
                typed = True
        except Exception as e:
            log("send_keys 异常: " + str(e))
        if not typed:
            try:
                driver.execute_script("""
                    var el = arguments[0];
                    el.focus();
                    var set = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
                    set.call(el, arguments[1]);
                    el.dispatchEvent(new InputEvent('input', {bubbles: true, data: arguments[1], inputType: 'insertText'}));
                """, tb, question)
                time.sleep(0.6)
                val = driver.execute_script("return arguments[0].value", tb) or ""
                typed = val == question
            except Exception as e:
                log("JS 输入异常: " + str(e))
        if not typed:
            log("输入未生效（尝试 " + str(attempt + 1) + "），页面可能异常")
            time.sleep(3)
            continue
        log("输入成功: " + question[:30])

        # 发送：Enter，无效则点发送按钮（class 含 send-msg-btn）
        sent = False
        text_before_send = page_text(driver)
        q_before = text_before_send.count(question)
        try:
            tb.send_keys(u"\ue007")
            deadline = time.time() + 10
            while time.time() < deadline:
                time.sleep(0.5)
                cur = page_text(driver)
                if question in cur and cur.count(question) > q_before:
                    sent = True
                    break
        except Exception as e:
            log("Enter 异常: " + str(e))
        if not sent:
            try:
                btns = driver.find_elements("css selector", "button[class*='send-msg-btn']")
                for b in btns:
                    try:
                        if b.is_displayed():
                            b.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", b)
                    break
                deadline = time.time() + 8
                while time.time() < deadline:
                    time.sleep(0.5)
                    cur = page_text(driver)
                    if question in cur and cur.count(question) > q_before:
                        sent = True
                        break
            except Exception as e:
                log("发送按钮异常: " + str(e))
        if sent:
            log("问题已发送")
            return True

        # 发送失败：可能是登录弹窗拦截，或页面异常
        if need_login(driver):
            log("发送时检测到未登录（尝试 " + str(attempt + 1) + "）")
            return "NEED_LOGIN"
        log("发送后问题未出现（尝试 " + str(attempt + 1) + "）。页面文本尾部: " + page_text(driver)[-150:].replace("\n", " | "))
        time.sleep(8)
    return False

def try_extract_answer(full, before, question):
    """从最终页面文本中提取回答：取问题最后一次出现之后的文本，截到消息操作按钮/推荐区为止"""
    tail = ""
    qidx = full.rfind(question)
    if qidx >= 0:
        tail = full[qidx + len(question):]
    if not tail and len(full) > len(before):
        tail = full[len(before):]
    answer = tail
    # 助手消息自带操作按钮（复制/重新生成/点赞…），其后通常是推荐内容或 UI，直接截断
    for junk in ("复制", "重新生成", "停止生成", "点赞", "踩", "举报",
                 "AI 生成可能有误", "注意核实",
                 "相关推荐", "相关视频", "相关文章", "猜你想问", "大家都在问", "相关问题", "更多推荐",
                 "以上内容由 AI 生成", "内容由 AI 生成", "展开全部", "点击展开",
                 "资讯：", "快速", "PPT 生成", "图像生成", "帮我写作", "视频生成",
                 "翻译", "深入研究", "录音转写", "更多", "专业版", "下载电脑版",
                 "检测到自动化", "自动化软件"):
        if junk in answer:
            answer = answer.split(junk)[0]
    # 去掉开头的"参考 N 篇资料 / 找到 N 篇资料 / 已为你搜索到"等搜索摘要行
    lines0 = answer.split("\n")
    while lines0:
        first = lines0[0].strip()
        if not first:
            lines0.pop(0)
            continue
        if (first.startswith("搜索") or first.startswith("参考") or first.startswith("找到")
                or first.startswith("已搜索") or first.startswith("已为你") or first.startswith("搜索到")) and len(first) <= 30:
            lines0.pop(0)
        else:
            break
    answer = "\n".join(lines0)
    core = answer.strip()
    lines = answer.split("\n")
    while lines:
        last_line = lines[-1].strip()
        # 末尾短行视为 UI/建议（除非以句末标点结尾，如答案的"。"）
        if len(last_line) <= 30 and not last_line.endswith(("。", "！", "～", "~", "…")):
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

    # 总超时看门狗：防止浏览器/驱动异常导致独立运行时永久挂起（540 秒强制退出）
    def _watchdog():
        time.sleep(540)
        try:
            sys.stdout.write("ERROR|处理超时（浏览器异常），请重试\n")
            sys.stdout.flush()
        except Exception:
            pass
        os._exit(1)
    threading.Thread(target=_watchdog, daemon=True).start()

    answer_file = os.path.join(os.environ["APPDATA"], "DesktopPet", "doubao_answer.txt")
    profile = os.path.join(os.environ["APPDATA"], "DesktopPet", PROFILE_NAME)
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

    from selenium import webdriver
    from selenium.webdriver.edge.options import Options
    from selenium.webdriver.edge.service import Service

    def attempt(cold_start):
        """执行一次完整问答。cold_start=True 时强制重启 Edge。返回 (状态, 附加信息)。"""
        driver = None
        try:
            if cold_start:
                stop_keepalive_edge()
                time.sleep(3)
                log("冷启动 Edge")
                if not ensure_edge(profile):
                    return ("ERROR", "Edge 启动失败")
            elif not edge_alive():
                # 无保活实例时也先清理旧实例：可能有其他端口的残留 Edge 占着 profile 锁
                stop_keepalive_edge()
                time.sleep(3)
                log("冷启动 Edge（无保活实例）")
                if not ensure_edge(profile):
                    return ("ERROR", "Edge 启动失败")
            else:
                log("复用保活 Edge")

            opts = Options()
            opts.add_experimental_option("debuggerAddress", "127.0.0.1:" + str(DEBUG_PORT))
            svc = Service(driver_path)
            driver = webdriver.Edge(service=svc, options=opts)
            driver.set_window_size(1280, 900)
            driver.set_page_load_timeout(30)
            try:
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
                })
            except Exception:
                pass

            # 复用保活会话时若页面还是豆包聊天页则直接使用（保留多轮上下文），否则重载
            try:
                cur = driver.current_url or ""
                on_doubao = ("doubao.com" in cur)
            except Exception:
                on_doubao = False
            if on_doubao and find_input(driver, 6) is not None:
                log("复用当前豆包会话（多轮上下文）")
            else:
                try:
                    driver.get(DOUBAO_URL)
                except Exception:
                    pass
                if find_input(driver, 30) is None:
                    try:
                        driver.get(DOUBAO_URL)
                    except Exception:
                        pass
                    if find_input(driver, 30) is None:
                        return ("ERROR", "页面加载超时（网络慢或页面异常）")
            log("页面标题: " + str(driver.title))

            # 登录检测：未登录则把窗口移到可见位置让用户登录（登录后自动隐藏）
            login_timeout = 180
            try:
                login_timeout = max(30, min(600, int(os.environ.get("DOUBAO_LOGIN_TIMEOUT", "180"))))
            except Exception:
                pass
            if need_login(driver):
                try:
                    driver.set_window_position(150, 100)
                    driver.set_window_size(1280, 900)
                except Exception:
                    pass
                log("检测到未登录，已显示窗口等待登录（" + str(login_timeout) + " 秒）")
                deadline = time.time() + login_timeout
                while time.time() < deadline:
                    if not need_login(driver):
                        break
                    time.sleep(3)
                if need_login(driver):
                    log("等待登录超时，窗口保留")
                    return ("NEED_LOGIN", "")
                log("登录成功")
                # 登录后重载页面，确保聊天输入组件就绪
                try:
                    driver.get(DOUBAO_URL)
                except Exception:
                    pass
                if find_input(driver, 30) is None:
                    return ("ERROR", "登录后页面加载异常")

            # 隐藏到屏幕外（用户不可见）
            try:
                driver.set_window_position(-32000, -32000)
            except Exception:
                pass
            log("豆包窗口已隐藏")
            time.sleep(3)

            # 发送问题（含验证重试）
            result = send_question(driver, question)
            if result == "NEED_LOGIN":
                try:
                    driver.set_window_position(150, 100)
                    driver.set_window_size(1280, 900)
                except Exception:
                    pass
                return ("NEED_LOGIN", "")
            if result is not True:
                return ("SEND_FAIL", "发送问题失败（页面可能异常）")

            before = page_text(driver)
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
                return ("ERROR", "豆包检测到自动化操作，本次未回答（偶发风控，稍后再试）")
            if stable < 12:
                log("等待回答提前结束（可能风控或页面异常）")
                return ("ERROR", "豆包未完成回答（可能被风控，稍后再试）")

            answer = try_extract_answer(last, before, question)
            if len(answer) < 5:
                return ("NO_ANSWER", "未获取到回答（可能被风控或页面异常）")
            try:
                with open(answer_file, "w", encoding="utf-8") as f:
                    f.write(answer)
            except Exception as e:
                return ("ERROR", "写入回答失败: " + str(e))
            log("回答长度: " + str(len(answer)))
            return ("ANSWER", answer_file)
        except Exception as e:
            log("异常: " + str(e))
            return ("ERROR", str(e)[:150])
        finally:
            # 不调用 driver.quit()：保留保活 Edge 供复用；msedgedriver 由下次运行清理
            pass

    # 第一次：优先复用保活会话（多轮上下文、更快）
    status, info = attempt(cold_start=False)
    # 发送失败/页面异常：重启浏览器再试一次（自愈退化会话）
    if status in ("SEND_FAIL", "NO_ANSWER", "ERROR"):
        log("首次尝试失败（" + status + "），重启浏览器重试")
        status, info = attempt(cold_start=True)
    if status == "NEED_LOGIN":
        print("NEED_LOGIN")
    elif status == "ANSWER":
        print("ANSWER|" + info)
    else:
        print("ERROR|" + info)

if __name__ == "__main__":
    main()
