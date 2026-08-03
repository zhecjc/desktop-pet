#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""describe_image.py — 调用本地 OpenAI 兼容服务（xiaomimimo2.5）识别图片

用法:
    python describe_image.py <图片路径> [--prompt "描述要求"]
    python describe_image.py <图片路径> --base-url http://localhost:1234/v1 --model xiaomimimo2.5

配置优先级（高到低）:
    命令行参数 > 环境变量 (MIMO_BASE_URL / MIMO_MODEL / MIMO_API_KEY)
    > 配置文件 .reasonix/mimo.conf > 内置默认值

mimo.conf 示例:
    base_url=http://localhost:11434/v1
    model=xiaomimimo2.5
    api_key=          # 本地服务一般留空；云服务填 key
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "xiaomimimo2.5"


def load_config():
    """从 .reasonix/mimo.conf 读取 key=value 配置"""
    cfg = {}
    here = os.path.dirname(os.path.abspath(__file__))
    # work/pet/describe_image.py -> 项目根/.reasonix/mimo.conf
    conf_path = os.path.normpath(os.path.join(here, "..", "..", ".reasonix", "mimo.conf"))
    if os.path.exists(conf_path):
        with open(conf_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    cfg[k.strip()] = v.strip()
    return cfg


def guess_mime(path):
    ext = os.path.splitext(path)[1].lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }.get(ext, "image/jpeg")


def main():
    ap = argparse.ArgumentParser(description="用 xiaomimimo2.5 识别并描述图片")
    ap.add_argument("image", help="图片文件路径")
    ap.add_argument("--prompt", default="请详细描述这张图片的内容。", help="描述要求")
    ap.add_argument("--base-url", help="OpenAI 兼容服务地址，如 http://localhost:11434/v1")
    ap.add_argument("--model", help="模型名称")
    ap.add_argument("--api-key", help="API key（本地服务一般不需要）")
    args = ap.parse_args()

    cfg = load_config()
    base_url = args.base_url or os.environ.get("MIMO_BASE_URL") or cfg.get("base_url") or DEFAULT_BASE_URL
    model = args.model or os.environ.get("MIMO_MODEL") or cfg.get("model") or DEFAULT_MODEL
    api_key = args.api_key or os.environ.get("MIMO_API_KEY") or cfg.get("api_key") or ""

    if not os.path.exists(args.image):
        print("错误: 图片不存在: %s" % args.image, file=sys.stderr)
        sys.exit(2)

    with open(args.image, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": args.prompt},
                {"type": "image_url", "image_url": {"url": "data:%s;base64,%s" % (guess_mime(args.image), b64)}},
            ],
        }],
        "stream": False,
    }

    url = base_url.rstrip("/") + "/chat/completions"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    if api_key:
        req.add_header("Authorization", "Bearer " + api_key)

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        print("HTTP 错误 %s: %s" % (e.code, body[:500]), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print("连接失败: %s" % e, file=sys.stderr)
        print("请确认本地服务已启动，并检查 base-url（默认 %s）与 model（默认 %s）配置。" % (DEFAULT_BASE_URL, DEFAULT_MODEL), file=sys.stderr)
        sys.exit(1)

    try:
        msg = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        print("响应异常: %s" % json.dumps(data, ensure_ascii=False)[:500], file=sys.stderr)
        sys.exit(1)

    print(msg)


if __name__ == "__main__":
    main()
