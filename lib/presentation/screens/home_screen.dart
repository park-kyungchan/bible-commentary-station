import 'package:flutter/material.dart';
import '../../application/workstation_controller.dart';
import '../../core/responsive/responsive_layout.dart';
import '../../core/theme/app_theme.dart';
import '../widgets/pulpit_prompter_view.dart';

class HomeScreen extends StatefulWidget {
  final WorkstationController controller;

  const HomeScreen({super.key, required this.controller});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _isPulpitMode = false;
  int _rightTab = 0; // 0: 8대 주석, 1: 관주, 2: 설교 스튜디오
  int _mobileNavIndex = 1; // 0: 66권, 1: 본문, 2: 주석/설교

  WorkstationController get _ctrl => widget.controller;

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: _ctrl,
      builder: (context, _) {
        if (_isPulpitMode) {
          return PulpitPrompterView(
            slides: _ctrl.buildPulpitSlides(),
            targetDurationMins: _ctrl.activeSermon.targetDurationMins,
            onExit: () => setState(() => _isPulpitMode = false),
          );
        }

        final isMobile = ResponsiveLayout.isMobile(context);

        return Scaffold(
          appBar: AppBar(
            backgroundColor: PastoralTheme.primaryNavy,
            title: const Row(
              children: [
                Icon(Icons.auto_stories, color: PastoralTheme.accentGold),
                SizedBox(width: 8),
                Text('성경주혜주석 v2.0', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 17)),
              ],
            ),
            actions: [
              Container(
                margin: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: PastoralTheme.statusEmerald.withValues(alpha: 0.18),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: PastoralTheme.statusEmerald),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.offline_pin, color: PastoralTheme.statusEmerald, size: 16),
                    SizedBox(width: 6),
                    Text('오프라인 FTS5 준비됨', style: TextStyle(color: PastoralTheme.statusEmerald, fontSize: 12)),
                  ],
                ),
              ),
              Padding(
                padding: const EdgeInsets.only(right: 10),
                child: ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(backgroundColor: PastoralTheme.accentGold, foregroundColor: Colors.black),
                  onPressed: () => setState(() => _isPulpitMode = true),
                  icon: const Icon(Icons.podium, size: 18),
                  label: const Text('강단 모드', style: TextStyle(fontWeight: FontWeight.bold)),
                ),
              ),
            ],
          ),
          body: ResponsiveLayout(
            desktop: Row(
              children: [
                SizedBox(width: 240, child: _buildBookNavigator()),
                const VerticalDivider(width: 1, color: Colors.white12),
                Expanded(flex: 42, child: _buildScriptureReader()),
                const VerticalDivider(width: 1, color: Colors.white12),
                Expanded(flex: 38, child: _buildExegesisPanel()),
              ],
            ),
            tablet: Row(
              children: [
                Expanded(child: _buildScriptureReader()),
                const VerticalDivider(width: 1, color: Colors.white12),
                Expanded(child: _buildExegesisPanel()),
              ],
            ),
            mobile: IndexedStack(
              index: _mobileNavIndex,
              children: [
                _buildBookNavigator(),
                _buildScriptureReader(),
                _buildExegesisPanel(),
              ],
            ),
          ),
          bottomNavigationBar: isMobile
              ? NavigationBar(
                  selectedIndex: _mobileNavIndex,
                  onDestinationSelected: (i) => setState(() => _mobileNavIndex = i),
                  destinations: const [
                    NavigationDestination(icon: Icon(Icons.list), label: '66권'),
                    NavigationDestination(icon: Icon(Icons.menu_book), label: '성경 본문'),
                    NavigationDestination(icon: Icon(Icons.hub), label: '주석·설교'),
                  ],
                )
              : null,
        );
      },
    );
  }

  Widget _buildBookNavigator() {
    return ListView.builder(
      itemCount: _ctrl.books.length,
      itemBuilder: (context, index) {
        final b = _ctrl.books[index];
        final isSel = b.bookId == _ctrl.selectedBookId;
        return ListTile(
          dense: true,
          selected: isSel,
          title: Text(b.nameKr, style: TextStyle(color: isSel ? PastoralTheme.accentGold : Colors.white)),
          trailing: Text('${b.totalChapters}장', style: const TextStyle(fontSize: 11, color: Colors.grey)),
          onTap: () {
            _ctrl.loadChapter(b.bookId, 1);
            if (ResponsiveLayout.isMobile(context)) setState(() => _mobileNavIndex = 1);
          },
        );
      },
    );
  }

  Widget _buildScriptureReader() {
    final bookName = _ctrl.currentBook?.nameKr ?? '성경';
    final totalCh = _ctrl.currentBook?.totalChapters ?? 1;
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          color: PastoralTheme.darkCard,
          child: Row(
            children: [
              Text('$bookName ${_ctrl.selectedChapter}장 (KRV)', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              const Spacer(),
              IconButton(icon: const Icon(Icons.chevron_left), onPressed: _ctrl.selectedChapter > 1 ? _ctrl.previousChapter : null),
              Text('${_ctrl.selectedChapter} / $totalCh장'),
              IconButton(icon: const Icon(Icons.chevron_right), onPressed: _ctrl.selectedChapter < totalCh ? _ctrl.nextChapter : null),
            ],
          ),
        ),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.all(12),
            itemCount: _ctrl.chapterVerses.length,
            itemBuilder: (context, index) {
              final v = _ctrl.chapterVerses[index];
              final isSel = v.verse == _ctrl.selectedVerseNumber;
              return Card(
                color: isSel ? PastoralTheme.accentGold.withValues(alpha: 0.14) : PastoralTheme.darkCard,
                child: ListTile(
                  onTap: () => _ctrl.selectVerse(v.verse),
                  leading: CircleAvatar(
                    radius: 13,
                    backgroundColor: isSel ? PastoralTheme.accentGold : Colors.white12,
                    child: Text('${v.verse}', style: TextStyle(fontSize: 12, color: isSel ? Colors.black : Colors.white)),
                  ),
                  title: Text(v.text, style: const TextStyle(fontSize: 15.5, height: 1.65)),
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildExegesisPanel() {
    return Column(
      children: [
        SegmentedButton<int>(
          segments: const [
            ButtonSegment(value: 0, label: Text('8대 주석')),
            ButtonSegment(value: 1, label: Text('관주·연쇄')),
            ButtonSegment(value: 2, label: Text('설교')),
          ],
          selected: {_rightTab},
          onSelectionChanged: (s) => setState(() => _rightTab = s.first),
        ),
        Expanded(
          child: _rightTab == 0
              ? ListView.builder(
                  padding: const EdgeInsets.all(12),
                  itemCount: _ctrl.commentaries.length,
                  itemBuilder: (_, i) {
                    final c = _ctrl.commentaries[i];
                    return Card(
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('[${c.sourceName}] ${c.title ?? ""}',
                                style: const TextStyle(fontWeight: FontWeight.bold, color: PastoralTheme.accentGold)),
                            const SizedBox(height: 6),
                            Text(c.contentMarkdown, style: const TextStyle(height: 1.6)),
                          ],
                        ),
                      ),
                    );
                  },
                )
              : _rightTab == 1
                  ? ListView.builder(
                      padding: const EdgeInsets.all(12),
                      itemCount: _ctrl.crossRefs.length,
                      itemBuilder: (_, i) {
                        final r = _ctrl.crossRefs[i];
                        return Card(
                          child: ListTile(
                            title: Text('${r.refString} (${r.relationshipType})',
                                style: const TextStyle(color: Colors.cyanAccent, fontWeight: FontWeight.bold)),
                            subtitle: Text(r.fullText, style: const TextStyle(height: 1.5)),
                          ),
                        );
                      },
                    )
                  : ListView(
                      padding: const EdgeInsets.all(12),
                      children: [
                        Text(_ctrl.activeSermon.title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 8),
                        ..._ctrl.activeSermon.outline.map(
                          (o) => Card(child: ListTile(title: Text('[${o.section}] ${o.title}'), subtitle: Text(o.content))),
                        ),
                      ],
                    ),
        ),
      ],
    );
  }
}
