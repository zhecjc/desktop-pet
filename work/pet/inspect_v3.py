content = open(r"work\pet\DesktopPet.cs", "r", encoding="utf-8-sig").read()
markers = {
    "RunSelfTest": "自检方法",
    "/selftest": "自检入口",
    "OnMouseEnter": "悬停捕获",
    "CreateParams": "CreateParams",
    "OnLoad": "OnLoad",
    "LastUpdateOk": "透明结果记录",
    "hdcScreen, ref ptDst": "DC修复",
    "RenderSurface": "气泡渲染复用",
    "SetText": "气泡SetText",
    "Dictionary<string, Bitmap>": "表情字典",
    "SmoothPose": "动作平滑",
    "UpdateExpressionAndBlink": "表情更新",
    "_scale = 0.5": "默认50%",
    "pet2.ini": "新设置文件",
    "MIN_SCALE = 0.25": "最小25%",
    "_clickCount": "生气计数",
    "expr_normal": "表情资源",
    "LoadExpressions": "加载表情",
}
for m, label in markers.items():
    print(f"{label:12s} {m:35s} {'YES' if m in content else 'NO'}")
print("chars:", len(content))
