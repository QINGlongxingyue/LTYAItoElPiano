import mido
import os
import sys
from pydub import AudioSegment

def parse_midi_events(midi_path):
    """返回 events (start_sec, end_sec, pitch) 列表和 MIDI 总时长"""
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

    # 计算 MIDI 总时长
    total_ticks = 0
    for track in mid.tracks:
        t = 0
        for msg in track:
            t += msg.time
        total_ticks = max(total_ticks, t)
    mid_duration = total_ticks / ticks_per_second

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
    return events, mid_duration

def cut_audio_precise(audio_path, events, output_dir="cut_notes", fade_ms=2):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    ext = os.path.splitext(audio_path)[1].lower()
    if ext == '.mp3':
        audio = AudioSegment.from_mp3(audio_path)
    elif ext == '.wav':
        audio = AudioSegment.from_wav(audio_path)
    else:
        raise ValueError("只支持 .wav 或 .mp3")

    audio_duration = len(audio) / 1000.0
    print(f"音频总时长: {audio_duration:.2f}s")

    for idx, (start, end, pitch) in enumerate(events, start=1):
        start_ms = start * 1000
        end_ms = end * 1000
        if end_ms > audio_duration * 1000:
            print(f"警告: 音符 {idx} 结束时间 {end_ms:.0f}ms 超出音频长度，已截断")
            end_ms = audio_duration * 1000
        if end_ms <= start_ms:
            seg = AudioSegment.silent(duration=10)
        else:
            seg = audio[start_ms:end_ms]
            if fade_ms > 0 and len(seg) > 2 * fade_ms:
                seg = seg.fade_in(fade_ms).fade_out(fade_ms)
        out_path = os.path.join(output_dir, f"note_{idx:04d}.wav")
        seg.export(out_path, format="wav")
        print(f"导出 {out_path}  (音高={pitch}, 时长={len(seg)}ms)")

    print(f"完成！共导出 {len(events)} 个片段到 {output_dir}/")

if __name__ == "__main__":
    midi_file = "test.mid"
    audio_file = "test.wav"   # 或 test.mp3
    if not os.path.exists(midi_file) or not os.path.exists(audio_file):
        print("请确保当前目录有 test.mid 和 test.wav 文件")
        sys.exit(1)

    # 获取音频长度
    ext = os.path.splitext(audio_file)[1].lower()
    if ext == '.mp3':
        tmp = AudioSegment.from_mp3(audio_file)
    else:
        tmp = AudioSegment.from_wav(audio_file)
    audio_len = len(tmp) / 1000.0
    del tmp

    print("解析 MIDI...")
    events, mid_duration = parse_midi_events(midi_file)
    print(f"MIDI 总时长: {mid_duration:.2f}s")
    print(f"共找到 {len(events)} 个音符事件")

    # 检查对齐：允许 0.5 秒误差，否则报错
    if abs(audio_len - mid_duration) > 0.5:
        print(f"错误：音频长度 ({audio_len:.2f}s) 与 MIDI 总时长 ({mid_duration:.2f}s) 相差过大！")
        print("请使用 DAW 或音频编辑器将音频裁剪到与 MIDI 完全等长，然后重新运行。")
        sys.exit(1)
    else:
        print("对齐检查通过。")

    cut_audio_precise(audio_file, events, fade_ms=2)