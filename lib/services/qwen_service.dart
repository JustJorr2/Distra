import 'dart:async';

import 'package:file_picker/file_picker.dart';
import 'package:llama_flutter_android/llama_flutter_android.dart';

class QwenService {
  final LlamaController _controller = LlamaController();

  bool _isModelLoaded = false;
  String? _modelPath;

  bool get isModelLoaded => _isModelLoaded;
  String? get modelPath => _modelPath;

  // Memilih file GGUF
  Future<String?> pickModelFile() async {
    final file = await FilePicker.pickFile(
      type: FileType.custom,
      allowedExtensions: ['gguf'],
    );

    return file?.path;
  }

  // Memuat model ke memori
  Future<void> loadModel(String path) async {
    await _controller.loadModel(
      modelPath: path,
      threads: 4,
      contextSize: 2048,
      gpuLayers: 0,
    );

    _modelPath = path;
    _isModelLoaded = true;
  }

  // Memilih sekaligus memuat model
  Future<String?> selectAndLoadModel() async {
    final path = await pickModelFile();

    if (path == null) {
      return null;
    }

    await loadModel(path);

    return path;
  }

  // Menghasilkan respons AI
  Stream<String> generateResponse(String prompt) {
    if (!_isModelLoaded) {
      throw StateError('Model Qwen belum dimuat.');
    }

    return _controller.generateChat(
      messages: [
        ChatMessage(
          role: 'system',
          content: 'You are a helpful AI assistant for disaster mitigation.',
        ),
        ChatMessage(
          role: 'user',
          content: prompt,
        ),
      ],
      template: 'chatml',
      maxTokens: 256,
      temperature: 0.7,
    );
  }

  // Menghentikan generasi
  Future<void> stopGeneration() async {
    await _controller.stop();
  }

  // Membersihkan resource
  Future<void> dispose() async {
    await _controller.dispose();

    _isModelLoaded = false;
    _modelPath = null;
  }
}