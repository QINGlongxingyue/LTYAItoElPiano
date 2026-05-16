import os
import time
import pygame
import keyboard
from pydub import AudioSegment
import tempfile

def ensure_min_duration(wav_path, min_duration_ms=500):
    """检查wav时长，如果小于最小时长，则填充尾部静音到最小时长，返回新临时文件路径"""
    seg = AudioSegment.from_wav(wav_path)
    if len(seg) < min_duration_ms:
        silence = AudioSegment.silent(duration=min_duration_ms - len(seg))
        seg = seg + silence
        # 保存到临时文件
        fd, tmp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        seg.export(tmp_path, format="wav")
        return tmp_path
    return wav_path

def load_note_files(note_dir="cut_notes", min_duration_ms=500):
    files = [f for f in os.listdir(note_dir) if f.startswith("note_") and f.endswith(".wav")]
    files.sort()
    if not files:
        print(f"错误：在 {note_dir} 中没有找到文件，请先运行切割脚本")
        return None
    # 预处理：保证每个片段至少 min_duration_ms 毫秒
    temp_files = []
    processed = []
    for f in files:
        orig_path = os.path.join(note_dir, f)
        new_path = ensure_min_duration(orig_path, min_duration_ms)
        processed.append(new_path)
        if new_path != orig_path:
            temp_files.append(new_path)
    return processed, temp_files

def play_smart(note_dir="cut_notes", min_duration_ms=500):
    files, temp_files = load_note_files(note_dir, min_duration_ms)
    if not files:
        return
    total = len(files)
    print(f"共加载 {total} 个音频片段（已确保每个片段至少 {min_duration_ms}ms）")
    print("按任意键顺序播放（每个按键播放下一个片段，自动连贯，无需等待松开）")
    print("按 ESC 退出")

    pygame.mixer.init()
    idx = 0
    current_channel = None

    def play_next(e):
        nonlocal idx, current_channel
        if e.event_type == keyboard.KEY_DOWN and e.name != 'esc':
            if idx >= total:
                print("所有片段已播放完毕")
                return
            # 如果当前有正在播放的，立即停止（实现快速切换）
            if current_channel and current_channel.get_busy():
                current_channel.stop()
            # 加载并播放当前片段
            sound = pygame.mixer.Sound(files[idx])
            current_channel = pygame.mixer.find_channel()
            if current_channel is None:
                current_channel = pygame.mixer.Channel(0)
            current_channel.play(sound)
            print(f"播放 {os.path.basename(files[idx])} ({idx+1}/{total})")
            idx += 1

    keyboard.hook(play_next)
    print("已启动，请按任意键开始...")
    keyboard.wait('esc')
    pygame.mixer.quit()
    # 清理临时文件
    for tmp in temp_files:
        try:
            os.remove(tmp)
        except:
            pass
    print("退出")

if __name__ == "__main__":
    play_smart(min_duration_ms=500)  # 你可以调整这个数值，例如 400, 600