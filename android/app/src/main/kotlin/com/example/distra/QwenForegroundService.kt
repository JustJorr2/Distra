
package com.example.distra

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder

class QwenForegroundService : Service() {

    companion object {
        const val CHANNEL_ID = "distra_qwen_channel"
        const val NOTIFICATION_ID = 1001

        const val ACTION_START = "com.example.distra.START_QWEN"
        const val ACTION_STOP = "com.example.distra.STOP_QWEN"
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onStartCommand(
        intent: Intent?,
        flags: Int,
        startId: Int
    ): Int {

        when (intent?.action) {
            ACTION_STOP -> {
                stopForeground(STOP_FOREGROUND_REMOVE)
                stopSelf()
                return START_NOT_STICKY
            }

            ACTION_START -> {
                startForeground(
                    NOTIFICATION_ID,
                    createNotification()
                )
            }
        }

        return START_NOT_STICKY
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Distra AI",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Status proses generasi AI Distra"
            }

            val manager = getSystemService(
                NotificationManager::class.java
            )

            manager.createNotificationChannel(channel)
        }
    }

    private fun createNotification(): Notification {
        return Notification.Builder(this, CHANNEL_ID)
            .setContentTitle("Distra AI")
            .setContentText("Sedang menghasilkan jawaban...")
            .setSmallIcon(android.R.drawable.stat_notify_sync)
            .setOngoing(true)
            .build()
    }

    override fun onTaskRemoved(rootIntent: Intent?) {
        // Pengguna menghapus Distra dari Recent Apps.
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
        super.onTaskRemoved(rootIntent)
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
