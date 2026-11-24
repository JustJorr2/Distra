
import 'dart:async';
import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:llama_flutter_android/llama_flutter_android.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../config/personalization.dart';

class QwenService {
  final LlamaController _controller = LlamaController();

  bool _isModelLoaded = false;
  String? _modelPath;

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

    if (files.isEmpty) return null;

    return files.first.path;
  }

  // Memulihkan model setelah hot restart.
  Future<bool> restoreModel() async {
    final prefs = await SharedPreferences.getInstance();
    final savedPath = prefs.getString('qwen_model_path');

    final nativeLoaded = await _controller.isModelLoaded();

    if (nativeLoaded) {
      _isModelLoaded = true;
      _modelPath = savedPath;
      return true;
    }

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
      contextSize: 4096,
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

    if (path == null) return null;

    await loadModel(path);

    return path;
  }

  // Mencari panjang akhiran yang mungkin merupakan
  // bagian awal dari tag think.
  int _longestSuffixPrefix(String text, String marker) {
    final maxLength = text.length < marker.length - 1
        ? text.length
        : marker.length - 1;

    for (int length = maxLength; length > 0; length--) {
      if (text.endsWith(marker.substring(0, length))) {
        return length;
      }
    }

    return 0;
  }

  // Menyaring blok <think>...</think> selama streaming.
  Stream<String> _filterThinkTags(Stream<String> source) async* {
    const startTag = '<think>';
    const endTag = '</think>';

    String pending = '';
    bool insideThink = false;

    await for (final token in source) {
      pending += token;

      while (pending.isNotEmpty) {
        final lowerPending = pending.toLowerCase();

        if (insideThink) {
          final endIndex = lowerPending.indexOf(endTag);

          if (endIndex != -1) {
            pending = pending.substring(endIndex + endTag.length);
            insideThink = false;
            continue;
          }

          // Pertahankan kemungkinan potongan tag penutup.
          final keepLength = _longestSuffixPrefix(
            lowerPending,
            endTag,
          );

          pending = keepLength == 0
              ? ''
              : pending.substring(pending.length - keepLength);

          break;
        }

        final startIndex = lowerPending.indexOf(startTag);

        if (startIndex != -1) {
          final visibleText = pending.substring(0, startIndex);

          if (visibleText.isNotEmpty) {
            yield visibleText;
          }

          pending = pending.substring(startIndex + startTag.length);
          insideThink = true;
          continue;
        }

        // Jangan keluarkan karakter yang mungkin merupakan
        // awal tag <think> yang terpecah antar-token.
        final keepLength = _longestSuffixPrefix(
          lowerPending,
          startTag,
        );

        final safeLength = pending.length - keepLength;

        if (safeLength > 0) {
          yield pending.substring(0, safeLength);
        }

        pending = keepLength == 0
            ? ''
            : pending.substring(safeLength);

        break;
      }
    }

    // Keluarkan sisa teks jika bukan bagian dari blok think.
    if (!insideThink && pending.isNotEmpty) {
      yield pending;
    }
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
      final rawStream = _controller.generateChat(
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
      );

      await for (final token in _filterThinkTags(rawStream)) {
        responseBuffer.write(token);
        yield token;
      }

      final response = responseBuffer.toString().trim();

      if (response.isNotEmpty) {
        _conversationHistory.add(
          ChatMessage(
            role: 'assistant',
            content: response,
          ),
        );
      }
    } catch (_) {
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
