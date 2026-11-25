
import 'package:flutter/services.dart';

class QwenBackgroundManager {
  QwenBackgroundManager._();

  static const MethodChannel _channel = MethodChannel(
    'com.example.distra/qwen_service',
  );

  static bool _isRunning = false;

  static bool get isRunning => _isRunning;

  /// Memulai Android Foreground Service.
  static Future<void> startService() async {
    if (_isRunning) return;

    final result = await _channel.invokeMethod<bool>(
      'startService',
    );

    if (result == true) {
      _isRunning = true;
    } else {
      throw Exception('Gagal memulai Qwen Background Service.');
    }
  }

  /// Menghentikan Android Foreground Service.
  static Future<void> stopService() async {
    if (!_isRunning) return;

    final result = await _channel.invokeMethod<bool>(
      'stopService',
    );

    if (result == true) {
      _isRunning = false;
    }
  }
}
