# -*- coding: utf-8 -*-
"""
ask_doubao.py — 桌宠调用脚本：打开网页版豆包（doubao.com），提问并取回回答。
用法: python ask_doubao.py <问题base64>
输出(stdout, 单行):
  ANSWER|<回答文件UTF-8路径>   成功
  NEED_LOGIN                  等登录超时
  ERROR|<原因>                失败
首次使用会弹出 Chrome 窗口，需手动登录豆包一次（登录态保存在 profile 中，之后免登录）。
"""
import sys, os, base64, time, json

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
    profile = os.path.join(os.environ["APPDATA"], "DesktopPet", "doubao_profile")

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=profile, channel="chrome", headless=False,
            viewport={"width": 1280, "height": 900})
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://www.doubao.com/chat/", timeout=45000, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        log("页面标题: " + str(page.title()))

        # ---- 等待登录（最多 180 秒）----
        deadline = time.time() + 180
        while time.time() < deadline:
            btn = page.query_selector("text=登录")
            if btn is None:
                break
            page.wait_for_timeout(3000)
        else:
            print("NEED_LOGIN")
            ctx.close()
            return
        log("登录状态: 已登录")

        # ---- 定位输入框 ----
        tb = page.query_selector("textarea[placeholder], div[contenteditable='true']")
        if tb is None:
            # 再试一次等待
            page.wait_for_timeout(4000)
            tb = page.query_selector("textarea[placeholder], div[contenteditable='true']")
        if tb is None:
            print("ERROR|找不到输入框（页面结构可能变化）")
            ctx.close()
            return

        # ---- 记录发送前页面文本 ----
        before = page.evaluate("() => document.body ? document.body.innerText : ''")

        # ---- 输入并发送 ----
        tb.click()
        page.keyboard.type(question, delay=10)
        page.wait_for_timeout(500)
        page.keyboard.press("Enter")

        # ---- 等待回答（最多 120 秒，文本 4 秒无变化视为完成）----
        last = before
        stable = 0
        deadline = time.time() + 120
        while time.time() < deadline:
            page.wait_for_timeout(500)
            try:
                cur = page.evaluate("() => document.body ? document.body.innerText : ''")
            except Exception:
                cur = last
            if cur != last:
                last = cur
                stable = 0
            else:
                stable += 1
                if stable >= 8:  # 4 秒无变化
                    break
        ctx.close()

        # ---- 提取回答：发送后新增的文本 ----
        answer = ""
        if len(last) > len(before):
            answer = last[len(before):]
        # 清理常见 UI 噪声
        for junk in ("复制", "重新生成", "停止生成", "点赞", "踩", "举报"):
            if junk in answer:
                answer = answer.split(junk)[0]
        answer = answer.strip()
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

if __name__ == "__main__":
    main()
