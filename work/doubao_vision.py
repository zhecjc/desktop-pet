# -*- coding: utf-8 -*-
"""
豆包（火山方舟 Ark）视觉理解脚本
把本地图片发给豆包视觉模型，返回图片描述。

用法:
    python doubao_vision.py <图片路径> [--prompt "描述要求"] [--model "模型ID"]

配置:
    环境变量 ARK_API_KEY 必填（火山方舟 API Key）
    环境变量 ARK_MODEL 可选（视觉模型 Model ID 或推理接入点 ID），
    也可用 --model 覆盖；默认 doubao-1.5-vision-pro-32k-250115

依赖: 仅标准库；若有 Pillow 会对超大图片自动压缩
"""
import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.request
import urllib.error

API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
DEFAULT_MODEL = "doubao-seed-2-0-lite-260215"  # 若提示 ModelNotOpen，需在方舟控制台开通该模型
MAX_IMAGE_BYTES = 4 * 1024 * 1024  # 4MB 以上自动压缩
MAX_DIM = 2048


def load_image_b64(path):
    """读取图片为 base64 data URL；超大图片用 Pillow 压缩（可选）。"""
    data = open(path, "rb").read()
    if len(data) > MAX_IMAGE_BYTES:
        try:
            from PIL import Image
            import io
            im = Image.open(path)
            if max(im.size) > MAX_DIM:
                ratio = MAX_DIM / float(max(im.size))
                im = im.resize((int(im.size[0] * ratio), int(im.size[1] * ratio)), Image.LANCZOS)
            buf = io.BytesIO()
            im.convert("RGB").save(buf, format="JPEG", quality=88)
            data = buf.getvalue()
        except Exception:
            pass  # 无 Pillow 或压缩失败时保持原图
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    return "data:%s;base64,%s" % (mime, base64.b64encode(data).decode("ascii"))


def call_doubao(image_url, prompt, model, key):
    body = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
        "max_tokens": 800,
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    try:
        return result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError("响应格式异常: " + json.dumps(result, ensure_ascii=False)[:500])


def main():
    ap = argparse.ArgumentParser(description="用豆包视觉模型描述本地图片")
    ap.add_argument("image", help="图片文件路径")
    ap.add_argument("--prompt", default="请详细描述这张图片的内容。", help="描述要求")
    ap.add_argument("--model", default=os.environ.get("ARK_MODEL", DEFAULT_MODEL), help="模型 ID / 推理接入点 ID")
    args = ap.parse_args()

    key = os.environ.get("ARK_API_KEY", "").strip()
    if not key:
        print("错误: 未配置 ARK_API_KEY 环境变量。", file=sys.stderr)
        print("请在火山方舟控制台(https://console.volcengine.com/ark)创建 API Key，", file=sys.stderr)
        print("然后设置环境变量 ARK_API_KEY=<你的key>，可选 ARK_MODEL=<模型ID>。", file=sys.stderr)
        sys.exit(2)

    if not os.path.isfile(args.image):
        print("错误: 图片不存在: " + args.image, file=sys.stderr)
        sys.exit(2)

    try:
        image_url = load_image_b64(args.image)
    except Exception as e:
        print("错误: 读取图片失败: %s" % e, file=sys.stderr)
        sys.exit(2)

    try:
        desc = call_doubao(image_url, args.prompt, args.model, key)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        print("错误: 豆包 API 返回 %s: %s" % (e.code, detail), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print("错误: 调用豆包失败: %s" % e, file=sys.stderr)
        sys.exit(1)

    print(desc.strip())


if __name__ == "__main__":
    main()
