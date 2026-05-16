import os
import pygame
import mido
import sys

# ---------- 1. 解析 MIDI ----------
def parse_midi_events(midi_path):
    mid = mido.MidiFile(midi_path)
    ticks_per_beat = mid.ticks_per_beat
    tempo = 500000
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                tempo = msg.tempo
                break
        if tempo != 500000:
            break
    ticks_per_second = ticks_per_beat * (1_000_000.0 / tempo)
    events = []
    for track in mid.tracks:
        abs_ticks = 0
        note_on = {}
        for msg in track:
            abs_ticks += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                note_on[msg.note] = abs_ticks
            elif (msg.type == 'note_off') or (msg.type == 'note_on' and msg.velocity == 0):
                if msg.note in note_on:
                    start_ticks = note_on.pop(msg.note)
                    start_sec = start_ticks / ticks_per_second
                    end_sec = abs_ticks / ticks_per_second
                    events.append((start_sec, end_sec, msg.note))
    events.sort(key=lambda x: x[0])
    return events

# ---------- 2. 加载音频片段 ----------
def load_notes(note_dir="cut_notes"):
    if not os.path.isdir(note_dir):
        return []
    files = [f for f in os.listdir(note_dir) if f.startswith("note_") and f.endswith(".wav")]
    files.sort()
    return [os.path.join(note_dir, f) for f in files]

# ---------- 3. 字体加载 ----------
def load_font(size):
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/arial.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return pygame.font.Font(path, size)
            except:
                continue
    return pygame.font.Font(None, size)

# ---------- 4. 构建琴键矩形 ----------
def build_key_rects(width, height, min_note, max_note):
    white_notes = []
    for note in range(min_note, max_note+1):
        if note % 12 in [0,2,4,5,7,9,11]:
            white_notes.append(note)
    num_white = len(white_notes)
    if num_white == 0:
        num_white = 52
    key_width = width / num_white
    piano_y = height - 150
    key_rects = {}
    for i, note in enumerate(white_notes):
        x = i * key_width
        rect = pygame.Rect(x, piano_y, key_width, 120)
        key_rects[note] = rect
    black_key_width = key_width * 0.6
    black_key_height = 80
    for i in range(num_white - 1):
        left_note = white_notes[i]
        right_note = white_notes[i+1]
        if right_note - left_note == 2:
            black_note = left_note + 1
            if min_note <= black_note <= max_note:
                left_rect = key_rects[left_note]
                x = left_rect.right - black_key_width / 2
                rect = pygame.Rect(x, piano_y, black_key_width, black_key_height)
                key_rects[black_note] = rect
    return key_rects, key_width

def draw_piano(screen, key_rects, highlight_note=None):
    for note, rect in key_rects.items():
        if rect.height > 100:
            color = (255,255,255)
            if highlight_note == note:
                color = (200,200,255)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (0,0,0), rect, 1)
    for note, rect in key_rects.items():
        if rect.height <= 100:
            color = (0,0,0)
            if highlight_note == note:
                color = (100,100,150)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (0,0,0), rect, 1)

# ---------- 5. 下落音符类 ----------
class FallingNote:
    def __init__(self, note, start_time, duration, target_rect, key_width):
        self.note = note
        self.start_time = start_time
        self.duration = duration
        self.target_rect = target_rect
        self.width = key_width * 0.8
        self.height = max(15, min(120, int(duration * 100)))
        hue = (note % 12) * 25
        self.color = (hue, 180, 220)
        self.played = False

    def get_rect(self, current_time, fall_duration):
        if current_time < self.start_time:
            return None
        elapsed = current_time - self.start_time
        progress = min(1.0, elapsed / fall_duration)
        y = progress * self.target_rect.top
        if progress >= 1.0:
            return None
        x = self.target_rect.centerx - self.width / 2
        return pygame.Rect(x, y, self.width, self.height)

# ---------- 6. 主程序 ----------
def main():
    pygame.init()
    screen_width = 1280
    screen_height = 720
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("MIDI 等待模式 - 伴奏延迟2.3秒启动")
    clock = pygame.time.Clock()

    midi_file = "test.mid"
    note_dir = "cut_notes"
    if not os.path.exists(midi_file):
        print(f"错误：找不到 {midi_file}")
        return
    events = parse_midi_events(midi_file)
    if not events:
        print("MIDI 中没有音符")
        return
    note_files = load_notes(note_dir)
    if not note_files:
        print(f"错误：找不到 {note_dir} 中的 WAV 文件")
        return
    min_len = min(len(events), len(note_files))
    events = events[:min_len]
    note_files = note_files[:min_len]

    all_notes = [e[2] for e in events]
    min_note = max(21, min(all_notes) - 12)
    max_note = min(108, max(all_notes) + 12)

    pygame.mixer.init()
    channel = None

    # ---------- 加载伴奏 ----------
    bgm_path = "banzo.wav"
    bgm_loaded = False
    if os.path.exists(bgm_path):
        pygame.mixer.music.load(bgm_path)
        bgm_loaded = True
        print("伴奏已加载，将在2.3秒后播放")
    else:
        print("警告：找不到 test_bgm.wav，将无伴奏")

    key_rects, key_width = build_key_rects(screen_width, screen_height, min_note, max_note)

    font = load_font(24)
    small_font = load_font(18)

    # 游戏状态
    current_time = 0.0
    paused = False               # 暂停标志（音符下落和伴奏都暂停）
    fall_duration = 1.0
    last_frame_time = pygame.time.get_ticks() / 1000.0

    # 伴奏延迟启动相关变量
    BGM_DELAY = 1.2                      # 延迟2.3秒
    program_start_time = last_frame_time # 程序启动的绝对时间
    bgm_started = False                  # 伴奏是否已经开始播放
    bgm_pending = False                  # 到达延迟时间但因暂停而未播放，等恢复时播放

    # 伴奏控制函数（暂停/恢复）
    def set_music_pause(pause):
        if bgm_loaded:
            if pause:
                pygame.mixer.music.pause()
            else:
                pygame.mixer.music.unpause()

    # 预创建所有音符对象
    all_falling_notes = []
    for idx, (start_sec, end_sec, pitch) in enumerate(events):
        if pitch in key_rects:
            duration = end_sec - start_sec
            fn = FallingNote(pitch, start_sec, duration, key_rects[pitch], key_width)
            all_falling_notes.append((idx, fn))

    active_notes = []          # 当前活跃音符
    waiting_note = None
    waiting_idx = -1

    def update_active_notes(now):
        nonlocal active_notes, waiting_note, waiting_idx, paused
        for idx, fn in all_falling_notes:
            if fn.start_time <= now and not fn.played and (idx, fn) not in active_notes:
                active_notes.append((idx, fn))
        active_notes[:] = [(idx, fn) for idx, fn in active_notes if not fn.played]
        if waiting_note is None:
            for idx, fn in active_notes:
                if now >= fn.start_time + fall_duration:
                    waiting_note = fn
                    waiting_idx = idx
                    paused = True
                    set_music_pause(True)
                    if channel and channel.get_busy():
                        channel.stop()
                    active_notes = [(i, f) for i, f in active_notes if i != idx]
                    return

    def play_note(idx):
        nonlocal channel
        if channel and channel.get_busy():
            channel.stop()
        sound = pygame.mixer.Sound(note_files[idx])
        channel = pygame.mixer.find_channel()
        if channel is None:
            channel = pygame.mixer.Channel(0)
        channel.play(sound)

    running = True
    while running:
        now = pygame.time.get_ticks() / 1000.0

        # ---------- 伴奏延迟启动逻辑 ----------
        if bgm_loaded and not bgm_started:
            elapsed = now - program_start_time
            if elapsed >= BGM_DELAY:
                # 到达延迟时间，尝试启动伴奏
                if not paused:
                    pygame.mixer.music.play(-1)
                    bgm_started = True
                    bgm_pending = False
                    print("伴奏开始播放")
                else:
                    # 当前处于暂停状态，延迟启动但尚未播放，标记待启动
                    bgm_pending = True
            # 如果还没到延迟时间，什么都不做

        # ---------- 更新游戏时间和音符 ----------
        if not paused:
            dt = min(0.05, now - last_frame_time)
            current_time += dt
            update_active_notes(current_time)
        last_frame_time = now

        # ---------- 事件处理 ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    if waiting_note is None:
                        # 正常暂停/恢复
                        paused = not paused
                        set_music_pause(paused)
                        # 如果恢复时，伴奏尚未开始但已到达延迟时间且未播放，则立即播放
                        if not paused and bgm_pending and not bgm_started:
                            pygame.mixer.music.play(-1)
                            bgm_started = True
                            bgm_pending = False
                            print("恢复时启动伴奏")
                else:
                    # 任意键处理（击中音符）
                    if waiting_note is not None:
                        play_note(waiting_idx)
                        waiting_note.played = True
                        waiting_note = None
                        waiting_idx = -1
                        paused = False
                        set_music_pause(False)
                    else:
                        if active_notes:
                            idx, fn = active_notes.pop(0)
                            play_note(idx)
                            fn.played = True

        # ---------- 绘制界面 ----------
        screen.fill((30,30,40))

        title = font.render("等待模式 - 空格开始/暂停 | 任意键击中当前音符", True, (255,255,255))
        screen.blit(title, (20, 20))
        if waiting_note:
            status = f"等待音符 {waiting_note.note} (按任意键)"
            status_color = (255,0,0)
        else:
            status = "播放中" if not paused else "暂停"
            status_color = (0,255,0) if not paused else (255,0,0)
        status_surf = font.render(status, True, status_color)
        screen.blit(status_surf, (screen_width - 300, 20))

        time_surf = small_font.render(f"时间: {current_time:.2f} s", True, (200,200,200))
        screen.blit(time_surf, (20, 60))

        # 显示伴奏启动倒计时或提示
        if bgm_loaded and not bgm_started:
            remain = max(0, BGM_DELAY - (now - program_start_time))
            if remain > 0:
                delay_text = small_font.render(f"伴奏启动倒计时: {remain:.1f} s", True, (255,200,100))
                screen.blit(delay_text, (20, 90))
            else:
                if bgm_pending:
                    pending_text = small_font.render("伴奏已就绪 (游戏暂停中)", True, (255,200,100))
                    screen.blit(pending_text, (20, 90))

        highlight = waiting_note.note if waiting_note else None
        draw_piano(screen, key_rects, highlight_note=highlight)

        for idx, fn in active_notes:
            rect = fn.get_rect(current_time, fall_duration)
            if rect:
                pygame.draw.rect(screen, fn.color, rect)
                pygame.draw.rect(screen, (255,255,255), rect, 2)

        help_text = small_font.render("任意键击中下落音符（或等待音符） | ESC退出", True, (200,200,200))
        screen.blit(help_text, (20, screen_height - 30))

        pygame.display.flip()
        clock.tick(60)

    # 退出清理
    if bgm_loaded:
        pygame.mixer.music.stop()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()