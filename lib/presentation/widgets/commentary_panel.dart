import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';
import '../../domain/models/bible_models.dart';

class CommentaryPanel extends StatefulWidget {
  final BibleVerse selectedVerse;
  final Function(String source, String text) onScrapToSermon;

  const CommentaryPanel({
    super.key,
    required this.selectedVerse,
    required this.onScrapToSermon,
  });

  @override
  State<CommentaryPanel> createState() => _CommentaryPanelState();
}

class _CommentaryPanelState extends State<CommentaryPanel>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  final List<Map<String, String>> _sources = [
    {"key": "oxford", "name": "옥스포드 원어"},
    {"key": "wesley", "name": "웨슬리"},
    {"key": "hokma", "name": "호크마"},
    {"key": "grand", "name": "그랜드(대지)"},
    {"key": "charisma", "name": "카리스마"},
    {"key": "henry", "name": "매튜 헨리"},
    {"key": "baker", "name": "베이커 배경"},
    {"key": "esv", "name": "ESV 해설"},
  ];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _sources.length, vsync: this);
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
                const Icon(Icons.menu_book, color: PastoralTheme.accentGold, size: 20),
                const SizedBox(width: 8),
                Text(
                  "8대 종합 주석 대조",
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const Spacer(),
                Text(
                  "창세기 ${widget.selectedVerse.chapter}:${widget.selectedVerse.verse}",
                  style: const TextStyle(
                    color: PastoralTheme.accentGold,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),

          // Commentary Tabs
          TabBar(
            controller: _tabController,
            isScrollable: true,
            tabAlignment: TabAlignment.start,
            indicatorColor: PastoralTheme.accentGold,
            labelColor: PastoralTheme.accentGold,
            unselectedLabelColor: Colors.grey,
            labelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
            tabs: _sources.map((s) => Tab(text: s["name"])).toList(),
          ),

          // Commentary Body
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: _sources.map((s) {
                return _buildCommentaryContent(s["key"]!, s["name"]!);
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCommentaryContent(String key, String name) {
    // Demonstration high-value exegesis content
    String title = "";
    String content = "";
    String practical = "";

    switch (key) {
      case "oxford":
        title = "원어 형태론 및 구문론 분해 (창 22:2)";
        content = "히브리어 'קַח־נָא' (카흐-나)는 칼(Qal) 능동태 명령형과 간청의 불변사 '나'가 결합된 형태이다. 강제적 명령이 아니라 아버지 하나님의 비통한 사랑과 절대적 순종을 촉구하시는 신적 간청을 내포한다. '네 사랑하는 독자 이삭'(אֶת־יְחִידְךָ אֲשֶׁר־אָהַבְתָּ)에서 '야히드'는 단순한 외아들을 넘어 '생명보다 소중하고 유일무이한 보물'을 의미한다.";
        practical = "원어적 강해 포인트: 하나님은 가장 아끼는 유일한 것을 요구하심으로써 우리의 믿음의 중심을 시험하신다.";
        break;
      case "wesley":
        title = "존 웨슬리 주석: 온전한 헌신과 믿음의 순종";
        content = "믿음의 조상 아브라함에게 요구된 시험은 자신의 뜻을 완전히 비우고 하나님의 은혜에 전적으로 맡기는 성화(Sanctification)의 절정이다. 하나님께서 이삭을 요구하신 것은 그를 죽이기 위함이 아니라 아브라함의 마음에 하나님보다 앞선 우상이 없음을 온 우주 앞에 증명하시기 위함이었다.";
        practical = "목회적 설교 적용: 성도는 은혜로 구원받은 후, 가장 귀한 약속마저도 하나님께 드릴 수 있는 성숙한 사랑으로 나아가야 한다.";
        break;
      case "hokma":
        title = "호크마 종합 해설: 모리아 산의 구속사적 의미";
        content = "모리아(Moriah) 산은 훗날 다윗이 번제단을 쌓은 아라우나의 타작마당이자 솔로몬 성전이 건축된 장소이며(대하 3:1), 골고다 언덕과 맥을 같이한다. 아브라함이 독자를 제단에 바친 바로 그 장소에서 하나님은 온 인류를 위한 하나님의 독생자 예수 그리스도의 대속 제사를 미리 준비하셨다.";
        practical = "구속사적 맥락: 구약의 그림자는 신약의 십자가 은혜에서 완전히 성취된다.";
        break;
      case "grand":
        title = "그랜드 종합주석: 3대지 설교 아웃라인";
        content = "I. 버림의 시험: 혈육의 가장 귀한 애착을 내려놓는 결단\nII. 순종의 동행: 사흘 길을 묵묵히 걷는 믿음의 침묵\nIII. 예비하시는 하나님: 여호와 이레의 절대적 공급과 축복";
        practical = "설교자 가이드: 설교 본문 구성 시 '순종의 고난'과 '여호와 이레의 축복'을 균형 있게 다룰 것.";
        break;
      default:
        title = "$name 성경 주석";
        content = "선택하신 구절에 대한 심층 신학 해설과 구속사적 강해가 로컬 SQLite DB(Drift)로부터 실시간 렌더링됩니다.";
        practical = "말씀을 삶에 적용하여 성령의 열매를 맺도록 이끄는 목회적 통찰.";
    }

    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: ListView(
        children: [
          Text(
            title,
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: PastoralTheme.accentGold,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            content,
            style: const TextStyle(fontSize: 15, height: 1.7),
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: PastoralTheme.accentGold.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: PastoralTheme.accentGold.withOpacity(0.3)),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.lightbulb_outline, color: PastoralTheme.accentGold, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    practical,
                    style: const TextStyle(fontSize: 14, height: 1.5, color: PastoralTheme.accentGold),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          ElevatedButton.icon(
            style: ElevatedButton.styleFrom(
              backgroundColor: PastoralTheme.primaryNavy,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 12),
            ),
            onPressed: () {
              widget.onScrapToSermon(name, "$title\n$content");
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text("[$name] 주석이 설교 스튜디오로 스크랩되었습니다.")),
              );
            },
            icon: const Icon(Icons.bookmark_add, size: 18),
            label: const Text("이 주석을 설교 대지 카드로 인용 (+)"),
          ),
        ],
      ),
    );
  }
}
