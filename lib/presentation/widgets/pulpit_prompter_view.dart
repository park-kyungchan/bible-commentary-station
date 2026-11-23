import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:wakelock_plus/wakelock_plus.dart';
import '../../application/workstation_controller.dart';
import '../../core/theme/app_theme.dart';

/// Isolated Zero-Glare Pulpit Mode Prompter (#000000 bg, #24201B buttons, #FFFDF5 ink).
/// - All buttons enforce >= 48dp hit targets with plain Korean labels
/// - Scroll-safe reading stage (no tap overlay blocking scroll drag)
/// - Full keyboard & presentation clicker support (Arrow/Page/Space/Escape)
/// - Countdown + overtime timer with pause/resume/reset
class PulpitPrompterView extends StatefulWidget {
  final List<PulpitSlide> slides;
  final int targetDurationMins;
  final VoidCallback onExit;
  final Future<void> Function(bool enabled)? onWakelockChanged;

  const PulpitPrompterView({
    super.key,
    required this.slides,
    required this.targetDurationMins,
    required this.onExit,
    this.onWakelockChanged,
  });

  @override
  State<PulpitPrompterView> createState() => _PulpitPrompterViewState();
}

class _PulpitPrompterViewState extends State<PulpitPrompterView> {
  final FocusNode _focusNode = FocusNode();
  int _currentSlideIndex = 0;
  double _fontSizePt = 36.0;
  late int _remainingSeconds;
  bool _isTimerPaused = false;
  Timer? _countdownTimer;

  @override
  void initState() {
    super.initState();
    _remainingSeconds = widget.targetDurationMins * 60;
    unawaited(_setWakelock(true));
    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (!_isTimerPaused && mounted) {
        setState(() => _remainingSeconds--);
      }
    });
  }

  @override
  void dispose() {
    unawaited(_setWakelock(false));
    _countdownTimer?.cancel();
    _focusNode.dispose();
    super.dispose();
  }

  Future<void> _setWakelock(bool enabled) async {
    try {
      if (widget.onWakelockChanged != null) {
        await widget.onWakelockChanged!(enabled);
      } else if (enabled) {
        await WakelockPlus.enable();
      } else {
        await WakelockPlus.disable();
      }
    } catch (_) {
      // Safe no-op in headless/test environments without native wakelock channel.
    }
  }

  String _formatTimer(int totalSecs) {
    final isOvertime = totalSecs < 0;
    final absSecs = totalSecs.abs();
    final mins = (absSecs ~/ 60).toString().padLeft(2, '0');
    final secs = (absSecs % 60).toString().padLeft(2, '0');
    return isOvertime ? '+$mins:$secs' : '$mins:$secs';
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

  void _resetTimer() {
    setState(() {
      _remainingSeconds = widget.targetDurationMins * 60;
      _isTimerPaused = false;
    });
  }

  KeyEventResult _handleKeyEvent(FocusNode node, KeyEvent event) {
    if (event is! KeyDownEvent) return KeyEventResult.ignored;
    final key = event.logicalKey;
    if (key == LogicalKeyboardKey.arrowRight ||
        key == LogicalKeyboardKey.pageDown ||
        key == LogicalKeyboardKey.space) {
      _nextSlide();
      return KeyEventResult.handled;
    }
    if (key == LogicalKeyboardKey.arrowLeft ||
        key == LogicalKeyboardKey.pageUp) {
      _prevSlide();
      return KeyEventResult.handled;
    }
    if (key == LogicalKeyboardKey.escape) {
      widget.onExit();
      return KeyEventResult.handled;
    }
    return KeyEventResult.ignored;
  }

  ButtonStyle _pulpitButtonStyle({Size minimumSize = const Size(48, 48)}) {
    return ElevatedButton.styleFrom(
      minimumSize: minimumSize,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      backgroundColor: PastoralTheme.pulpitButtonBg,
      foregroundColor: PastoralTheme.pulpitInk,
      disabledBackgroundColor: PastoralTheme.pulpitBarBg,
      disabledForegroundColor: PastoralTheme.pulpitInk.withValues(alpha: 0.35),
      elevation: 0,
      side: const BorderSide(color: PastoralTheme.pulpitButtonBorder),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
    );
  }

  @override
  Widget build(BuildContext context) {
    final totalSlides = widget.slides.length;
    final currentSlide = totalSlides > 0
        ? widget.slides[_currentSlideIndex]
        : const PulpitSlide(
            section: '안내',
            header: '설교 대지 없음',
            body: '설교 준비 화면에서 대지를 추가해 주세요.',
          );
    final nextSlide = _currentSlideIndex < totalSlides - 1
        ? widget.slides[_currentSlideIndex + 1]
        : null;
    final progress = totalSlides > 0 ? (_currentSlideIndex + 1) / totalSlides : 0.0;
    final disableAnimations = MediaQuery.disableAnimationsOf(context);
    final isWarning = _remainingSeconds < 300;

    return Focus(
      focusNode: _focusNode,
      autofocus: true,
      onKeyEvent: _handleKeyEvent,
      child: Scaffold(
        backgroundColor: PastoralTheme.pulpitBackground,
        body: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Top progress hairline
              LinearProgressIndicator(
                value: progress,
                minHeight: 4,
                color: PastoralTheme.pulpitGold,
                backgroundColor: PastoralTheme.pulpitBarBorder,
              ),
              // Zero-glare dark control bar
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                decoration: const BoxDecoration(
                  color: PastoralTheme.pulpitBarBg,
                  border: Border(
                    bottom: BorderSide(color: PastoralTheme.pulpitBarBorder),
                  ),
                ),
                child: Wrap(
                  spacing: 10,
                  runSpacing: 10,
                  alignment: WrapAlignment.spaceBetween,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  children: [
                    Text(
                      '대지 ${_currentSlideIndex + 1} / $totalSlides · ${currentSlide.section}',
                      key: const Key('pulpit_slide_counter'),
                      style: const TextStyle(
                        color: PastoralTheme.pulpitGold,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: [
                        ElevatedButton.icon(
                          key: const Key('pulpit_btn_smaller'),
                          style: _pulpitButtonStyle(),
                          onPressed: () => setState(
                            () => _fontSizePt = (_fontSizePt - 2).clamp(24.0, 56.0),
                          ),
                          icon: const Icon(Icons.text_decrease, size: 18),
                          label: const Text('글자 작게'),
                        ),
                        ElevatedButton.icon(
                          key: const Key('pulpit_btn_bigger'),
                          style: _pulpitButtonStyle(),
                          onPressed: () => setState(
                            () => _fontSizePt = (_fontSizePt + 2).clamp(24.0, 56.0),
                          ),
                          icon: const Icon(Icons.text_increase, size: 18),
                          label: const Text('글자 크게'),
                        ),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 8),
                          child: Text(
                            _formatTimer(_remainingSeconds),
                            key: const Key('pulpit_timer_text'),
                            style: TextStyle(
                              fontSize: 22,
                              fontWeight: FontWeight.bold,
                              color: isWarning
                                  ? PastoralTheme.pulpitAlert
                                  : PastoralTheme.pulpitInk,
                            ),
                          ),
                        ),
                        ElevatedButton.icon(
                          key: const Key('pulpit_btn_timer_toggle'),
                          style: _pulpitButtonStyle(),
                          onPressed: () =>
                              setState(() => _isTimerPaused = !_isTimerPaused),
                          icon: Icon(
                            _isTimerPaused ? Icons.play_arrow : Icons.pause,
                            size: 18,
                          ),
                          label: Text(_isTimerPaused ? '재개' : '일시정지'),
                        ),
                        ElevatedButton.icon(
                          key: const Key('pulpit_btn_timer_reset'),
                          style: _pulpitButtonStyle(),
                          onPressed: _resetTimer,
                          icon: const Icon(Icons.restart_alt, size: 18),
                          label: const Text('초기화'),
                        ),
                        ElevatedButton.icon(
                          key: const Key('pulpit_btn_exit'),
                          style: _pulpitButtonStyle(),
                          onPressed: widget.onExit,
                          icon: const Icon(Icons.close, size: 18),
                          label: const Text('나가기'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              // Scroll-safe reading stage (zero blocking tap overlays)
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 24),
                  child: AnimatedSwitcher(
                    duration: disableAnimations
                        ? Duration.zero
                        : const Duration(milliseconds: 240),
                    child: Align(
                      key: ValueKey<int>(_currentSlideIndex),
                      alignment: Alignment.topLeft,
                      child: SingleChildScrollView(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              currentSlide.header,
                              key: const Key('pulpit_slide_header'),
                              style: PastoralTheme.pulpitHeaderStyle(_fontSizePt),
                            ),
                            const SizedBox(height: 24),
                            Text(
                              currentSlide.body,
                              key: const Key('pulpit_slide_body'),
                              style: PastoralTheme.pulpitBodyStyle(_fontSizePt),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
              ),
              // Bottom slide navigation footer with >= 48dp buttons
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: const BoxDecoration(
                  color: PastoralTheme.pulpitBarBg,
                  border: Border(
                    top: BorderSide(color: PastoralTheme.pulpitBarBorder),
                  ),
                ),
                child: Row(
                  children: [
                    ElevatedButton.icon(
                      key: const Key('pulpit_btn_prev'),
                      style: _pulpitButtonStyle(minimumSize: const Size(120, 52)),
                      onPressed: _currentSlideIndex > 0 ? _prevSlide : null,
                      icon: const Icon(Icons.arrow_back, size: 20),
                      label: const Text('이전 대지'),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        nextSlide != null ? '다음: ${nextSlide.header}' : '마지막 대지입니다',
                        textAlign: TextAlign.center,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          color: PastoralTheme.pulpitGold.withValues(alpha: 0.85),
                          fontSize: 15,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    ElevatedButton.icon(
                      key: const Key('pulpit_btn_next'),
                      style: _pulpitButtonStyle(minimumSize: const Size(120, 52)),
                      onPressed:
                          _currentSlideIndex < totalSlides - 1 ? _nextSlide : null,
                      icon: const Icon(Icons.arrow_forward, size: 20),
                      label: const Text('다음 대지'),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
