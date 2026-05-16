package com.example.ltyaitoelpiano.audio

import android.content.Context
import android.media.AudioAttributes
import android.media.MediaPlayer
import android.media.SoundPool
import android.os.Handler
import android.os.Looper

class AudioManager(private val context: Context) {
    private var bgmPlayer: MediaPlayer? = null
    private var soundPool: SoundPool? = null
    private val soundMap = mutableMapOf<Int, Int>()
    private var bgmPendingStart = false
    private var isBgmMuted = false   // 静音状态标志

    init {
        val audioAttributes = AudioAttributes.Builder()
            .setUsage(AudioAttributes.USAGE_GAME)
            .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
            .build()
        soundPool = SoundPool.Builder()
            .setMaxStreams(8)
            .setAudioAttributes(audioAttributes)
            .build()
    }

    fun loadNotes(count: Int) {
        for (i in 1..count) {
            val fileName = "cut_notes/note_${String.format("%04d", i)}.wav"
            try {
                val afd = context.assets.openFd(fileName)
                val soundId = soundPool?.load(afd, 1) ?: continue
                soundMap[i - 1] = soundId
            } catch (e: Exception) {
                // 忽略缺失文件
            }
        }
    }

    fun playNote(index: Int) {
        val soundId = soundMap[index] ?: return
        soundPool?.play(soundId, 1.0f, 1.0f, 0, 0, 1.0f)
    }

    fun loadBgm() {
        try {
            val afd = context.assets.openFd("banzo.wav")
            bgmPlayer = MediaPlayer().apply {
                setDataSource(afd.fileDescriptor, afd.startOffset, afd.length)
                prepare()
                isLooping = true
                // 应用当前静音状态
                setVolume(if (isBgmMuted) 0f else 1f, if (isBgmMuted) 0f else 1f)
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    fun startBgm(delayMs: Long = 0) {
        if (delayMs > 0) {
            bgmPendingStart = true
            Handler(Looper.getMainLooper()).postDelayed({
                if (bgmPendingStart) {
                    bgmPlayer?.start()
                    bgmPendingStart = false
                }
            }, delayMs)
        } else {
            bgmPlayer?.start()
        }
    }

    fun pauseBgm() {
        bgmPlayer?.let { if (it.isPlaying) it.pause() }
        bgmPendingStart = false
    }

    fun resumeBgm() {
        bgmPlayer?.let { if (!it.isPlaying) it.start() }
    }

    fun stopBgm() {
        bgmPlayer?.stop()
        bgmPlayer?.release()
        bgmPlayer = null
    }

    // 静音/取消静音伴奏
    fun setBgmMute(mute: Boolean) {
        isBgmMuted = mute
        val volume = if (mute) 0f else 1f
        bgmPlayer?.setVolume(volume, volume)
    }

    // 重新开始伴奏（从头播放，无延迟）
    fun restartBgm() {
        stopBgm()
        loadBgm()
        startBgm(0)  // 立即播放
    }

    fun release() {
        soundPool?.release()
        bgmPlayer?.release()
    }
}