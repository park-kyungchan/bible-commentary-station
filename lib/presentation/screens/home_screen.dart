import 'package:flutter/material.dart';
import '../../core/responsive/responsive_layout.dart';
import '../../core/theme/app_theme.dart';
import '../../domain/models/bible_models.dart';
import '../widgets/commentary_panel.dart';
import '../widgets/cross_ref_drawer.dart';
import '../widgets/sermon_studio_view.dart';
import '../widgets/pulpit_prompter_view.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _isPulpitMode = false;
  int _rightPanelTab = 0; // 0: 주석, 1: 관주, 2: 설교스튜디오
  final List<String> _scrapedCitations = [];

  // Selected Bible state
  String _selectedBook = "창세기";
  int _selectedChapter = 22;
  int _selectedVerseNumber = 2;

  // Mock Chapter Verses (Genesis 22:1-4)
  final List<Map<String, dynamic>> _currentVerses = [
    {
      "verse": 1,
      "text": "그 일 후에 하나님이 아브라함을 시험하시려고 그를 부르시되 아브라함아 하시니 그가 이르되 내가 여기 있나이다",
      "strongs": ["H0430 (하나님)", "H5254 (시험하시다)", "H0085 (아브라함)"]
    },
    {
      "verse": 2,
      "text": "여호와께서 이르시되 네 아들 네 사랑하는 독자 이삭을 데리고 모리아 땅으로 가서 내가 네게 일러 준 한 산 거기서 그를 번제로 드리라",
      "strongs": ["H3068 (여호와)", "H3173 (독자-야히드)", "H3327 (이삭)", "H5930 (번제)"]
    },
    {
      "verse": 3,
      "text": "아브라함이 아침에 일찍이 일어나 나귀에 안장을 지우고 두 종과 그의 아들 이삭을 데리고 번제에 쓸 나무를 쪼개어 가지고 떠나 하나님이 자기에게 일러 주신 곳으로 가더니",
      "strongs": ["H7925 (일찍이 일어나)", "H2543 (나귀)", "H6086 (나무)"]
    },
    {
      "verse": 4,
      "text": "제삼일에 아브라함이 눈을 들어 그 곳을 멀리 바라본지라",
      "strongs": ["H7992 (제삼일)", "H5375 (눈을 들어)", "H7200 (바라보다)"]
    },
  ];

  void _onScrap(String source, String text) {
    setState(() {
      _scrapedCitations.add("[$source] $text");
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isPulpitMode) {
      return PulpitPrompterView(
        onExit: () => setState(() => _isPulpitMode = false),
      );
    }

    return Scaffold(
      appBar: _buildTopAppBar(),
      body: ResponsiveLayout(
        desktop: _buildDesktop3Panel(),
        tablet: _buildTablet2Panel(),
        mobile: _buildMobile1Column(),
      ),
    );
  }

  PreferredSizeWidget _buildTopAppBar() {
    return AppBar(
      backgroundColor: PastoralTheme.primaryNavy,
      title: Row(
        children: [
          const Icon(Icons.auto_stories, color: PastoralTheme.accentGold),
          const SizedBox(width: 10),
          const Text(
            "성경주혜주석 (Pastoral Workstation)",
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
          ),
          const SizedBox(width: 16),
          // Device badge
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
              color: Colors.white10,
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              ResponsiveLayout.isDesktop(context)
                  ? "PC 연구실 모드 (3-Panel)"
                  : ResponsiveLayout.isFoldableOrTablet(context)
                      ? "Z Fold 6 / iPad 모드"
                      : "스마트폰 모드",
              style: const TextStyle(fontSize: 12, color: Colors.white70),
            ),
          ),
        ],
      ),
      actions: [
        // GCP Cloud sync badge
        Container(
          margin: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
          decoration: BoxDecoration(
            color: Colors.emerald.withOpacity(0.2),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: Colors.greenAccent),
          ),
          child: const Row(
            children: [
              Icon(Icons.cloud_done, color: Colors.greenAccent, size: 16),
              SizedBox(width: 6),
              Text("GCS 주석 DB 준비됨", style: TextStyle(color: Colors.greenAccent, fontSize: 12)),
            ],
          ),
        ),
        // Pulpit Prompter Launch Button
        Padding(
          padding: const EdgeInsets.only(right: 12.0),
          child: ElevatedButton.icon(
            style: ElevatedButton.styleFrom(
              backgroundColor: PastoralTheme.accentGold,
              foregroundColor: Colors.black,
            ),
            onPressed: () => setState(() => _isPulpitMode = true),
            icon: const Icon(Icons.podium, size: 18),
            label: const Text("강단 모드 (38pt)", style: TextStyle(fontWeight: FontWeight.bold)),
          ),
        ),
      ],
    );
  }

  /// PC 3-Panel Split View (20% Nav | 42% Scripture | 38% Exegesis & Studio)
  Widget _buildDesktop3Panel() {
    return Row(
      children: [
        // Left Nav Panel (20%)
        SizedBox(
          width: 260,
          child: _buildBookNavigator(),
        ),
        const VerticalDivider(width: 1, color: Colors.white10),

        // Center Scripture Panel (42%)
        Expanded(
          flex: 42,
          child: _buildScriptureReader(),
        ),
        const VerticalDivider(width: 1, color: Colors.white10),

        // Right Exegesis & Studio Panel (38%)
        Expanded(
          flex: 38,
          child: _buildRightExegesisStudioPanel(),
        ),
      ],
    );
  }

  /// Fold 6 Unfolded / iPad 2-Panel Adaptive View
  Widget _buildTablet2Panel() {
    return Row(
      children: [
        Expanded(
          flex: 50,
          child: _buildScriptureReader(),
        ),
        const VerticalDivider(width: 1, color: Colors.white10),
        Expanded(
          flex: 50,
          child: _buildRightExegesisStudioPanel(),
        ),
      ],
    );
  }

  /// Fold 6 Folded / Mobile 1-Column View
  Widget _buildMobile1Column() {
    return _buildScriptureReader();
  }

  Widget _buildBookNavigator() {
    final books = ["창세기", "출애굽기", "레위기", "이사야", "마태복음", "요한복음", "로마서", "갈라디아서", "히브리서"];
    return Container(
      color: PastoralTheme.darkBg,
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: const BoxDecoration(
              border: Border(bottom: BorderSide(color: Colors.white10)),
            ),
            child: const Row(
              children: [
                Icon(Icons.list, color: Colors.grey, size: 20),
                SizedBox(width: 8),
                Text("성경 66권 목록", style: TextStyle(fontWeight: FontWeight.bold)),
              ],
            ),
          ),
          Expanded(
            child: ListView.builder(
              itemCount: books.length,
              itemBuilder: (context, index) {
                final b = books[index];
                final isSelected = b == _selectedBook;
                return ListTile(
                  dense: true,
                  selected: isSelected,
                  selectedTileColor: PastoralTheme.accentGold.withOpacity(0.15),
                  title: Text(
                    b,
                    style: TextStyle(
                      fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                      color: isSelected ? PastoralTheme.accentGold : Colors.white,
                    ),
                  ),
                  trailing: Text(
                    b == "창세기" ? "50장" : "총서",
                    style: const TextStyle(fontSize: 11, color: Colors.grey),
                  ),
                  onTap: () => setState(() => _selectedBook = b),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildScriptureReader() {
    return Container(
      color: PastoralTheme.darkBg,
      child: Column(
        children: [
          // Chapter navigation bar
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            color: PastoralTheme.darkCard,
            child: Row(
              children: [
                Text(
                  "$_selectedBook $_selectedChapter장 (개역개정 / 원어대조)",
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                const Spacer(),
                IconButton(
                  icon: const Icon(Icons.chevron_left),
                  onPressed: () {},
                ),
                Text("$_selectedChapter / 50장", style: const TextStyle(fontWeight: FontWeight.bold)),
                IconButton(
                  icon: const Icon(Icons.chevron_right),
                  onPressed: () {},
                ),
              ],
            ),
          ),

          // Verses list
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _currentVerses.length,
              itemBuilder: (context, index) {
                final v = _currentVerses[index];
                final isSelected = v["verse"] == _selectedVerseNumber;

                return InkWell(
                  onTap: () => setState(() => _selectedVerseNumber = v["verse"]),
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: isSelected
                          ? PastoralTheme.accentGold.withOpacity(0.12)
                          : PastoralTheme.darkCard,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(
                        color: isSelected ? PastoralTheme.accentGold : Colors.white12,
                        width: isSelected ? 1.5 : 1.0,
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            CircleAvatar(
                              radius: 12,
                              backgroundColor: isSelected ? PastoralTheme.accentGold : Colors.white12,
                              child: Text(
                                "${v["verse"]}",
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                  color: isSelected ? Colors.black : Colors.white,
                                ),
                              ),
                            ),
                            const Spacer(),
                            if (isSelected)
                              const Text(
                                "연구 선택됨",
                                style: TextStyle(color: PastoralTheme.accentGold, fontSize: 11),
                              ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          v["text"],
                          style: TextStyle(
                            fontSize: 16.5,
                            height: 1.7,
                            fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                            color: isSelected ? Colors.white : Colors.white70,
                          ),
                        ),
                        const SizedBox(height: 8),
                        // Strong's Hebrew chips
                        Wrap(
                          spacing: 6,
                          runSpacing: 4,
                          children: (v["strongs"] as List<String>).map((st) {
                            return Chip(
                              label: Text(st, style: const TextStyle(fontSize: 11)),
                              backgroundColor: Colors.white.withOpacity(0.06),
                              padding: EdgeInsets.zero,
                              visualDensity: VisualDensity.compact,
                            );
                          }).toList(),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRightExegesisStudioPanel() {
    return Container(
      color: PastoralTheme.darkBg,
      padding: const EdgeInsets.all(12),
      child: Column(
        children: [
          // Selector Switch
          Container(
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.all(4),
            decoration: BoxDecoration(
              color: PastoralTheme.darkCard,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                _buildTabButton(0, Icons.menu_book, "8대 주석"),
                _buildTabButton(1, Icons.hub, "성경 관주"),
                _buildTabButton(2, Icons.edit_note, "설교 스튜디오"),
              ],
            ),
          ),

          // Active Panel Body
          Expanded(
            child: IndexedStack(
              index: _rightPanelTab,
              children: [
                CommentaryPanel(
                  selectedVerse: BibleVerse(
                    verseId: 1022002,
                    bookId: 1,
                    chapter: 22,
                    verse: _selectedVerseNumber,
                    versionCode: 'KRV',
                    text: _currentVerses.firstWhere((e) => e["verse"] == _selectedVerseNumber)["text"],
                  ),
                  onScrapToSermon: _onScrap,
                ),
                CrossRefDrawer(onScrapToSermon: _onScrap),
                SermonStudioView(
                  scrapedCitations: _scrapedCitations,
                  onLaunchPulpitMode: () => setState(() => _isPulpitMode = true),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTabButton(int index, IconData icon, String label) {
    final isSelected = _rightPanelTab == index;
    return Expanded(
      child: InkWell(
        onTap: () => setState(() => _rightPanelTab = index),
        borderRadius: BorderRadius.circular(6),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 8),
          decoration: BoxDecoration(
            color: isSelected ? PastoralTheme.primaryNavy : Colors.transparent,
            borderRadius: BorderRadius.circular(6),
            border: isSelected ? Border.all(color: PastoralTheme.accentGold.withOpacity(0.5)) : null,
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 16,
                color: isSelected ? PastoralTheme.accentGold : Colors.grey,
              ),
              const SizedBox(width: 6),
              Text(
                label,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                  color: isSelected ? Colors.white : Colors.grey,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
