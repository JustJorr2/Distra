
package com.example.distra

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {

    private val CHANNEL = "com.example.distra/qwen_service"
    private val NOTIFICATION_PERMISSION_REQUEST = 1001

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        requestNotificationPermission()
    }

    private fun requestNotificationPermission() {
        if (Build.VERSION.SDK_INT >= 33) {
            val permission = Manifest.permission.POST_NOTIFICATIONS

            val alreadyGranted = checkSelfPermission(permission) ==
                PackageManager.PERMISSION_GRANTED

            if (!alreadyGranted) {
                requestPermissions(
                    arrayOf(permission),
                    NOTIFICATION_PERMISSION_REQUEST
                )
            }
        }
    }

    override fun configureFlutterEngine(
        flutterEngine: FlutterEngine
    ) {
        super.configureFlutterEngine(flutterEngine)

        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            CHANNEL
        ).setMethodCallHandler { call, result ->

            when (call.method) {

                "startService" -> {
                    val intent = Intent(
                        this,
                        QwenForegroundService::class.java
                    ).apply {
                        action = QwenForegroundService.ACTION_START
                    }

                    try {
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                            startForegroundService(intent)
                        } else {
                            startService(intent)
                        }

                        result.success(true)
                    } catch (e: Exception) {
                        result.error(
                            "SERVICE_START_ERROR",
                            e.message,
                            null
                        )
                    }
                }

                "stopService" -> {
                    val intent = Intent(
                        this,
                        QwenForegroundService::class.java
                    )

                    stopService(intent)
                    result.success(true)
                }

                else -> result.notImplemented()
            }
        }
    }
}
