
import 'dart:async';

import 'package:flutter/services.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:material_ui/material_ui.dart';

import '../services/qwen_service.dart';
import '../services/chat_storage_service.dart';

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

  // Mengubah daftar pesan menjadi format penyimpanan.
  List<Map<String, String>> _conversationData() {
    return _messages
        .where((message) => message.content.trim().isNotEmpty)
        .map(
          (message) => {
            'role': message.isUser ? 'user' : 'assistant',
            'content': message.content,
          },
        )
        .toList();
  }

  // Menyimpan percakapan ke penyimpanan lokal.
  Future<void> _saveChat() async {
    await ChatStorageService.saveMessages(_conversationData());
  }

  // Menyamakan riwayat Qwen dengan pesan yang tampil di layar.
  void _syncQwenConversation() {
    _qwenService.replaceConversation(_conversationData());
  }


  // Memulihkan model yang sebelumnya digunakan.
  Future<void> _restoreModel() async {
    setState(() {
      _isLoadingModel = true;
    });

    try {
      // Memulihkan percakapan yang tersimpan.
      final savedMessages = await ChatStorageService.loadMessages();

      if (!mounted) return;

      setState(() {
        _messages
          ..clear()
          ..addAll(
            savedMessages.map(
              (message) => _ChatMessage(
                content: message['content'] ?? '',
                isUser: message['role'] == 'user',
              ),
            ),
          );
      });

      // Memulihkan model Qwen.
      final restored = await _qwenService.restoreModel();

      if (!mounted) return;

      if (restored) {
        setState(() {
          _modelName = _qwenService.modelPath
                  ?.split(RegExp(r'[/\\]'))
                  .last ??
              'Previously loaded model';
        });

        _syncQwenConversation();
      }
    } catch (e) {
      _showMessage('Failed to restore conversation: $e');
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

      await ChatStorageService.clearMessages();

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
  Future<void> _sendMessage({String? promptOverride}) async {
    final prompt = (promptOverride ?? _promptController.text).trim();

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

      _messages.add(
        _ChatMessage(
          content: '',
          isUser: false,
        ),
      );

      _isGenerating = true;
    });

    // Simpan pertanyaan sebelum proses generasi.
    unawaited(_saveChat());

    _scrollToBottom();

    try {
      _generationSubscription = _qwenService
          .generateResponse(prompt)
          .listen(
        (token) {
          if (!mounted || assistantIndex >= _messages.length) return;

          setState(() {
            _messages[assistantIndex].content += token;
          });

          _scrollToBottom();
        },
        onError: (error) {
          if (!mounted) return;

          setState(() {
            _isGenerating = false;

            if (assistantIndex < _messages.length &&
                _messages[assistantIndex].content.isEmpty) {
              _messages.removeAt(assistantIndex);
            }
          });

          _syncQwenConversation();
          unawaited(_saveChat());

          _showMessage('Generation error: $error');
        },
        onDone: () {
          if (!mounted) return;

          setState(() {
            _isGenerating = false;
          });

          _syncQwenConversation();
          unawaited(_saveChat());

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

      _syncQwenConversation();
      unawaited(_saveChat());

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

    _syncQwenConversation();
    await _saveChat();
  }

  // Memulai percakapan baru.
  Future<void> _startNewChat() async {
    if (_isGenerating) return;

    _qwenService.clearConversation();

    setState(() {
      _messages.clear();
      _promptController.clear();
    });

    await ChatStorageService.clearMessages();

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


// Menghapus pesan beserta pasangan percakapannya.
  Future<void> _deleteMessage(int index) async {
    if (_isGenerating || index < 0 || index >= _messages.length) {
      return;
    }

    final message = _messages[index];

    int startIndex;
    int endIndex;

    if (message.isUser) {
      startIndex = index;
      endIndex = index + 1;

      // Hapus jawaban AI yang mengikuti pertanyaan.
      if (endIndex < _messages.length &&
          !_messages[endIndex].isUser) {
        endIndex++;
      }
    } else {
      // Jika memilih jawaban AI, hapus pertanyaan pasangannya.
      startIndex = index > 0 && _messages[index - 1].isUser
          ? index - 1
          : index;

      endIndex = index + 1;
    }

    setState(() {
      _messages.removeRange(startIndex, endIndex);
    });

    _syncQwenConversation();
    await _saveChat();

    if (!mounted) return;

    _showMessage('Conversation deleted.');
  }

  // Mengedit pertanyaan dan menghasilkan ulang jawabannya.
  Future<void> _editMessage(int index) async {
    if (_isGenerating ||
        index < 0 ||
        index >= _messages.length ||
        !_messages[index].isUser) {
      return;
    }

    final editedPrompt = await showDialog<String>(
      context: context,
      builder: (dialogContext) {
        return _EditMessageDialog(
          initialText: _messages[index].content,
        );
      },
    );

    if (!mounted || editedPrompt == null) return;

    final newPrompt = editedPrompt.trim();

    if (newPrompt.isEmpty) {
      _showMessage('Message cannot be empty.');
      return;
    }

    if (newPrompt == _messages[index].content) {
      return;
    }

    // Hapus pertanyaan lama dan pesan setelahnya.
    setState(() {
      _messages.removeRange(index, _messages.length);
      _promptController.text = newPrompt;
    });

    _syncQwenConversation();
    await _saveChat();

    if (!mounted) return;

    // Kirim kembali pertanyaan yang sudah diedit.
    await _sendMessage(promptOverride: newPrompt);
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

  Widget _buildUserMessage(int index) {
    final content = _messages[index].content;

    return Align(
      alignment: Alignment.centerRight,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Container(
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
          _buildMessageActions(
            index: index,
            content: content,
            isUser: true,
          ),
        ],
      ),
    );
  }


  // Tombol aksi yang ditampilkan di bawah bubble.
  Widget _buildMessageActions({
    required int index,
    required String content,
    required bool isUser,
  }) {
    final canUseActions =
        !_isGenerating && content.trim().isNotEmpty;

    return Padding(
      padding: const EdgeInsets.only(
        left: 4,
        right: 4,
        top: 2,
        bottom: 4,
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          IconButton(
            onPressed: content.trim().isEmpty
                ? null
                : () => _copyMessage(content),
            tooltip: 'Copy',
            visualDensity: VisualDensity.compact,
            icon: const Icon(
              Icons.copy_outlined,
              size: 18,
            ),
          ),

          if (isUser)
            IconButton(
              onPressed: canUseActions
                  ? () => _editMessage(index)
                  : null,
              tooltip: 'Edit',
              visualDensity: VisualDensity.compact,
              icon: const Icon(
                Icons.edit_outlined,
                size: 18,
              ),
            ),

          IconButton(
            onPressed: canUseActions
                ? () => _deleteMessage(index)
                : null,
            tooltip: 'Hapus',
            visualDensity: VisualDensity.compact,
            icon: const Icon(
              Icons.delete_outline,
              size: 18,
            ),
          ),
        ],
      ),
    );
  }


  // Bubble respons AI.
 
  Widget _buildAIMessage(int index) {
    final content = _messages[index].content;
    final isEmpty = content.isEmpty;

    return Align(
      alignment: Alignment.centerLeft,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            constraints: BoxConstraints(
              maxWidth: MediaQuery.of(context).size.width * 0.88,
            ),
            margin: const EdgeInsets.symmetric(vertical: 6),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Theme.of(context)
                  .colorScheme
                  .surfaceContainerHighest,
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
          _buildMessageActions(
            index: index,
            content: content,
            isUser: false,
          ),
        ],
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
            ? _buildUserMessage(index)
            : _buildAIMessage(index);
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


class _EditMessageDialog extends StatefulWidget {
  const _EditMessageDialog({
    required this.initialText,
  });

  final String initialText;

  @override
  State<_EditMessageDialog> createState() =>
      _EditMessageDialogState();
}

class _EditMessageDialogState
    extends State<_EditMessageDialog> {
  late final TextEditingController _controller;

  @override
  void initState() {
    super.initState();

    _controller = TextEditingController(
      text: widget.initialText,
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Edit message'),
      content: TextField(
        controller: _controller,
        autofocus: true,
        minLines: 1,
        maxLines: 5,
        textCapitalization: TextCapitalization.sentences,
        decoration: const InputDecoration(
          hintText: 'Edit your question...',
          border: OutlineInputBorder(),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () {
            Navigator.pop(context);
          },
          child: const Text('Cancel'),
        ),
        FilledButton(
          onPressed: () {
            Navigator.pop(
              context,
              _controller.text.trim(),
            );
          },
          child: const Text('Save'),
        ),
      ],
    );
  }
}
