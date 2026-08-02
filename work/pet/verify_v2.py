src = open(r"work\pet\DesktopPet_v2b.cs", "r", encoding="utf-8-sig").read()
must_have = {
    "RunSelfTest": "自检",
    "/selftest": "自检入口",
    "OnMouseEnter": "悬停捕获",
    "CreateParams": "CreateParams",
    "OnLoad": "OnLoad",
    "LastUpdateOk": "透明记录",
    "hdcScreen, ref ptDst": "DC修复",
    "RenderSurface": "气泡复用",
    "_scale = 1.0": "默认100%",
    "pet.ini": "旧设置文件",
    "MIN_SCALE = 0.30": "最小30%",
    "Native.SetCapture(Handle)": "捕获",
}
must_not = {
    "Dictionary<string, Bitmap>": "表情字典",
    "SmoothPose": "平滑",
    "UpdateExpressionAndBlink": "表情更新",
    "LoadExpressions": "加载表情",
    "_expr =": "表情字段",
    "_clickCount": "生气",
    "pet2.ini": "新设置",
    "_scale = 0.5": "50%",
    "expr_": "表情资源",
    "CurrentBase": "表情基图",
}
print("=== 必须存在 ===")
ok = True
for m, label in must_have.items():
    has = m in src
    if not has: ok = False
    print(f"  {label:8s} {m:30s} {'YES' if has else 'NO'}")
print("=== 必须不存在 ===")
for m, label in must_not.items():
    has = m in src
    if has: ok = False
    print(f"  {label:8s} {m:30s} {'PRESENT!' if has else 'ok'}")
print("RESULT:", "PASS" if ok else "FAIL")
