package com.example.ltyaitoelpiano.util

import android.content.Context
import com.example.ltyaitoelpiano.model.MidiEvent
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken

object MidiJsonLoader {
    fun loadFromAssets(context: Context): List<MidiEvent> {
        val jsonString = context.assets.open("midi_events.json").bufferedReader().use { it.readText() }
        val type = object : TypeToken<List<MidiEvent>>() {}.type
        return Gson().fromJson(jsonString, type)
    }
}