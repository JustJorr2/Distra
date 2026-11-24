
import 'dart:async';

import 'package:flutter/services.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:material_ui/material_ui.dart';

import '../services/qwen_service.dart';

class AIAnalysisScreen extends StatefulWidget {
  const AIAnalysisScreen({super.key});

  @override
  State<AIAnalysisScreen> createState() => _AIAnalysisScreenState();
}

class _AIAnalysisScreenState extends State<AIAnalysisScreen> {
  final QwenService _qwenService = QwenService();

  final TextEditingController _promptController =
      TextEditingController();

  final ScrollController _scrollController = ScrollController();

  StreamSubscription<String>? _generationSubscription;

  final List<_ChatMessage> _messages = [];

  String _modelName = 'No model selected';

  bool _isLoadingModel = false;
  bool _isGenerating = false;

  @override
  void initState() {
    super.initState();
    _restoreModel();
  }

  // Memulihkan model yang sebelumnya digunakan.
  Future<void> _restoreModel() async {
    setState(() {
      _isLoadingModel = true;
    });

    try {
      final restored = await _qwenService.restoreModel();

      if (!mounted) return;

      if (restored) {
        setState(() {
          _modelName = _qwenService.modelPath
                  ?.split(RegExp(r'[/\\]'))
                  .last ??
              'Previously loaded model';
        });
      }
    } catch (e) {
      _showMessage('Failed to restore model: $e');
    } finally {
      if (mounted) {
        setState(() {
          _isLoadingModel = false;
        });
      }
    }
  }

  // Memilih dan memuat model GGUF.
  Future<void> _selectAndLoadModel() async {
    setState(() {
      _isLoadingModel = true;
    });

    try {
      final path = await _qwenService.selectAndLoadModel();

      if (!mounted) return;

      if (path == null) {
        _showMessage('Model selection cancelled.');
        return;
      }

      setState(() {
        _modelName = path.split(RegExp(r'[/\\]')).last;
        _messages.clear();
      });

      _showMessage('Model loaded successfully.');
    } catch (e) {
      _showMessage('Failed to load model: $e');
    } finally {
      if (mounted) {
        setState(() {
          _isLoadingModel = false;
        });
      }
    }
  }

  // Mengirim pesan pengguna.
  Future<void> _sendMessage() async {
    final prompt = _promptController.text.trim();

    if (prompt.isEmpty || _isGenerating) return;

    if (!_qwenService.isModelLoaded) {
      _showMessage('Please load a model first.');
      return;
    }

    _promptController.clear();

    final assistantIndex = _messages.length + 1;

    setState(() {
      _messages.add(
        _ChatMessage(
          content: prompt,
          isUser: true,
        ),
      );

      // Menyediakan bubble kosong untuk respons AI.
      _messages.add(
        _ChatMessage(
          content: '',
          isUser: false,
        ),
      );

      _isGenerating = true;
    });

    _scrollToBottom();

    try {
      _generationSubscription = _qwenService
          .generateResponse(prompt)
          .listen(
        (token) {
          if (!mounted) return;

          setState(() {
            _messages[assistantIndex].content += token;
          });

          _scrollToBottom();
        },
        onError: (error) {
          if (!mounted) return;

          setState(() {
            _isGenerating = false;

            if (_messages[assistantIndex].content.isEmpty) {
              _messages.removeAt(assistantIndex);
            }
          });

          _showMessage('Generation error: $error');
        },
        onDone: () {
          if (!mounted) return;

          setState(() {
            _isGenerating = false;
          });

          _scrollToBottom();
        },
      );
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _isGenerating = false;

        if (assistantIndex < _messages.length &&
            _messages[assistantIndex].content.isEmpty) {
          _messages.removeAt(assistantIndex);
        }
      });

      _showMessage('Error: $e');
    }
  }

  // Menghentikan generasi AI.
  Future<void> _stopGeneration() async {
    await _qwenService.stopGeneration();
    await _generationSubscription?.cancel();

    if (!mounted) return;

    setState(() {
      _isGenerating = false;
    });
  }

  // Memulai percakapan baru.
  void _startNewChat() {
    if (_isGenerating) return;

    _qwenService.clearConversation();

    setState(() {
      _messages.clear();
      _promptController.clear();
    });

    _scrollToBottom();
  }

  // Menyalin respons AI.
  Future<void> _copyMessage(String content) async {
    if (content.trim().isEmpty) return;

    await Clipboard.setData(
      ClipboardData(text: content),
    );

    if (!mounted) return;

    _showMessage('Response copied to clipboard.');
  }

  // Mengikuti pesan terbaru.
  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;

      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 200),
        curve: Curves.easeOut,
      );
    });
  }

  void _showMessage(String message) {
    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  @override
  void dispose() {
    _generationSubscription?.cancel();
    _promptController.dispose();
    _scrollController.dispose();
    unawaited(_qwenService.dispose());

    super.dispose();
  }

  // Informasi model.
  Widget _buildModelStatus() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Icon(
              _qwenService.isModelLoaded
                  ? Icons.check_circle
                  : Icons.memory,
              color: _qwenService.isModelLoaded
                  ? Colors.green
                  : Colors.grey,
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Local AI Model',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(
                    _isLoadingModel
                        ? 'Loading model...'
                        : _modelName,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 12,
                      color: Colors.grey,
                    ),
                  ),
                ],
              ),
            ),
            if (_isLoadingModel)
              const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                ),
              )
            else
              IconButton(
                onPressed: _isGenerating
                    ? null
                    : _selectAndLoadModel,
                tooltip: 'Select model',
                icon: const Icon(Icons.folder_open),
              ),
          ],
        ),
      ),
    );
  }

  // Tampilan ketika belum ada percakapan.
  Widget _buildWelcomeScreen() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.auto_awesome,
              size: 48,
              color: Theme.of(context).colorScheme.primary,
            ),
            const SizedBox(height: 16),
            const Text(
              'Halo, saya Distra!',
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Saya siap membantu kamu memahami bencana alam, '
              'kesiapsiagaan, dan mitigasi bencana.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }

  // Bubble pesan pengguna.
  Widget _buildUserMessage(String content) {
    return Align(
      alignment: Alignment.centerRight,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.78,
        ),
        margin: const EdgeInsets.symmetric(vertical: 6),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.primaryContainer,
          borderRadius: BorderRadius.circular(16).copyWith(
            bottomRight: const Radius.circular(4),
          ),
        ),
        child: SelectableText(content),
      ),
    );
  }

  // Bubble respons AI.
  Widget _buildAIMessage(String content) {
    final isEmpty = content.isEmpty;

    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.88,
        ),
        margin: const EdgeInsets.symmetric(vertical: 6),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(16).copyWith(
            bottomLeft: const Radius.circular(4),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.auto_awesome,
                  size: 16,
                  color: Theme.of(context).colorScheme.primary,
                ),
                const SizedBox(width: 6),
                const Text(
                  'Distra',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                  ),
                ),
                const Spacer(),
                IconButton(
                  onPressed: isEmpty
                      ? null
                      : () => _copyMessage(content),
                  tooltip: 'Copy response',
                  visualDensity: VisualDensity.compact,
                  icon: const Icon(
                    Icons.copy,
                    size: 17,
                  ),
                ),
              ],
            ),
            if (isEmpty && _isGenerating)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 8),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                      ),
                    ),
                    SizedBox(width: 10),
                    Text(
                      'Distra sedang mengetik...',
                      style: TextStyle(color: Colors.grey),
                    ),
                  ],
                ),
              )
            else if (content.isNotEmpty)
              MarkdownBody(
                data: content,
                selectable: true,
              ),
          ],
        ),
      ),
    );
  }

  // Daftar seluruh pesan.
  Widget _buildMessageList() {
    if (_messages.isEmpty) {
      return _buildWelcomeScreen();
    }

    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.symmetric(
        horizontal: 4,
        vertical: 12,
      ),
      itemCount: _messages.length,
      itemBuilder: (context, index) {
        final message = _messages[index];

        return message.isUser
            ? _buildUserMessage(message.content)
            : _buildAIMessage(message.content);
      },
    );
  }

  // Input pesan.
  Widget _buildMessageComposer() {
    final canSend = _qwenService.isModelLoaded &&
        !_isLoadingModel &&
        !_isGenerating;

    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.only(top: 8),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Expanded(
              child: TextField(
                controller: _promptController,
                enabled: canSend,
                minLines: 1,
                maxLines: 4,
                textCapitalization: TextCapitalization.sentences,
                decoration: InputDecoration(
                  hintText: canSend
                      ? 'Tanyakan sesuatu kepada Distra...'
                      : 'Muat model terlebih dahulu...',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                  ),
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 12,
                  ),
                ),
                onSubmitted: (_) => _sendMessage(),
              ),
            ),
            const SizedBox(width: 8),
            SizedBox(
              height: 48,
              width: 48,
              child: IconButton.filled(
                onPressed: _isGenerating
                    ? _stopGeneration
                    : canSend
                        ? _sendMessage
                        : null,
                tooltip: _isGenerating
                    ? 'Stop generation'
                    : 'Send message',
                icon: Icon(
                  _isGenerating ? Icons.stop : Icons.send,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Distra',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            Text(
              'Natural Disaster Assistant',
              style: TextStyle(fontSize: 11),
            ),
          ],
        ),
        actions: [
          IconButton(
            onPressed: _isGenerating || _messages.isEmpty
                ? null
                : _startNewChat,
            tooltip: 'New chat',
            icon: const Icon(Icons.add_comment_outlined),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
        child: Column(
          children: [
            _buildModelStatus(),
            const SizedBox(height: 8),
            Expanded(
              child: _buildMessageList(),
            ),
            const SizedBox(height: 8),
            _buildMessageComposer(),
          ],
        ),
      ),
    );
  }
}

class _ChatMessage {
  _ChatMessage({
    required this.content,
    required this.isUser,
  });

  String content;
  final bool isUser;
}
