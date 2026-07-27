# Notebook UI Patterns — Snapshot 识别参考

本文档记录了在聚宽 notebook 页面 `take_snapshot` 中发现的 UI 模式，供编写 evaluate_script 和诊断问题时精确匹配。

## 1. 内存指示器

**Snapshot 特征：**
```
uid=X button "内存使用 XXXM/1.0G，本篇YYY.YYM"
```

**evaluate_script 读取方式：**
```javascript
// 通过 Jupyter iframe 内 DOM 查找
const memBtn = iframe.contentDocument.querySelector('[class*="memory"]');
// 或直接读 snapshot 中的 StaticText/button
```

**阈值判断：**
- `< 80%` → 安全，不触发规则8
- `>= 80%` → 触发规则8，主动警告用户
- 不同用户内存上限不同（免费 1G，付费更大），用百分比而非绝对值

**实测数据：**
| 场景 | 内存 | 占比 |
|------|------|------|
| 空 notebook | 174M/1.0G | 17% |
| numpy 12×50MB | 826M/1.0G | 83% |
| 全市场 Panel 5515×252 | 679M/1.0G | 68% |
| 溢出后自动恢复 | 178M/1.0G | 18% |

---

## 2. 内核状态指示器

**正常状态 — Snapshot 特征：**
```
StaticText "Python 3"
StaticText "已信任"
```
注意：两者之间可能有或没有 "未连接"。

**断开状态 — Snapshot 特征：**
```
StaticText "Python 3"
StaticText "未连接"    ← 关键标识
StaticText "已信任"
```
`"未连接"` 是一个独立的 `StaticText` 节点，位于 "Python 3" 和 "已信任" 之间。

---

## 3. 弹出对话框（三种类型）

### 3.1 连接失败弹窗
**出现场景：** notebook 服务器连接断开（非内存原因）

**Snapshot 特征：**
```
heading "连接失败" level="4"
StaticText "无法连接至notebook服务器，程序将尝试重新连接， 请检查您的网络连接或服务器配置。"
button "确定"
```

**处理：** 点"确定" → 规则7(1) 手动重启内核

### 3.2 内核正在重启弹窗（内存溢出标志）
**出现场景：** 内存溢出导致内核崩溃，系统正在自动重启

**Snapshot 特征：**
```
heading "内核正在重启" level="4"
StaticText "内核可能已停止运行，稍后将自动重启。"
button "确定" focusable focused
```

**处理：** 点"确定" → 等 5-8 秒 → 重新 snapshot 检查：
- 恢复 "Python 3 已信任" → 继续
- 仍有 "未连接" → 规则7(1) 兜底

### 3.3 内存溢出/内存不足弹窗
**出现场景：** 内存耗尽时平台弹出的警告

**Snapshot 特征（推测，实测未触发）：**
```
heading "内存溢出" 或 "内存不足"
button "确定" 或 "重启内核"
```

**处理：** 点"确定" → 规则7(1) 手动重启 → 规则8 分批建议

---

## 4. Cell 状态识别

**Snapshot 特征：**
```
未运行:  StaticText "In [ ]:"
运行中:  StaticText "In [*]:"
已完成:  StaticText "In [5]:"   ← 数字 = 执行序号
```

**evaluate_script 读取方式：**
```javascript
const prompt = cell.element.find('.input_prompt').text().trim();
// 返回如 "In [5]:" 或 "In [*]:" 或 "In [ ]:"
```

---

## 5. 研究页面 — 文件"运行中"状态

**Snapshot 特征：**
```
link "文件名.ipynb"
StaticText "运行中"    ← 文件后有这个表示内核活跃
```

**无运行中时：**
```
link "文件名.ipynb"
StaticText "X分钟前"   ← 只有时间戳，无"运行中"
```

**处理：** 规则6(3) 中检查此项。有"运行中"→程序正常运行；无→需重启。

---

## 6. UID 生命周期

- `take_snapshot` 后 uid 在当前页面有效
- `close_page` 后重新 snapshot，uid 会变化
- 页面切换 (`select_page`) 后 snapshot 更新，uid 也会变化
- **每次 DOM 更新（弹窗出现/消失）后需要重新 snapshot**

**最佳实践：** 每次操作前 `take_snapshot`，不要跨操作复用 uid。

---

## 7. 研究页面工具栏

**Snapshot 关键 uid 模式：**
```
button "新建"            — 创建新 notebook
button "重置内核"         — 重置内核
button "重启研究环境"     — 最后手段
button "刷新notebook列表"
checkbox "点击这里进行重命名，删除等操作。"  — 文件选择框

# 选中文件后出现：
button "停止运行选择的notebook"    — 关闭内核
button "删除"
```

---

## 8. Notebook 页面工具栏

**Snapshot 关键 uid 模式：**
```
button "运行"    — 执行选中 cell (描述: "运行")
button "中断内核"  — 停止执行 (描述: "中断内核")
button "重启内核(显示确认对话框)"  — 描述含完整说明
button "重启内核,然后重新运行整个代码(显示确认对话框)"
combobox value="代码"   — cell 类型选择
```
