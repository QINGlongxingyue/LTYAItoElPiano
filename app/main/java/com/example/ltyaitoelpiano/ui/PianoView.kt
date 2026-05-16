package com.example.ltyaitoelpiano.ui

import android.content.Context
import android.graphics.*
import android.util.AttributeSet
import android.view.View
import com.example.ltyaitoelpiano.model.MidiEvent

class PianoView(context: Context, attrs: AttributeSet?) : View(context, attrs) {
    private val whiteRects = mutableListOf<RectF>()
    private val blackRects = mutableMapOf<Int, RectF>()
    private val noteToWhiteRect = mutableMapOf<Int, RectF>()

    private val whitePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.WHITE; style = Paint.Style.FILL }
    private val blackPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.BLACK; style = Paint.Style.FILL }
    private val strokePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.BLACK; style = Paint.Style.STROKE; strokeWidth = 2f }
    private val highlightPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.argb(120, 100, 150, 255); style = Paint.Style.FILL }

    var events: List<MidiEvent> = emptyList()
    var currentTime = 0f
    var highlightNote: Int? = null
    var fallDuration = 1.0f

    var playedIndices: Set<Int> = emptySet()
        set(value) {
            field = value
            for (note in fallingNotes) {
                if (!note.played && value.contains(note.eventIndex)) {
                    note.played = true
                }
            }
            invalidate()
        }

    data class FallingNote(
        val eventIndex: Int,
        val note: Int,
        val startTime: Float,
        val duration: Float,
        var rect: RectF? = null,
        var played: Boolean = false
    )
    private val fallingNotes = mutableListOf<FallingNote>()

    private var keyWidth = 0f
    private var pianoY = 0f
    private val minNote = 21
    private val maxNote = 108

    override fun onSizeChanged(w: Int, h: Int, oldw: Int, oldh: Int) {
        super.onSizeChanged(w, h, oldw, oldh)
        buildKeyRects(w.toFloat(), h.toFloat())
    }

    private fun buildKeyRects(width: Float, height: Float) {
        whiteRects.clear()
        blackRects.clear()
        noteToWhiteRect.clear()

        val whiteNoteList = (minNote..maxNote).filter { note -> note % 12 !in listOf(1,3,6,8,10) }
        val numWhite = whiteNoteList.size
        keyWidth = width / numWhite
        pianoY = height - 150f

        for ((i, note) in whiteNoteList.withIndex()) {
            val left = i * keyWidth
            val rect = RectF(left, pianoY, left + keyWidth, pianoY + 120f)
            whiteRects.add(rect)
            noteToWhiteRect[note] = rect
        }

        for (i in 0 until numWhite - 1) {
            val leftNote = whiteNoteList[i]
            val rightNote = whiteNoteList[i+1]
            if (rightNote - leftNote == 2) {
                val blackNote = leftNote + 1
                if (blackNote in minNote..maxNote) {
                    val leftRect = noteToWhiteRect[leftNote]!!
                    val x = leftRect.right - keyWidth * 0.3f
                    val rect = RectF(x, pianoY, x + keyWidth * 0.6f, pianoY + 80f)
                    blackRects[blackNote] = rect
                }
            }
        }
    }

    private fun getKeyRect(note: Int): RectF? = blackRects[note] ?: noteToWhiteRect[note]

    fun updateFallingNotes(now: Float) {
        fallingNotes.removeAll { it.played || now > it.startTime + fallDuration + 0.5f }

        for ((idx, event) in events.withIndex()) {
            if (event.start <= now && idx !in playedIndices &&
                !fallingNotes.any { it.eventIndex == idx }) {
                fallingNotes.add(
                    FallingNote(
                        eventIndex = idx,
                        note = event.pitch,
                        startTime = event.start,
                        duration = (event.end - event.start).coerceAtLeast(0.1f) // 避免0时长
                    )
                )
            }
        }

        for (note in fallingNotes) {
            if (note.played) continue
            val progress = ((now - note.startTime) / fallDuration).coerceIn(0f, 1f)
            val targetRect = getKeyRect(note.note) ?: continue
            val y = targetRect.top * progress
            val x = targetRect.centerX() - keyWidth * 0.4f
            // 动态高度：最短50px，最长180px，基于 duration 线性映射
            val height = (note.duration * 100).coerceIn(50f, 180f)
            note.rect = RectF(x, y, x + keyWidth * 0.8f, y + height)
        }
        invalidate()
    }

    fun markNoteAsPlayedByIndex(index: Int) {
        for (note in fallingNotes) {
            if (!note.played && note.eventIndex == index) {
                note.played = true
                break
            }
        }
        invalidate()
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        for (rect in whiteRects) {
            canvas.drawRect(rect, whitePaint)
            canvas.drawRect(rect, strokePaint)
        }
        for (rect in blackRects.values) {
            canvas.drawRect(rect, blackPaint)
            canvas.drawRect(rect, strokePaint)
        }
        highlightNote?.let { note ->
            getKeyRect(note)?.let { canvas.drawRect(it, highlightPaint) }
        }
        val notePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.rgb(70, 170, 250) }
        val borderPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.WHITE; style = Paint.Style.STROKE; strokeWidth = 2f }
        for (fall in fallingNotes) {
            if (fall.played) continue
            fall.rect?.let { rect ->
                canvas.drawRect(rect, notePaint)
                canvas.drawRect(rect, borderPaint)
            }
        }
    }
}