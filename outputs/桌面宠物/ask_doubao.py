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
import sys, os, base64, time

def log(msg):
    try:
        with open(os.path.join(os.environ["APPDATA"], "DesktopPet", "doubao.log"), "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S") + " " + msg + "\n")
    except Exception:
        pass

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

    from selenium import webdriver
    from selenium.webdriver.edge.options import Options
    from selenium.webdriver.edge.service import Service

    opts = Options()
    opts.add_argument("--user-data-dir=" + profile)
    opts.add_argument("--no-first-run")
    opts.add_argument("--disable-search-engine-choice-screen")
    # ---- 反自动化检测：隐藏 webdriver 特征，避免豆包风控 ----
    opts.add_argument("--disable-blink-features=AutomationControlled")
    try:
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
    except Exception:
        pass
    if not os.path.exists(driver_path):
        print("ERROR|缺少 msedgedriver.exe（请放在桌宠目录下）")
        return
    svc = Service(driver_path)

    driver = None
    try:
        driver = webdriver.Edge(service=svc, options=opts)
        driver.set_window_size(1280, 900)
        driver.set_page_load_timeout(45)
        # 覆盖 navigator.webdriver（对之后加载的所有页面生效）
        try:
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            })
        except Exception:
            pass
        driver.get("https://www.doubao.com/chat/")
        time.sleep(6)
        log("页面标题: " + str(driver.title))

        # ---- 等待登录（最多 180 秒）----
        deadline = time.time() + 180
        while time.time() < deadline:
            btns = driver.find_elements("xpath", "//*[contains(text(),'登录')]")
            if len(btns) == 0:
                break
            time.sleep(3)
        else:
            # 超时：保留 Edge 窗口让用户继续登录，脚本退出
            log("等待登录超时，窗口保留")
            print("NEED_LOGIN")
            driver = None  # 防止 finally 里 quit 关掉等待登录的窗口
            return
        log("登录状态: 已登录")

        # ---- 定位输入框 ----
        def find_input():
            try:
                return driver.find_element("css selector", "textarea[placeholder], div[contenteditable='true']")
            except Exception:
                return None
        tb = find_input()
        if tb is None:
            time.sleep(4)
            tb = find_input()
        if tb is None:
            print("ERROR|找不到输入框（页面结构可能变化）")
            return

        # ---- 记录发送前页面文本 ----
        before = driver.execute_script("return document.body ? document.body.innerText : ''")

        # ---- 输入并发送 ----
        tb.click()
        tb.send_keys(question)
        time.sleep(0.5)
        tb.send_keys(u"\ue007")  # Enter

        # ---- 等待回答（最多 120 秒，文本 4 秒无变化视为完成）----
        last = before
        stable = 0
        deadline = time.time() + 120
        wind_risk = False
        while time.time() < deadline:
            time.sleep(0.5)
            try:
                cur = driver.execute_script("return document.body ? document.body.innerText : ''")
            except Exception as e:
                log("等待回答时页面异常: " + str(e))
                wind_risk = True
                break
            if "检测到自动化" in cur or "自动化软件" in cur:
                log("页面出现风控提示")
                wind_risk = True
                break
            if cur != last:
                last = cur
                stable = 0
            else:
                stable += 1
                if stable >= 8:
                    break
        if wind_risk:
            print("ERROR|豆包检测到自动化操作，本次未回答（偶发风控，稍后再试）")
            return
        if stable < 8:
            log("等待回答提前结束（可能风控或页面异常）")
            print("ERROR|豆包未完成回答（可能被风控，稍后再试）")
            return

        # ---- 提取回答：定位用户问题之后的新增文本 ----
        full = last
        tail = ""
        qidx = full.rfind(question)
        if qidx >= 0:
            tail = full[qidx + len(question):]
        elif len(full) > len(before):
            tail = full[len(before):]
        answer = tail
        # 1) 功能栏 / 操作按钮截断
        for junk in ("快速", "解题答疑", "帮我写作", "图像生成", "音乐生成", "翻译", "PPT 生成", "视频生成", "更多",
                     "复制", "重新生成", "停止生成", "点赞", "踩", "举报", "检测到自动化"):
            if junk in answer:
                answer = answer.split(junk)[0]
        # 2) 去掉尾部"追问推荐"（连续短句：≤40 字且不以句号/冒号等结尾）
        lines = answer.split("\n")
        while lines:
            last_line = lines[-1].strip()
            if len(last_line) <= 40 and not last_line.endswith(("。", "！", "：", ":", "；", ";", "～", "~")):
                lines.pop()
            else:
                break
        answer = "\n".join(lines).strip().lstrip(":： \n")
        if not answer:
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
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass

if __name__ == "__main__":
    main()
