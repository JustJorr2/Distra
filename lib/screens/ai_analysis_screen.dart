import 'dart:async';
import 'package:material_ui/material_ui.dart';
import '../services/qwen_service.dart';

class AIAnalysisScreen extends StatefulWidget {
  const AIAnalysisScreen({super.key});

  @override
  State<AIAnalysisScreen> createState() => _AIAnalysisScreenState();
}

class _AIAnalysisScreenState extends State<AIAnalysisScreen> {
  final QwenService _qwenService = QwenService();
  final TextEditingController _promptController = TextEditingController();

  StreamSubscription<String>? _generationSubscription;

  String _modelName = 'No model selected';
  String _response = '';

  bool _isLoadingModel = false;
  bool _isGenerating = false;

  Future<void> _selectAndLoadModel() async {
    setState(() {
      _isLoadingModel = true;
      _response = '';
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

  Future<void> _generateResponse() async {
    final prompt = _promptController.text.trim();

    if (prompt.isEmpty || !_qwenService.isModelLoaded) {
      _showMessage(
        prompt.isEmpty ? 'Enter a prompt first.' : 'Load a model first.',
      );
      return;
    }

    setState(() {
      _response = '';
      _isGenerating = true;
    });

    try {
      _generationSubscription = _qwenService
          .generateResponse(prompt)
          .listen(
        (token) {
          if (!mounted) return;

          setState(() {
            _response += token;
          });
        },
        onError: (error) {
          if (!mounted) return;
          _showMessage('Generation error: $error');
        },
        onDone: () {
          if (!mounted) return;

          setState(() {
            _isGenerating = false;
          });
        },
      );
    } catch (e) {
      _showMessage('Error: $e');

      if (mounted) {
        setState(() {
          _isGenerating = false;
        });
      }
    }
  }

  Future<void> _stopGeneration() async {
    await _qwenService.stopGeneration();
    await _generationSubscription?.cancel();

    if (!mounted) return;

    setState(() {
      _isGenerating = false;
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
    _qwenService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Local AI Playground'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Model Status',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(_modelName),
                    const SizedBox(height: 12),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: _isLoadingModel || _isGenerating
                            ? null
                            : _selectAndLoadModel,
                        icon: const Icon(Icons.folder_open),
                        label: const Text('Select & Load GGUF Model'),
                      ),
                    ),
                    if (_isLoadingModel) ...[
                      const SizedBox(height: 12),
                      const LinearProgressIndicator(),
                      const SizedBox(height: 8),
                      const Text('Loading model into memory...'),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _promptController,
              enabled: _qwenService.isModelLoaded && !_isGenerating,
              maxLines: 4,
              decoration: const InputDecoration(
                labelText: 'Prompt',
                hintText: 'Ask Qwen something...',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _isGenerating
                    ? _stopGeneration
                    : _qwenService.isModelLoaded
                        ? _generateResponse
                        : null,
                icon: Icon(
                  _isGenerating ? Icons.stop : Icons.send,
                ),
                label: Text(
                  _isGenerating ? 'Stop Generation' : 'Generate Response',
                ),
              ),
            ),
            const SizedBox(height: 16),
            const Text(
              'AI Response',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Expanded(
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: SingleChildScrollView(
                  child: SelectableText(
                    _response.isEmpty
                        ? 'Response will appear here...'
                        : _response,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}