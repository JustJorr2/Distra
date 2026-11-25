
import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

class ChatStorageService {
  ChatStorageService._();

  static const String _storageKey = 'distra_chat_messages_v1';

  /// Menyimpan seluruh pesan percakapan.
  static Future<void> saveMessages(
    List<Map<String, dynamic>> messages,
  ) async {
    final prefs = await SharedPreferences.getInstance();

    await prefs.setString(
      _storageKey,
      jsonEncode(messages),
    );
  }

  /// Mengambil kembali pesan yang tersimpan.
  static Future<List<Map<String, dynamic>>> loadMessages() async {
    final prefs = await SharedPreferences.getInstance();

    final savedData = prefs.getString(_storageKey);

    if (savedData == null || savedData.isEmpty) {
      return [];
    }

    try {
      final decoded = jsonDecode(savedData);

      if (decoded is! List) {
        return [];
      }

      return decoded
          .whereType<Map>()
          .map((item) => Map<String, dynamic>.from(item))
          .toList();
    } catch (e) {
      return [];
    }
  }

  /// Menghapus seluruh percakapan tersimpan.
  static Future<void> clearMessages() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_storageKey);
  }
}
