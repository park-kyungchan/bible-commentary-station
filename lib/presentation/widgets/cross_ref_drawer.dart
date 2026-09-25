import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';
import '../../domain/models/bible_models.dart';

class CrossRefDrawer extends StatefulWidget {
  final Function(String ref, String text) onScrapToSermon;

  const CrossRefDrawer({
    super.key,
    required this.onScrapToSermon,
  });

  @override
  State<CrossRefDrawer> createState() => _CrossRefDrawerState();
}

class _CrossRefDrawerState extends State<CrossRefDrawer>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  // Demonstrated full-text cross references for Genesis 22:2
  final List<Map<String, String>> _fullTextCrossRefs = [
    {
      "ref": "요한복음 3:16",
      "text": "하나님이 세상을 이처럼 사랑하사 독생자를 주셨으니 이는 그를 믿는 자마다 멸망하지 않고 영생을 얻게 하려 하심이라",
      "type": "예표적 성취 (독생자)",
      "point": "아브라함의 독자 이삭은 인류를 위해 독생자를 내어주신 하나님의 사랑의 그림자.",
    },
    {
      "ref": "로마서 8:32",
      "text": "자기 아들을 아끼지 아니하시고 우리 모든 사람을 위하여 내주신 이가 어찌 그 아들과 함께 모든 것을 우리에게 주시지 아니하겠느냐",
      "type": "바울의 구속사 해설",
      "point": "독자를 아끼지 않은 믿음에 화답하여 독생자를 아끼지 않으신 하나님의 절대적 은혜.",
    },
    {
      "ref": "히브리서 11:17-19",
      "text": "아브라함은 시험을 받을 때에 믿음으로 이삭을 드렸으니... 그가 하나님이 능히 이삭을 죽은 자 가운데서 다시 살리실 줄로 생각한지라 비유컨대 그를 죽은 자 가운데서 도로 받은 것이니라",
      "type": "부활 신앙의 절정",
      "point": "이삭 번제 사건은 죽음을 이기는 부활 신앙의 역사적 선언.",
    },
    {
      "ref": "야고보서 2:21-22",
      "text": "우리 조상 아브라함이 그 아들 이삭을 제단에 바칠 때에 행함으로 의롭다 하심을 받은 것이 아니냐 네가 보거니와 믿음이 그의 행함과 함께 일하고 행함으로 믿음이 온전하게 되었느니라",
      "type": "실천적 믿음의 온전함",
      "point": "마음의 고백을 넘어 실제 삶의 결단으로 입증된 참된 믿음.",
    }
  ];

  // Entity Chain-Reference for Isaac
  final List<ChainLink> _isaacChains = [
    ChainLink(
      ref: "창세기 21:3",
      book: "창세기",
      text: "아브라함이 그에게 태어난 아들 곧 사라가 자기에게 낳은 아들을 이름하여 이삭이라 하였고",
      type: "언약의 출생",
      point: "인간의 가능성이 끝난 100세에 하나님의 초자연적 약속으로 태어난 웃음의 아들.",
    ),
    ChainLink(
      ref: "창세기 22:2",
      book: "창세기",
      text: "여호와께서 이르시되 네 아들 네 사랑하는 독자 이삭을 데리고 모리아 땅으로 가서... 번제로 드리라",
      type: "모리아산 번제",
      point: "십자가에 죽기까지 복종하신 그리스도의 순종을 예표함.",
    ),
    ChainLink(
      ref: "창세기 26:12",
      book: "창세기",
      text: "이삭이 그 땅에서 농사하여 그 해에 백 배나 얻었고 여호와께서 복을 주시므로",
      type: "백 배의 결실",
      point: "흉년 중에도 하나님의 약속을 의지하여 씨를 뿌리는 자에게 부어지는 절대적 축복.",
    ),
    ChainLink(
      ref: "창세기 26:22",
      book: "창세기",
      text: "이삭이 거기서 옮겨 다른 우물을 팠더니 그들이 다투지 아니하였으므로 그 이름을 르호봇이라 하여...",
      type: "르호봇의 온유함",
      point: "분쟁 앞에서 양보할 때 하나님께서 지경을 넓히시는 온유한 성도의 승리 원리.",
    ),
    ChainLink(
      ref: "갈라디아서 4:28",
      book: "갈라디아서",
      text: "형제들아 너희는 이삭과 같이 약속의 자녀라",
      type: "신약의 구속사 완성",
      point: "율법의 종이 아니라 성령의 은혜로 자유함을 얻은 거듭난 성도의 정체성.",
    ),
  ];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

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
          // Header Bar
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: const BoxDecoration(
              border: Border(bottom: BorderSide(color: Colors.white10)),
            ),
            child: Row(
              children: [
                const Icon(Icons.hub, color: Colors.cyanAccent, size: 20),
                const SizedBox(width: 8),
                Text(
                  "성경 심층 관주 & 연쇄 관주",
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
              ],
            ),
          ),

          // Tabs
          TabBar(
            controller: _tabController,
            indicatorColor: Colors.cyanAccent,
            labelColor: Colors.cyanAccent,
            unselectedLabelColor: Colors.grey,
            tabs: const [
              Tab(icon: Icon(Icons.format_quote, size: 18), text: "구절 전문 관주 (TSK)"),
              Tab(icon: Icon(Icons.link, size: 18), text: "인물 연쇄 관주 (이삭)"),
            ],
          ),

          // Tab Content
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildVerseCrossRefs(),
                _buildChainReferences(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildVerseCrossRefs() {
    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: _fullTextCrossRefs.length,
      itemBuilder: (context, index) {
        final item = _fullTextCrossRefs[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          color: PastoralTheme.darkBorder.withOpacity(0.4),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
            side: const BorderSide(color: Colors.white10),
          ),
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.cyan.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        item["ref"]!,
                        style: const TextStyle(
                          color: Colors.cyanAccent,
                          fontWeight: FontWeight.bold,
                          fontSize: 13,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      item["type"]!,
                      style: const TextStyle(color: Colors.white60, fontSize: 12),
                    ),
                    const Spacer(),
                    IconButton(
                      icon: const Icon(Icons.add_circle_outline, color: Colors.cyanAccent, size: 20),
                      tooltip: "설교 대지에 인용",
                      onPressed: () {
                        widget.onScrapToSermon(item["ref"]!, item["text"]!);
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text("${item["ref"]} 관주 성구가 설교 스튜디오로 복사되었습니다.")),
                        );
                      },
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  item["text"]!,
                  style: const TextStyle(fontSize: 14.5, height: 1.6, color: Colors.white),
                ),
                const SizedBox(height: 6),
                Text(
                  "💡 ${item["point"]}",
                  style: const TextStyle(fontSize: 12.5, color: Colors.amberAccent, height: 1.4),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildChainReferences() {
    return ListView(
      padding: const EdgeInsets.all(12),
      children: [
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.cyanAccent.withOpacity(0.08),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.cyanAccent.withOpacity(0.3)),
          ),
          child: const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                "인물 연쇄 관주: 이삭 (Isaac - '웃음')",
                style: TextStyle(fontWeight: FontWeight.bold, color: Colors.cyanAccent, fontSize: 15),
              ),
              SizedBox(height: 4),
              Text(
                "약속의 자녀 · 순종의 번제물 · 온유한 승리자",
                style: TextStyle(color: Colors.amberAccent, fontSize: 13),
              ),
              SizedBox(height: 6),
              Text(
                "창세기 출생부터 모리아산 번제, 르호봇의 양보와 신약 로마서/갈라디아서의 성령으로 난 성결한 약속의 자녀까지 성경 전체 생애 사슬망.",
                style: TextStyle(fontSize: 12.5, height: 1.5, color: Colors.white70),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        ..._isaacChains.map((chain) {
          return Card(
            margin: const EdgeInsets.only(bottom: 10),
            color: PastoralTheme.darkBorder.withOpacity(0.3),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(
                        chain.ref,
                        style: const TextStyle(color: Colors.cyanAccent, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: Colors.white10,
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          chain.type,
                          style: const TextStyle(fontSize: 11, color: Colors.white70),
                        ),
                      ),
                      const Spacer(),
                      InkWell(
                        onTap: () {
                          widget.onScrapToSermon(chain.ref, "${chain.text}\n[설교 포인트: ${chain.point}]");
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text("${chain.ref} 연쇄 관주가 설교 스튜디오로 인용되었습니다.")),
                          );
                        },
                        child: const Row(
                          children: [
                            Icon(Icons.add, color: Colors.cyanAccent, size: 16),
                            Text("설교 인용", style: TextStyle(color: Colors.cyanAccent, fontSize: 12)),
                          ],
                        ),
                      )
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    chain.text,
                    style: const TextStyle(fontSize: 13.5, height: 1.5),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    "설교 포인트: ${chain.point}",
                    style: const TextStyle(color: Colors.amberAccent, fontSize: 12, height: 1.4),
                  ),
                ],
              ),
            ),
          );
        }),
      ],
    );
  }
}
