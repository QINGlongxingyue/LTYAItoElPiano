package com.example.ltyaitoelpiano

import android.content.Context
import android.media.midi.*
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.widget.TextView
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import com.example.ltyaitoelpiano.audio.AudioManager
import com.example.ltyaitoelpiano.model.MidiEvent
import com.example.ltyaitoelpiano.ui.PianoView
import com.example.ltyaitoelpiano.util.MidiJsonLoader
import com.example.ltyaitoelpiano.ui.theme.LTYAItoElPianoTheme

class MainActivity : ComponentActivity() {
    private var pianoView: PianoView? = null
    private lateinit var audioManager: AudioManager
    private lateinit var statusText: TextView
    private var midiEvents: List<MidiEvent> = emptyList()
    private var startRealTime = 0L
    private var pausedTimeOffset = 0f
    private var isPaused = false
    private var isWaiting = false
    private var waitingNoteIndex = -1
    private var waitingNotePitch = -1
    private var waitingEvent: MidiEvent? = null
    private val playedFlags = mutableSetOf<Int>()

    // 模式：0=等待模式, 1=演奏模式, 2=练习模式
    private var currentMode by mutableStateOf(0)
    private val modeNames = listOf("等待模式", "演奏模式", "练习模式")
    private var isBgmMuted by mutableStateOf(false)

    private lateinit var midiManager: MidiManager
    private var midiDevice: MidiDevice? = null
    private var midiOutputPort: MidiOutputPort? = null

    private val updateHandler = Handler(Looper.getMainLooper())
    private val updateRunnable = object : Runnable {
        override fun run() {
            val view = pianoView
            if (view == null) {
                updateHandler.postDelayed(this, 50)
                return
            }
            if (!isPaused && !isWaiting) {
                val nowReal = SystemClock.elapsedRealtime()
                val currentSec = (nowReal - startRealTime) / 1000f + pausedTimeOffset
                view.currentTime = currentSec
                view.playedIndices = playedFlags
                view.updateFallingNotes(currentSec)

                for ((idx, event) in midiEvents.withIndex()) {
                    if (event.start <= currentSec && idx !in playedFlags) {
                        val timeToBottom = currentSec - event.start
                        if (timeToBottom >= view.fallDuration) {
                            when (currentMode) {
                                1 -> autoHitNote(idx, event)          // 演奏模式：自动播放并消失
                                2 -> cleanNote(idx, event)            // 练习模式：落底直接消失（不播放）
                                else -> enterWaitMode(idx, event)     // 等待模式：暂停等待
                            }
                            break
                        }
                    }
                }
            }
            updateHandler.postDelayed(this, 16)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        midiEvents = MidiJsonLoader.loadFromAssets(this)

        audioManager = AudioManager(this)
        audioManager.loadNotes(midiEvents.size)
        audioManager.loadBgm()
        audioManager.startBgm(1200)

        startRealTime = SystemClock.elapsedRealtime()
        pausedTimeOffset = 0f
        isPaused = false

        setContent {
            LTYAItoElPianoTheme {
                Box(modifier = Modifier.fillMaxSize()) {
                    AndroidView(
                        factory = { context ->
                            PianoView(context, null).apply {
                                pianoView = this
                                events = midiEvents
                                setBackgroundColor(android.graphics.Color.BLACK)
                            }
                        },
                        modifier = Modifier.fillMaxSize()
                    )
                    AndroidView(
                        factory = { context ->
                            TextView(context).apply {
                                statusText = this
                                setTextColor(android.graphics.Color.WHITE)
                                textSize = 20f
                                setPadding(32, 32, 32, 32)
                                setBackgroundColor(android.graphics.Color.argb(180, 0, 0, 0))
                            }
                        }
                    )
                    // 三个按钮：右上角水平排列
                    Row(
                        modifier = Modifier
                            .align(Alignment.TopEnd)
                            .padding(16.dp),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        // 模式切换按钮
                        Button(onClick = {
                            currentMode = (currentMode + 1) % 3
                            // 如果切换到练习模式且处于等待状态，强制退出等待
                            if (currentMode == 2 && isWaiting) {
                                exitWaitingMode()
                            }
                        }) {
                            Text(modeNames[currentMode])
                        }
                        // 静音伴奏按钮
                        Button(onClick = {
                            isBgmMuted = !isBgmMuted
                            audioManager.setBgmMute(isBgmMuted)
                        }) {
                            Text(if (isBgmMuted) "取消静音" else "静音")
                        }
                        // 重新开始按钮
                        Button(onClick = { resetGame() }) {
                            Text("重开")
                        }
                    }
                }
            }
        }

        midiManager = getSystemService(Context.MIDI_SERVICE) as MidiManager
        connectToMidiKeyboard()

        updateHandler.post(updateRunnable)
    }

    private fun autoHitNote(index: Int, event: MidiEvent) {
        audioManager.playNote(index)
        markNoteAsPlayed(index)
    }

    // 练习模式落底清理：仅标记消失，不播放声音
    private fun cleanNote(index: Int, event: MidiEvent) {
        markNoteAsPlayed(index)
    }

    // 统一标记音符为已播放（消失）
    private fun markNoteAsPlayed(index: Int) {
        if (playedFlags.add(index)) {
            pianoView?.markNoteAsPlayedByIndex(index)
            pianoView?.playedIndices = playedFlags
        }
    }

    private fun exitWaitingMode() {
        isWaiting = false
        isPaused = false
        pianoView?.highlightNote = null
        audioManager.resumeBgm()
        statusText.text = ""
        waitingEvent = null
    }

    private fun resetGame() {
        if (isWaiting) exitWaitingMode()
        playedFlags.clear()
        startRealTime = SystemClock.elapsedRealtime()
        pausedTimeOffset = 0f
        pianoView?.playedIndices = emptySet()
        pianoView?.currentTime = 0f
        pianoView?.updateFallingNotes(0f)
        waitingNoteIndex = -1
        waitingNotePitch = -1
        waitingEvent = null
        audioManager.restartBgm()
        statusText.text = ""
    }

    inner class MidiInputReceiver(private val onNotePressed: (Int) -> Unit) : MidiReceiver() {
        override fun onSend(data: ByteArray, offset: Int, count: Int, timestamp: Long) {
            var i = offset
            while (i < offset + count) {
                val status = data[i].toInt() and 0xF0
                if (status == 0x90) {
                    if (i + 2 < offset + count) {
                        val pitch = data[i + 1].toInt() and 0x7F
                        val velocity = data[i + 2].toInt() and 0x7F
                        if (velocity > 0) {
                            runOnUiThread { onNotePressed(pitch) }
                        }
                    }
                    i += 3
                } else {
                    i++
                }
            }
        }
    }

    private fun connectToMidiKeyboard() {
        val devices = midiManager.devices
        var found = false
        for (deviceInfo in devices) {
            if (deviceInfo.outputPortCount > 0) {
                found = true
                midiManager.openDevice(deviceInfo, object : MidiManager.OnDeviceOpenedListener {
                    override fun onDeviceOpened(device: MidiDevice?) {
                        if (device == null) {
                            runOnUiThread {
                                Toast.makeText(this@MainActivity, "MIDI 设备打开失败", Toast.LENGTH_SHORT).show()
                            }
                            return
                        }
                        midiDevice = device
                        midiOutputPort = device.openOutputPort(0)
                        val receiver = MidiInputReceiver { pitch -> onMidiNotePressed(pitch) }
                        midiOutputPort?.connect(receiver)
                        runOnUiThread {
                            Toast.makeText(this@MainActivity, "MIDI 键盘已连接", Toast.LENGTH_SHORT).show()
                        }
                    }
                }, null)
                break
            }
        }
        if (!found) {
            runOnUiThread {
                Toast.makeText(this@MainActivity, "未检测到 MIDI 设备，请连接电钢琴", Toast.LENGTH_LONG).show()
            }
        }
    }

    private fun onMidiNotePressed(pitch: Int) {
        val now = (SystemClock.elapsedRealtime() - startRealTime) / 1000f + pausedTimeOffset
        val view = pianoView ?: return

        // 练习模式：弹奏匹配的音符（在有效时间窗口内）立即消失并播放声音
        if (currentMode == 2) {
            for ((idx, event) in midiEvents.withIndex()) {
                if (event.pitch == pitch && idx !in playedFlags &&
                    now >= event.start && now <= event.start + view.fallDuration) {
                    audioManager.playNote(idx)
                    markNoteAsPlayed(idx)
                    break
                }
            }
            return
        }

        // 等待模式：必须弹奏等待的正确音符
        if (currentMode == 0 && isWaiting) {
            if (pitch == waitingNotePitch) {
                hitWaitingNote()
            } else {
                statusText.text = "❌ 按错了！应该是 ${waitingNotePitch}"
                statusText.postDelayed({ if (isWaiting) statusText.text = "等待击中音符 ${waitingNotePitch}" }, 500)
            }
            return
        }

        // 演奏模式 或 等待模式下未等待时，提前命中
        for ((idx, event) in midiEvents.withIndex()) {
            if (event.pitch == pitch && idx !in playedFlags &&
                now >= event.start && now <= event.start + view.fallDuration) {
                audioManager.playNote(idx)
                markNoteAsPlayed(idx)
                break
            }
        }
    }

    private fun enterWaitMode(index: Int, event: MidiEvent) {
        isWaiting = true
        isPaused = true
        waitingNoteIndex = index
        waitingNotePitch = event.pitch
        waitingEvent = event
        pianoView?.highlightNote = event.pitch
        audioManager.pauseBgm()
        statusText.text = "🎹 请在电钢琴上弹奏音符 ${event.pitch}"
    }

    private fun hitWaitingNote() {
        if (waitingNoteIndex >= 0) {
            audioManager.playNote(waitingNoteIndex)
            markNoteAsPlayed(waitingNoteIndex)
            isWaiting = false
            isPaused = false
            pianoView?.highlightNote = null
            audioManager.resumeBgm()
            startRealTime = SystemClock.elapsedRealtime()
            pausedTimeOffset = pianoView?.currentTime ?: 0f
            statusText.text = ""
            waitingEvent = null
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        audioManager.release()
        updateHandler.removeCallbacks(updateRunnable)
        midiOutputPort?.close()
        midiDevice?.close()
    }
}