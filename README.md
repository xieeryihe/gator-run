直接用带apk的分析
python runGatorOnApk.py

apk目录等相关配置查看
AndroidBench\config\gator_config.json


---

一键执行：

python runGator.py -j apv/config.json -p apv

带apk的分析（路径在AndroidBench\config\gator_config.json中配置，但是runGator.py没改，后面一般就用这个带apk的即可）
python runGatorOnApk.py ./apk/Calendar.apk 

apv目录中替换为自己需要的app，包含源码的压缩包，并到目录下config.json 中配置基本信息。

如果没改runGatorOnApk.py的实现，或者出现路径问题，可以试着用这个配置一下。
```txt
export GatorRoot=C:\Code\experiment\Gator
export ADK=D:\AndroidSDK
```

运行前准备：
- 如文档所说，下载 apache 的 ant 并在 SootAndroid 目录下执行 `ant` 指令，编译一下
- 配置配置ADK
（如果修改了SootAndroid中的内容，都需要重新编译）

论文是
Static Window Transition Graphs for Android（2015）
Static Control-Flow Analysis of User-Driven Callbacks in Android Applications（2015）

都是同一个系列的。


# WTG 可视化分析 - 完整指南

---

## 🚀 快速开始

```bash
# 方法 1：运行 APV 示例
cd AndroidBench
visualize_apv.bat              # Windows
# 或
python visualize_apv.py        # 跨平台

# 方法 2：手动运行
python runGator.py -j apv/config.json -p apv

# 查看结果（自动在浏览器打开）
# output/apv/results/apv_utg.html
```

---

## 📊 查看分析结果

### 1. HTML 查看器（推荐）

打开 `output/apv/results/apv_utg.html`，包含 4 个标签页：
- **Overview** - 使用说明
- **Nodes** - 窗口节点详情
- **Edges** - 转换边详情
- **DOT File** - 图形定义（可复制）

### 2. JSON 数据分析

查看 `output/apv/results/apv_analysis.json` 获取：

```json
{
  "application": "apv",
  "analysis_time": "2025-12-05 15:45:16",
  "summary": {
    "total_nodes": 14,
    "total_edges": 105,
    "launcher_nodes": 1,
    "activity_nodes": 4,
    "dialog_nodes": 5,
    "menu_nodes": 4,
    "total_event_handlers": 53,
    "total_callbacks": 144
  },
  "activities": [...],
  "dialogs": [...],
  "event_types": {...},
  "nodes": [...],
  "edges": [...]
}
```

### 3. 在线可视化

1. 在 HTML 查看器点击 "DOT File" 标签
2. 点击 "Copy DOT Content"
3. 访问 https://dreampuf.github.io/GraphvizOnline/
4. 粘贴内容查看图形

### 4. Graphviz 命令

```bash
cd output/apv/results
dot -Tpng apv_utg.dot -o apv_wtg.png      # PNG 格式
dot -Tsvg apv_utg.dot -o apv_wtg.svg      # SVG 格式
```

---

## 🔧 分析其他应用

### 从项目分析

```bash
# 1. 编辑配置文件添加应用配置
python runGator.py -j your-app/config.json -p your-app

# 结果保存在 output/your-app/
```

### 从 APK 分析

```bash
# 分析并保留源码
python runGatorOnApk.py app.apk -client WTGVisualizationClient --keep-decoded-apk-dir

# 输出结构
# output/app/source/   - APK 源码
# output/app/results/  - 分析结果
```

### 配置文件示例（apv/config.json）

```json
{
    "BASE_DIR": "C:\\Code\\experiment\\Gator\\AndroidBench",
    "BASE_CLIENT": "WTGVisualizationClient",
    
    "apv": {
        "relative-path": "apv/pdfview",
        "api-level": "android-10",
        "zip-file": "apv/apv-0.4.0.zip"
    },
    
    "your-app": {
        "relative-path": "path/to/your/app",
        "api-level": "android-23"
    }
}
```

---

## 📖 WTG 图形说明

### 节点类型
- 🟢 **绿色（Launcher）** - 应用入口
- 🔵 **蓝色（Activity）** - 活动窗口
- 🔴 **粉色（Dialog）** - 对话框
- 🟡 **黄色（Menu）** - 菜单

### 边信息
- **箭头** - 窗口转换方向
- **标签** - 事件类型（click、back 等）
- **数字** - 事件处理器数量

### 常见事件类型
- `click` - 点击事件
- `implicit_back_event` - 返回键
- `implicit_home_event` - Home 键
- `implicit_power_event` - 电源键
- `implicit_rotate_event` - 屏幕旋转

---

## 💻 编程访问示例

```java
// 在自定义 Client 中访问 WTG
WTGBuilder wtgBuilder = new WTGBuilder();
wtgBuilder.build(output);
WTG wtg = wtgBuilder.build(output).getWTG();

// 遍历节点
for (WTGNode node : wtg.getNodes()) {
    System.out.println("Window: " + node.getWindow());
    System.out.println("Type: " + node.getWindowType());
}

// 遍历边
for (WTGEdge edge : wtg.getEdges()) {
    System.out.println(edge.getSourceNode() + " -> " + edge.getTargetNode());
    System.out.println("Event: " + edge.getGUIWidget().getEventType());
}
```

---

### ✅ 三种输出格式
- **HTML** - 交互式查看器，支持 4 个标签页
- **DOT** - Graphviz 图形定义，兼容可视化工具
- **JSON** - 结构化数据，支持程序化访问


### ✅ 自动化脚本
- Windows 批处理文件（`visualize_apv.bat`）
- Python 跨平台脚本（`visualize_apv.py`）

---

## 📁 核心文件清单

| 文件 | 说明 |
|------|------|
| `SootAndroid/src/.../WTGVisualizationClient.java` | 可视化客户端 |
| `AndroidBench/apv/config.json` | APV 配置文件 |
| `AndroidBench/visualize_apv.bat` | Windows 快速启动 |
| `AndroidBench/visualize_apv.py` | Python 快速启动 |
| `AndroidBench/runGator.py` | 通用分析脚本 |
| `AndroidBench/runGatorOnApk.py` | APK 分析脚本 |


保留 APK 源码？
使用 `--keep-decoded-apk-dir` 参数

### 编译错误？
```bash
cd SootAndroid
ant compile
```

