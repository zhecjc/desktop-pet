# 桌面宠物 (Desktop Pet)

一个会互动、会播报天气、会提醒你喝水休息的 Windows 桌面宠物。单文件程序，双击即用，无需安装。

## 功能特性

- **互动动画**：单击角色触发随机互动（跳跃 / 压扁回弹 / 左右抖动 / 摆姿势 / 点头 / 卖萌），平时有呼吸起伏、打哈欠、伸懒腰、东张西望、打瞌睡
- **表情特效**：互动时显示爱心、音符、汗滴、星星、Zzz、感叹号
- **天气播报**：优先用 Windows 本地定位（WiFi / GPS，精度街道级），拿不到时自动回退 IP 定位城市；启动时与每天 8 点后自动播报一次，之后每 30 分钟静默刷新温度与天气效果，不弹气泡打扰
- **天气视觉特效**：下雨飘雨丝、下雪飘雪花；天气炎热（≥27℃）红温冒热气、寒冷（≤2℃）结冰挂冰晶，效果跟随角色动作动态贴合
- **天气效果预览**：可手动切换查看雨丝 / 雪花 / 红温 / 结冰效果，不依赖真实天气，随时恢复自动
- **番茄钟**：25 分钟专注 / 5 分钟休息，专注结束提醒起身活动，并自动进入休息计时
- **健康提醒**：喝水 / 久坐提醒（间隔 30 / 45 / 60 / 90 / 120 分钟可调，设置持久化），久坐时伸懒腰动画
- **换角色**：往 `characters` 文件夹放角色图即可随时换，纯色背景自动去背景，无需抠图
- **自定义台词**：记事本编辑 `台词.txt`（一行一句，支持 `[点击][姿势][发呆][放下][开心][委屈]` 分段），菜单一键重新加载
- **心情系统**：根据互动频率自动变化（开心 / 不错 / 困倦 / 委屈），影响动作风格与说话内容
- **问豆包**：右键菜单"问豆包…"输入问题，调用网页版豆包（doubao.com）联网搜索后回答，气泡显示（首次需在弹出窗口登录豆包一次）
- **其他**：自动散步（可关）、开机自启、置顶显示、鼠标滚轮缩放、设置自动记忆

## 快速开始

直接运行交付物：

```
outputs/桌面宠物/桌宠.exe
```

无需安装任何依赖，新版启动时会自动关闭旧版实例。

## 操作说明

| 操作 | 效果 |
|------|------|
| 左键按住拖动 | 移动桌宠位置 |
| 单击角色 | 触发随机互动 |
| 鼠标滚轮 | 放大 / 缩小 |
| 右键点击 | 打开菜单 |

## 目录结构

```
.
├── outputs/桌面宠物/        # 交付物（可直接分发）
│   ├── 桌宠.exe             # 程序本体（单文件）
│   ├── 使用说明.txt
│   ├── 台词.txt             # 气泡台词（可编辑）
│   ├── ask_doubao.py       # 豆包问答脚本（驱动 Chrome 操作网页版豆包）
│   ├── 角色透明图.png / 效果预览.png / 姿势预览.png
│   └── characters/          # 角色文件夹（每子文件夹一个角色）
└── work/                    # 开发目录
    ├── pet/
    │   ├── DesktopPet.cs     # 主程序（C# / WinForms，单文件）
    │   ├── winrt/            # WinRT 元数据（编译期引用，用于 Windows 本地定位）
    │   ├── DesktopPet_v2.cs  # 历史版本
    │   ├── DesktopPet_v2b.cs
    │   └── …                 # 图像处理 / 测试 / 补丁脚本、测试帧
    └── …
```

## 技术说明

- **主程序**：C# / .NET WinForms，透明无边框置顶窗口（`UpdateLayeredWindow`），单文件编译并内嵌图标
- **天气数据**：中国天气网；城市定位分两级——先调 Windows 位置服务（`Windows.Devices.Geolocation`，WiFi/GPS 三角定位）拿经纬度，再按内置城市经纬度表算最近城市（本地完成）；本地定位不可用（权限未开 / 无信号 / 超时）时自动回退 IP 定位（ipip.net → 搜狐 → ip-api）；仍失败可手动设置城市名或城市代码（如 `101280101`）
- **问豆包**：`ask_doubao.py` 用 Selenium 驱动本机 Edge（独立 profile，路径 `%APPDATA%\DesktopPet\doubao_profile_edge`）打开网页版豆包并提问取回答，不经过任何付费 API。依赖：本机需装有 python 3、`pip install selenium`、Edge，以及桌宠目录下的 `msedgedriver.exe`（已随交付物发布）；首次使用会在弹出的窗口里登录豆包一次（此后免登录）。回答截断为 1200 字显示
- **编译命令**（需 .NET Framework 4.x 的 csc，输出 `test_pet.exe`）：
  ```
  csc /nologo /target:winexe /out:test_pet.exe /r:System.dll /r:System.Core.dll /r:System.Drawing.dll /r:System.Windows.Forms.dll /r:System.Xml.dll /r:System.Web.dll /r:System.Runtime.dll /r:netstandard.dll /r:System.Runtime.WindowsRuntime.dll /r:winrt/windows.winmd /r:winrt/Windows.Foundation.FoundationContract.winmd /r:winrt/Windows.Foundation.UniversalApiContract.winmd DesktopPet.cs
  ```
  （在 `work/pet` 目录下执行；`winrt/` 下的 winmd 仅编译期需要，发布 exe 运行时不依赖）

## 常见问题

**Q: 桌宠不见了？**
A: 重新双击 exe 即可。

**Q: 想加新角色？**
A: 在 `characters` 文件夹新建一个子文件夹，放入角色图（`character.png` 必填，可选 `pose1.png` / `pose2.png`，支持 png / jpg / bmp），右键菜单"切换角色"即可选择。白底或纯色背景的图片会自动去背景。

**Q: 不想让它乱跑？**
A: 右键菜单取消勾选"自动散步"。

## License

未指定（个人项目，保留所有权利）。
