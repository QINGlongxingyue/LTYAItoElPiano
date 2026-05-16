<h1>LTYAItoElPiano单曲电钢安卓播放</h1>
<br>正在搭建....
<br>鸽了 现使用python处理 安卓app单曲弹奏 三模式 2控制 
直接跑了 app内声音仅供示范使用

## ✨ 主要功能

- 🎹 **实时 MIDI 输入**：支持 USB 或蓝牙 MIDI 电钢琴，延迟极低。
- 🎶 **下落式音符**：根据 MIDI 事件自动生成音符条，长度实时反映音符时值。
- 🔄 **三种练习模式**：
  - **等待模式**：音符落底时暂停游戏，必须弹奏正确音符才能继续（适合强制校准）。
  - **演奏模式**：音符落底自动播放人声，不暂停，适合完整演奏。
  - **练习模式**：落底自动消失（不播放）；提前弹奏可播放人声并消失，适合自由跟弹。
- 🔊 **洛天依 AI 人声**：每个音符对应预切割的 `.wav` 片段，弹奏时即时发声。
- 🎼 **伴奏同步**：支持背景伴奏（`banzo.wav`），启动延迟可调。
- 🎛️ **便捷控制**：
  - 模式切换（等待/演奏/练习）  
  - 静音伴奏  
  - 重新开始（重置所有音符和伴奏）
- 📱 **横屏界面**：钢琴键盘自适应屏幕，黑键清晰，下落音符带动态高度和醒目颜色。

## 🛠️ 技术栈

- **语言**：Kotlin  
- **UI**：Jetpack Compose + 自定义 View（PianoView）  
- **音频**：
  - 人声片段：`SoundPool`（低延迟）  
  - 伴奏：`MediaPlayer`（循环播放）  
- **MIDI 通信**：`android.media.midi`（API 28+）  
- **数据解析**：Gson（解析预处理的 `midi_events.json`）  
- **最低 SDK**：28（Android 8.1）

## 📦 项目结构
app/src/main/
├── assets/ # 资源文件
│ ├── midi_events.json # MIDI 事件（音高、起止时间）
│ ├── banzo.wav # 伴奏音频
│ └── cut_notes/ # 切割好的音符片段（note_0001.wav ~ note_xxxx.wav）
├── java/com/example/ltyaitoelpiano/
│ ├── MainActivity.kt # 主逻辑（模式控制、MIDI 处理、时间轴）
│ ├── audio/
│ │ └── AudioManager.kt # 音频管理（SoundPool + MediaPlayer）
│ ├── model/
│ │ └── MidiEvent.kt # 数据类
│ ├── ui/
│ │ └── PianoView.kt # 钢琴绘制及下落动画
│ └── util/
│ └── MidiJsonLoader.kt # JSON 加载工具
└── res/ # 布局、主题等资源

text

## 🚀 编译与安装

### 前提条件

- Android Studio Hedgehog 或更高版本  
- Android SDK 28+  
- 支持 USB 主机模式的 Android 设备（用于 MIDI 键盘）

### 步骤

1. **准备资源（必须）**

将您的 MIDI 文件通过 Python 预处理生成 midi_events.json 和 cut_notes/ 文件夹（参考下方“资源预处理”）。

将生成的 midi_events.json、banzo.wav 和整个 cut_notes/ 文件夹放入 app/src/main/assets/。

用 Android Studio 打开项目，等待 Gradle 同步完成。

连接 Android 设备（或使用模拟器，但 MIDI 输入需要真机）。

点击 Run 构建并安装 APK。

🧰 资源预处理（PC 端）
您需要在 PC 上使用 Python 将任意 MIDI 文件和对应的人声干声切割成对齐的音符片段。

安装依赖

bash
pip install mido pydub
运行切割脚本（示例脚本保存在 scripts/cut_notes.py）

输入：test.mid 和 vocals.wav（需时长对齐）

输出：midi_events.json 和 cut_notes/note_xxxx.wav

将输出文件复制到 Android 项目的 assets 目录。

详细脚本可参考项目 docs/preprocess.md。

🎮 使用说明
连接电钢琴：通过 USB OTG 线连接设备，启动应用后会自动识别并提示“MIDI 键盘已连接”。

选择模式：点击右上角按钮循环切换（等待模式 → 演奏模式 → 练习模式）。

开始游戏：

伴奏会在启动后 1.2 秒自动响起。

彩色长条从顶部向对应琴键下落。

等待模式：音符落底后游戏暂停，弹奏正确音高继续。

演奏模式：音符落底自动播放人声，无需暂停。

练习模式：落底自动消失（不播放）；提前弹奏可播放人声并消失。

其他控制：

静音伴奏：关闭/开启背景音乐。

重新开始：重置所有进度，伴奏从头播放。

📄 许可证
本项目采用 MIT 许可证，详情见 LICENSE 文件。
