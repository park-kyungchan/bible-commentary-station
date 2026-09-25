import 'dart:async';
import 'package:flutter/material.dart';
import 'package:wakelock_plus/wakelock_plus.dart';
import '../../core/theme/app_theme.dart';

class PulpitPrompterView extends StatefulWidget {
  final VoidCallback onExit;

  const PulpitPrompterView({
    super.key,
    required this.onExit,
  });

  @override
  State<PulpitPrompterView> createState() => _PulpitPrompterViewState();
}

class _PulpitPrompterViewState extends State<PulpitPrompterView> {
  int _currentSlideIndex = 0;
  int _remainingSeconds = 30 * 60; // 30 minutes countdown
  Timer? _countdownTimer;

  final List<Map<String, String>> _slides = [
    {
      "section": "설교 본문 및 제목",
      "header": "창세기 22장 1절 - 14절",
      "body": "모리아 산의 온전한 순종과\n여호와 이레의 축복",
      "cue": "목회자 기도 후 선포"
    },
    {
      "section": "본론 I",
      "header": "1. 가장 소중한 것을 내려놓는 믿음의 결단 (창 22:2)",
      "body": "• '네 아들 네 사랑하는 독자 이삭을 바치라'\n• 인간의 가능성이 끝난 100세에 얻은 유일한 보물\n• 마음에 하나님보다 앞선 우상이 없는가?",
      "cue": "강조: 자기 부인과 성화의 단계"
    },
    {
      "section": "본론 II",
      "header": "2. 묵묵히 제단을 향해 걷는 순종의 침묵 (창 22:9)",
      "body": "• 청년 이삭의 자발적 순종\n• 나무를 지고 모리아 산을 오르는 모습은\n  십자가를 지고 골고다로 가신 예수 그리스도의 그림자",
      "cue": "묵상: 십자가의 순종"
    },
    {
      "section": "본론 III",
      "header": "3. 수풀에 걸린 숫양과 여호와 이레의 절대적 채우심 (창 22:13)",
      "body": "• 순종의 끝에서 예비하시는 하나님\n• 백 배의 결실(창 26:12)과 르호봇의 지경을 넓히시는 섭리\n• 하나님은 순종하는 자의 미래를 책임지십니다",
      "cue": "결단: 여호와 이레의 하나님 찬양"
    },
    {
      "section": "결론 및 결단 기도",
      "header": "결론: 약속의 자녀로서의 결단",
      "body": "• 나의 모리아 산 제단에 무엇을 올려드릴 것인가?\n• 성령을 따라 난 성결한 약속의 자녀로 살아가라",
      "cue": "통성 기도 인도 (3분)"
    }
  ];

  @override
  void initState() {
    super.initState();
    // Keep screen awake on pulpit stand
    WakelockPlus.enable();

    // Start 30-min countdown timer
    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_remainingSeconds > 0) {
        setState(() {
          _remainingSeconds--;
        });
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
    return "$mins:$secs";
  }

  void _nextSlide() {
    if (_currentSlideIndex < _slides.length - 1) {
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
    final currentSlide = _slides[_currentSlideIndex];

    return Scaffold(
      backgroundColor: PastoralTheme.pulpitBackground,
      body: Stack(
        children: [
          // Touch Zones (Left 25% = Prev, Right 75% = Next)
          Row(
            children: [
              Expanded(
                flex: 25,
                child: GestureDetector(
                  behavior: HitTestBehavior.translucent,
                  onTap: _prevSlide,
                  child: Container(),
                ),
              ),
              Expanded(
                flex: 75,
                child: GestureDetector(
                  behavior: HitTestBehavior.translucent,
                  onTap: _nextSlide,
                  child: Container(),
                ),
              ),
            ],
          ),

          // Pulpit Content Display
          SafeArea(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Top Status Bar (Timer, Slide Progress, Exit)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                  color: Colors.white.withOpacity(0.04),
                  child: Row(
                    children: [
                      // Slide Indicator
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: PastoralTheme.pulpitAccent.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: PastoralTheme.pulpitAccent),
                        ),
                        child: Text(
                          "대지 ${_currentSlideIndex + 1} / ${_slides.length}",
                          style: const TextStyle(
                            color: PastoralTheme.pulpitAccent,
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Text(
                        currentSlide["section"]!,
                        style: const TextStyle(
                          color: Colors.white70,
                          fontSize: 20,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      const Spacer(),
                      // Large Countdown Timer
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                        decoration: BoxDecoration(
                          color: _remainingSeconds < 300
                              ? Colors.red.withOpacity(0.3)
                              : Colors.white.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                            color: _remainingSeconds < 300 ? Colors.redAccent : Colors.white24,
                          ),
                        ),
                        child: Row(
                          children: [
                            Icon(
                              Icons.timer,
                              color: _remainingSeconds < 300 ? Colors.redAccent : PastoralTheme.pulpitAccent,
                              size: 22,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              _formatTimer(_remainingSeconds),
                              style: TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.bold,
                                color: _remainingSeconds < 300 ? Colors.redAccent : Colors.white,
                                fontFamily: 'monospace',
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 16),
                      // Exit Button
                      IconButton(
                        icon: const Icon(Icons.close, color: Colors.white54, size: 28),
                        onPressed: widget.onExit,
                        tooltip: "강단 모드 종료",
                      ),
                    ],
                  ),
                ),

                // Large Main Pulpit Text (38pt ~ 44pt for 70cm distance)
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 48, vertical: 36),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          currentSlide["header"]!,
                          style: PastoralTheme.pulpitHeaderTextStyle,
                        ),
                        const SizedBox(height: 28),
                        Expanded(
                          child: SingleChildScrollView(
                            child: Text(
                              currentSlide["body"]!,
                              style: PastoralTheme.pulpitLargeTextStyle,
                            ),
                          ),
                        ),
                        if (currentSlide["cue"] != null)
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                            decoration: BoxDecoration(
                              color: Colors.amber.withOpacity(0.15),
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: Colors.amber.withOpacity(0.3)),
                            ),
                            child: Row(
                              children: [
                                const Icon(Icons.record_voice_over, color: PastoralTheme.pulpitAccent, size: 22),
                                const SizedBox(width: 10),
                                Text(
                                  "강단 큐: ${currentSlide["cue"]!}",
                                  style: const TextStyle(
                                    color: PastoralTheme.pulpitAccent,
                                    fontSize: 18,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ],
                            ),
                          ),
                      ],
                    ),
                  ),
                ),

                // Bottom Tap Guide
                Container(
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  color: Colors.white.withOpacity(0.02),
                  child: const Center(
                    child: Text(
                      "◀ 좌측 25% 터치: 이전 대지   |   우측 75% 터치: 다음 대지 ▶",
                      style: TextStyle(color: Colors.white30, fontSize: 14),
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
