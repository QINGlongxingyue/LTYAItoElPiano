import json
import mido

def export_midi_events(midi_path, json_path):
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
    ticks_per_sec = ticks_per_beat * (1000000.0 / tempo)

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
                    start_sec = start_ticks / ticks_per_sec
                    end_sec = abs_ticks / ticks_per_sec
                    events.append({
                        "pitch": msg.note,
                        "start": round(start_sec, 3),
                        "end": round(end_sec, 3)
                    })
    events.sort(key=lambda x: x["start"])
    with open(json_path, 'w') as f:
        json.dump(events, f, indent=2)
    print(f"导出 {len(events)} 个音符事件到 {json_path}")

export_midi_events("test.mid", "midi_events.json")