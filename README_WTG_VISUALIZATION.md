一键执行：

python runGator.py -j apv/config.json -p apv

apv目录中替换为自己需要的app，包含源码的压缩包，并到目录下config.json 中配置基本信息。


export GatorRoot=C:\Code\experiment\Gator
export ADK=D:\AndroidSDK

运行前准备：
- 如文档所说，下载 apache 的 ant 并在 SootAndroid 目录下执行 `ant` 指令，编译一下
- 配置配置ADK



# WTG 可视化分析 - 完整指南

## 📦 输出目录结构

所有输出统一在 `output/` 目录下，按应用名称组织：

```
output/
└── app_name/              # 应用名称（如 apv）
    ├── source/            # APK 解压源码（需要 --keep-decoded-apk-dir）
    │   ├── AndroidManifest.xml
    │   ├── res/           # 资源文件
    │   └── smali/         # 反编译代码
    └── results/           # 分析结果
        ├── app_name_wtg_viewer.html    # HTML 查看器
        ├── app_name_wtg.dot            # DOT 图形文件
        └── app_name_analysis.json      # JSON 分析报告
```

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
# output/apv/results/apv_wtg_viewer.html
```

---

## 📊 查看分析结果

### 1. HTML 查看器（推荐）

打开 `output/apv/results/apv_wtg_viewer.html`，包含 4 个标签页：
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
dot -Tpng apv_wtg.dot -o apv_wtg.png      # PNG 格式
dot -Tsvg apv_wtg.dot -o apv_wtg.svg      # SVG 格式
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

## 📝 主要改进总结

### ✅ 统一输出路径
- **修改前**：输出文件散落在各个目录，源码用后删除
- **修改后**：统一到 `output/app_name/` 目录，源码和结果分离

### ✅ 三种输出格式
- **HTML** - 交互式查看器，支持 4 个标签页
- **DOT** - Graphviz 图形定义，兼容可视化工具
- **JSON** - 结构化数据，支持程序化访问

### ✅ 文档精简
- 整合 5 个文档为 1 个统一指南
- 清晰的快速开始和使用说明

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

---

## 🎯 应用场景

- **测试生成** - 基于 WTG 路径生成测试用例
- **UI 分析** - 理解应用导航结构
- **漏洞检测** - 发现不安全的窗口转换
- **逆向工程** - 分析应用行为和流程
- **自动化分析** - 通过 JSON 数据批量处理

---

## 🔍 故障排查

### 找不到输出文件？
检查 `output/app_name/results/` 目录

### 想保留 APK 源码？
使用 `--keep-decoded-apk-dir` 参数

### 图形无法显示？
1. 检查 DOT 文件是否存在
2. 尝试在线工具：https://dreampuf.github.io/GraphvizOnline/
3. 安装 Graphviz：`choco install graphviz`（Windows）

### 编译错误？
```bash
cd SootAndroid
ant compile
```

---

## 📖 更多资源

- **Gator 项目**: https://github.com/secure-software-engineering/gator
- **Graphviz 文档**: https://graphviz.org/documentation/
- **在线可视化**: https://dreampuf.github.io/GraphvizOnline/

---

**祝你分析愉快！** 🎉
