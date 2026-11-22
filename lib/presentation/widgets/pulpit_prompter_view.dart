import 'dart:async';
import 'package:flutter/material.dart';
import 'package:wakelock_plus/wakelock_plus.dart';
import '../../application/workstation_controller.dart';
import '../../core/theme/app_theme.dart';

class PulpitPrompterView extends StatefulWidget {
  final List<PulpitSlide> slides;
  final int targetDurationMins;
  final VoidCallback onExit;

  const PulpitPrompterView({
    super.key,
    required this.slides,
    required this.targetDurationMins,
    required this.onExit,
  });

  @override
  State<PulpitPrompterView> createState() => _PulpitPrompterViewState();
}

class _PulpitPrompterViewState extends State<PulpitPrompterView> {
  int _currentSlideIndex = 0;
  double _fontSizePt = 38.0;
  late int _remainingSeconds;
  Timer? _countdownTimer;

  @override
  void initState() {
    super.initState();
    _remainingSeconds = widget.targetDurationMins * 60;
    WakelockPlus.enable();
    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (_remainingSeconds > 0 && mounted) {
        setState(() => _remainingSeconds--);
      }
    });
  }

  @override
  void dispose() {
    WakelockPlus.disable();
    _countdownTimer?.cancel();
    super.dispose();
  }

  String _formatTimer(int totalSecs) {
    final mins = (totalSecs ~/ 60).toString().padLeft(2, '0');
    final secs = (totalSecs % 60).toString().padLeft(2, '0');
    return '$mins:$secs';
  }

  void _nextSlide() {
    if (_currentSlideIndex < widget.slides.length - 1) {
      setState(() => _currentSlideIndex++);
    }
  }

  void _prevSlide() {
    if (_currentSlideIndex > 0) {
      setState(() => _currentSlideIndex--);
    }
  }

  @override
  Widget build(BuildContext context) {
    final currentSlide = widget.slides.isNotEmpty
        ? widget.slides[_currentSlideIndex]
        : const PulpitSlide(section: '안내', header: '설교 대지 없음', body: '설교 스튜디오에서 대지를 추가해 주세요.');

    return Scaffold(
      backgroundColor: PastoralTheme.pulpitBackground,
      body: Stack(
        children: [
          Row(
            children: [
              Expanded(
                flex: 25,
                child: GestureDetector(behavior: HitTestBehavior.translucent, onTap: _prevSlide, child: const SizedBox.expand()),
              ),
              Expanded(
                flex: 75,
                child: GestureDetector(behavior: HitTestBehavior.translucent, onTap: _nextSlide, child: const SizedBox.expand()),
              ),
            ],
          ),
          SafeArea(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  color: Colors.white.withValues(alpha: 0.05),
                  child: Row(
                    children: [
                      Text(
                        '대지 ${_currentSlideIndex + 1} / ${widget.slides.length} · ${currentSlide.section}',
                        style: const TextStyle(color: PastoralTheme.pulpitAccent, fontSize: 18, fontWeight: FontWeight.bold),
                      ),
                      const Spacer(),
                      IconButton(
                        icon: const Icon(Icons.text_decrease, color: Colors.white70),
                        onPressed: () => setState(() => _fontSizePt = (_fontSizePt - 2).clamp(36.0, 54.0)),
                      ),
                      IconButton(
                        icon: const Icon(Icons.text_increase, color: Colors.white70),
                        onPressed: () => setState(() => _fontSizePt = (_fontSizePt + 2).clamp(36.0, 54.0)),
                      ),
                      const SizedBox(width: 12),
                      Text(
                        _formatTimer(_remainingSeconds),
                        style: TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                          color: _remainingSeconds < 300 ? Colors.redAccent : Colors.white,
                          fontFamily: 'monospace',
                        ),
                      ),
                      const SizedBox(width: 12),
                      IconButton(icon: const Icon(Icons.close, color: Colors.white70, size: 28), onPressed: widget.onExit),
                    ],
                  ),
                ),
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 28),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(currentSlide.header, style: PastoralTheme.pulpitHeaderStyle(_fontSizePt)),
                        const SizedBox(height: 24),
                        Expanded(
                          child: SingleChildScrollView(
                            child: Text(currentSlide.body, style: PastoralTheme.pulpitBodyStyle(_fontSizePt)),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
