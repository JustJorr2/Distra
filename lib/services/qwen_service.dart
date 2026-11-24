
import 'dart:async';
import 'package:file_picker/file_picker.dart';
import 'package:llama_flutter_android/llama_flutter_android.dart';
import '../config/personalization.dart';
import 'dart:io';
import 'package:shared_preferences/shared_preferences.dart';

class QwenService {
  final LlamaController _controller = LlamaController();

  bool _isModelLoaded = false;
  String? _modelPath;

  // Menyimpan riwayat percakapan selama sesi aktif.
  final List<ChatMessage> _conversationHistory = [];

  bool get isModelLoaded => _isModelLoaded;
  String? get modelPath => _modelPath;

  int get conversationLength => _conversationHistory.length;


  // Memilih file GGUF.
  Future<String?> pickModelFile() async {
    final files = await FilePicker.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['gguf'],
    );

    if (files.isEmpty) {
      return null;
    }

    return files.first.path;
  }

  // Memulihkan model setelah hot restart.
  Future<bool> restoreModel() async {
    final prefs = await SharedPreferences.getInstance();
    final savedPath = prefs.getString('qwen_model_path');

    // Periksa apakah model masih berada di native memory.
    final nativeLoaded = await _controller.isModelLoaded();

    if (nativeLoaded) {
      _isModelLoaded = true;
      _modelPath = savedPath;
      return true;
    }

    // Jika tidak ada model di memory, gunakan path tersimpan.
    if (savedPath == null || !await File(savedPath).exists()) {
      return false;
    }

    await loadModel(savedPath);
    return true;
  }

  // Memuat model ke memori.
  Future<void> loadModel(String path) async {
    await _controller.loadModel(
      modelPath: path,
      threads: 4,
      contextSize: 2048,
      gpuLayers: 0,
    );

    _modelPath = path;
    _isModelLoaded = true;

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('qwen_model_path', path);

    clearConversation();
  }

  // Memilih sekaligus memuat model.
  Future<String?> selectAndLoadModel() async {
    final path = await pickModelFile();

    if (path == null) {
      return null;
    }

    await loadModel(path);

    return path;
  }

  // Menghasilkan respons dengan konteks percakapan.
  Stream<String> generateResponse(String prompt) async* {
    if (!_isModelLoaded) {
      throw StateError('Model Qwen belum dimuat.');
    }

    final userMessage = ChatMessage(
      role: 'user',
      content: prompt,
    );

    _conversationHistory.add(userMessage);

    final responseBuffer = StringBuffer();

    try {
      await for (final token in _controller.generateChat(
        messages: [
          ChatMessage(
            role: 'system',
            content: '''
          ${Personalization.systemPrompt}

          /no_think

          IMPORTANT:
          - Do not generate or display a <think> section.
          - Respond directly with the final answer.
          - Do not include internal reasoning in the response.
          ''',
          ),
          ..._conversationHistory,
        ],
        template: 'chatml',
        maxTokens: 512,
        temperature: 0.7,
      )) {
        responseBuffer.write(token);
        yield token;
      }

      final response = responseBuffer.toString();

      if (response.isNotEmpty) {
        _conversationHistory.add(
          ChatMessage(
            role: 'assistant',
            content: response,
          ),
        );
      }
    } catch (_) {
      // Menghapus pesan pengguna jika generasi gagal.
      if (_conversationHistory.isNotEmpty &&
          identical(_conversationHistory.last, userMessage)) {
        _conversationHistory.removeLast();
      }

      rethrow;
    }
  }

  // Memulai percakapan baru.
  void clearConversation() {
    _conversationHistory.clear();
  }

  // Menghentikan generasi.
  Future<void> stopGeneration() async {
    await _controller.stop();
  }

  // Membersihkan resource.
  Future<void> dispose() async {
    await _controller.dispose();

    _conversationHistory.clear();
    _isModelLoaded = false;
    _modelPath = null;
  }
}
