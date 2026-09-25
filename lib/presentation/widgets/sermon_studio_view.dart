import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';
import '../../domain/models/bible_models.dart';

class SermonStudioView extends StatefulWidget {
  final List<String> scrapedCitations;
  final VoidCallback onLaunchPulpitMode;

  const SermonStudioView({
    super.key,
    required this.scrapedCitations,
    required this.onLaunchPulpitMode,
  });

  @override
  State<SermonStudioView> createState() => _SermonStudioViewState();
}

class _SermonStudioViewState extends State<SermonStudioView> {
  final TextEditingController _titleController = TextEditingController(
    text: "모리아 산의 온전한 순종과 여호와 이레의 축복",
  );
  final TextEditingController _passageController = TextEditingController(
    text: "창세기 22장 1절-14절",
  );

  final List<Map<String, String>> _outlineCards = [
    {
      "section": "서론",
      "title": "믿음의 시험과 인생의 광야",
      "content": "하나님께서 아브라함을 부르실 때 즉각 순종한 믿음. 100세에 얻은 아들 이삭을 요구하시는 청천벽력 같은 명령 앞에서 신앙의 본질을 점검함."
    },
    {
      "section": "본론 I",
      "title": "가장 소중한 독자를 내려놓는 믿음의 결단 (창 22:2)",
      "content": "히브리어 '야히드'(유일하고 귀한 독자). 내 삶의 가장 깊은 애착과 우상을 내려놓는 완전한 자기 부인의 성화 단계."
    },
    {
      "section": "본론 II",
      "title": "묵묵히 사흘 길을 동행하는 순종의 침묵 (창 22:9)",
      "content": "청년 이삭의 자발적 순종. 아버지의 뜻에 거역하지 않고 제단 위에 눕는 온유함은 십자가 예수 그리스도의 복종을 완전하게 예표함."
    },
    {
      "section": "본론 III",
      "title": "수풀에 걸린 숫양과 여호와 이레의 절대적 채우심 (창 22:13)",
      "content": "순종의 끝에서 예비하시는 하나님. 백 배의 결실(창 26:12)과 르호봇의 지경을 넓히시는 하나님의 섭리."
    },
    {
      "section": "결론",
      "title": "약속의 자녀로서의 결단과 부활 신앙",
      "content": "오늘 우리에게 맡기신 모리아 산의 제단에서 나의 가장 귀한 것을 주님께 올려드릴 때 하늘의 문이 열리고 영원한 언약의 복이 임함."
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white12),
      ),
      child: Column(
        children: [
          // Studio Action Header
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: const BoxDecoration(
              border: Border(bottom: BorderSide(color: Colors.white10)),
            ),
            child: Row(
              children: [
                const Icon(Icons.edit_note, color: Colors.amberAccent, size: 22),
                const SizedBox(width: 8),
                Text(
                  "설교 스튜디오 (Sermon Studio)",
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const Spacer(),
                ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.amber.shade700,
                    foregroundColor: Colors.black,
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  ),
                  onPressed: widget.onLaunchPulpitMode,
                  icon: const Icon(Icons.podium, size: 18),
                  label: const Text(
                    "강단 프롬프터 모드 전환 (Pulpit Mode)",
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
          ),

          // Title & Passage Inputs
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                Expanded(
                  flex: 3,
                  child: TextField(
                    controller: _titleController,
                    decoration: const InputDecoration(
                      labelText: "설교 제목",
                      border: OutlineInputBorder(),
                      isDense: true,
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  flex: 2,
                  child: TextField(
                    controller: _passageController,
                    decoration: const InputDecoration(
                      labelText: "설교 본문",
                      border: OutlineInputBorder(),
                      isDense: true,
                    ),
                  ),
                ),
              ],
            ),
          ),

          // 3-Point Outline Cards
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              itemCount: _outlineCards.length,
              itemBuilder: (context, index) {
                final card = _outlineCards[index];
                return Card(
                  margin: const EdgeInsets.only(bottom: 10),
                  color: PastoralTheme.darkBorder.withOpacity(0.35),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: Colors.amber.withOpacity(0.2),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                card["section"]!,
                                style: const TextStyle(
                                  color: Colors.amberAccent,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 12,
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                card["title"]!,
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          card["content"]!,
                          style: const TextStyle(fontSize: 13, height: 1.5, color: Colors.white70),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),

          // Scrapped Citations tray
          if (widget.scrapedCitations.isNotEmpty)
            Container(
              padding: const EdgeInsets.all(10),
              decoration: const BoxDecoration(
                border: Border(top: BorderSide(color: Colors.white10)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    "인용 보관함 (${widget.scrapedCitations.length}개 스크랩됨)",
                    style: const TextStyle(fontSize: 12, color: Colors.grey, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 4),
                  Wrap(
                    spacing: 6,
                    runSpacing: 4,
                    children: widget.scrapedCitations.take(3).map((c) {
                      return Chip(
                        label: Text(
                          c.split('\n').first,
                          style: const TextStyle(fontSize: 11),
                        ),
                        backgroundColor: Colors.white10,
                      );
                    }).toList(),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
