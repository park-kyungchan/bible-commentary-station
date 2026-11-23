import 'dart:async';
import 'package:flutter/material.dart';
import '../../application/workstation_controller.dart';
import '../../core/responsive/responsive_layout.dart';
import '../../core/theme/app_theme.dart';
import '../../domain/models/bible_models.dart';
import '../widgets/pulpit_prompter_view.dart';

class HomeScreen extends StatefulWidget {
  final WorkstationController controller;
  final Future<void> Function(bool enabled)? onWakelockChanged;

  const HomeScreen({
    super.key,
    required this.controller,
    this.onWakelockChanged,
  });

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();
  bool _isPulpitMode = false;
  List<PulpitSlide>? _pulpitOverrideSlides;
  int _rightTab = 0; // 0: 핵심 주석, 1: 연결 말씀, 2: 설교 준비, 3: 예배 예전
  int _mobileNavIndex = 1; // 0: 66권, 1: 성경 본문, 2: 주석·설교

  WorkstationController get _ctrl => widget.controller;

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: _ctrl,
      builder: (context, _) {
        if (_isPulpitMode) {
          return PulpitPrompterView(
            slides: _pulpitOverrideSlides ?? _ctrl.buildPulpitSlides(),
            targetDurationMins: _ctrl.activeSermon.targetDurationMins,
            onExit: () => setState(() {
              _isPulpitMode = false;
              _pulpitOverrideSlides = null;
            }),
            onWakelockChanged: widget.onWakelockChanged,
          );
        }

        final theme = Theme.of(context);
        final cs = theme.colorScheme;
        final width = MediaQuery.sizeOf(context).width;
        final isMobile = width < 600;
        final isTablet = width >= 600 && width < 1024;
        final isDesktop = width >= 1024;
        final hairline = PastoralTheme.hairlineBorder(theme.brightness);

        return Scaffold(
          key: _scaffoldKey,
          drawer: isTablet && _ctrl.isDatabaseReady
              ? Drawer(
                  width: 300,
                  backgroundColor: cs.surface,
                  child: SafeArea(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Padding(
                          padding: const EdgeInsets.fromLTRB(16, 12, 8, 8),
                          child: Row(
                            children: [
                              Text(
                                '성경 66권',
                                style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                  color: cs.onSurface,
                                ),
                              ),
                              const Spacer(),
                              TextButton(
                                onPressed: () => Navigator.of(context).pop(),
                                child: const Text('닫기'),
                              ),
                            ],
                          ),
                        ),
                        Divider(height: 1, color: hairline),
                        Expanded(
                          child: _buildBookNavigator(
                            context,
                            closeDrawerOnSelect: true,
                          ),
                        ),
                      ],
                    ),
                  ),
                )
              : null,
          appBar: AppBar(
            toolbarHeight: 64,
            automaticallyImplyLeading: false,
            backgroundColor: cs.surface,
            foregroundColor: cs.onSurface,
            surfaceTintColor: Colors.transparent,
            elevation: 0,
            bottom: PreferredSize(
              preferredSize: const Size.fromHeight(1),
              child: Divider(height: 1, thickness: 1, color: hairline),
            ),
            title: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.auto_stories, color: cs.primary, size: 24),
                const SizedBox(width: 8),
                Text(
                  '말씀 서재',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 19,
                    color: cs.onSurface,
                  ),
                ),
              ],
            ),
            actions: [
              if (isDesktop || isTablet) ...[
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 6),
                  child: _buildStatusBadge(context),
                ),
              ],
              if (isDesktop) ...[
                _buildFontControls(context),
                const SizedBox(width: 8),
                _buildThemeToggleButton(context),
                const SizedBox(width: 8),
              ],
              Padding(
                padding: const EdgeInsets.only(right: 12),
                child: ElevatedButton.icon(
                  key: const Key('btn_pulpit_mode'),
                  onPressed: () => setState(() {
                    _pulpitOverrideSlides = null;
                    _isPulpitMode = true;
                  }),
                  icon: const Icon(Icons.present_to_all, size: 20),
                  label: const Text('강단 화면'),
                ),
              ),
            ],
          ),
          body: Column(
            children: [
              if (!isDesktop)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: cs.surface,
                    border: Border(bottom: BorderSide(color: hairline)),
                  ),
                  child: Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    crossAxisAlignment: WrapCrossAlignment.center,
                    children: [
                      if (isMobile) _buildStatusBadge(context),
                      _buildFontControls(context),
                      _buildThemeToggleButton(context),
                    ],
                  ),
                ),
              Expanded(child: _buildMainContent(context, isTablet: isTablet)),
            ],
          ),
          bottomNavigationBar: isMobile && _ctrl.isDatabaseReady
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

  Widget _buildStatusBadge(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    late final Color badgeColor;
    late final IconData icon;
    late final String label;

    switch (_ctrl.dbStatus) {
      case DatabaseStatus.ready:
        badgeColor = PastoralTheme.statusForest(brightness);
        icon = Icons.check_circle_outline;
        label = '오프라인 읽기 준비됨';
      case DatabaseStatus.syncing:
        badgeColor = PastoralTheme.warmAccent(brightness);
        icon = Icons.cloud_download;
        label = '성경 자료 내려받는 중';
      case DatabaseStatus.error:
        badgeColor = PastoralTheme.statusCrimson(brightness);
        icon = Icons.error_outline;
        label = '자료 확인 필요';
      case DatabaseStatus.idle:
        badgeColor = PastoralTheme.mutedInk(brightness);
        icon = Icons.hourglass_empty;
        label = '성경 자료 준비 중';
    }

    return Container(
      key: const Key('db_status_badge'),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: badgeColor.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: badgeColor),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: badgeColor, size: 16),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(
              color: badgeColor,
              fontSize: 13,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFontControls(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        OutlinedButton(
          key: const Key('btn_font_dec'),
          onPressed: _ctrl.canDecreaseFont ? _ctrl.decreaseFontSize : null,
          child: const Text('가-'),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8),
          child: Text(
            _ctrl.fontStepLabel,
            key: const Key('font_step_label'),
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: cs.onSurface,
            ),
          ),
        ),
        OutlinedButton(
          key: const Key('btn_font_inc'),
          onPressed: _ctrl.canIncreaseFont ? _ctrl.increaseFontSize : null,
          child: const Text('가+'),
        ),
      ],
    );
  }

  Widget _buildThemeToggleButton(BuildContext context) {
    final isDark = _ctrl.themeMode == ThemeMode.dark;
    return OutlinedButton.icon(
      key: const Key('btn_theme_toggle'),
      onPressed: _ctrl.toggleThemeMode,
      icon: Icon(isDark ? Icons.light_mode : Icons.dark_mode, size: 18),
      label: Text(isDark ? '밝은 화면' : '어두운 화면'),
    );
  }

  Widget _buildMainContent(BuildContext context, {required bool isTablet}) {
    if (_ctrl.dbStatus == DatabaseStatus.syncing ||
        (_ctrl.isLoading && !_ctrl.isDatabaseReady)) {
      return _buildLoadingView(context);
    }

    if (_ctrl.errorMessage != null && !_ctrl.isDatabaseReady) {
      return _buildErrorRecoveryView(context);
    }

    if (!_ctrl.isDatabaseReady) {
      return _buildLoadingView(context);
    }

    final hairline = PastoralTheme.hairlineBorder(Theme.of(context).brightness);

    return ResponsiveLayout(
      desktop: Row(
        children: [
          SizedBox(width: 256, child: _buildBookNavigator(context)),
          VerticalDivider(width: 1, thickness: 1, color: hairline),
          Expanded(
            flex: 42,
            child: _buildScriptureReader(context, showBookPickerButton: false),
          ),
          VerticalDivider(width: 1, thickness: 1, color: hairline),
          Expanded(flex: 38, child: _buildExegesisPanel(context)),
        ],
      ),
      tablet: Row(
        children: [
          Expanded(
            child: _buildScriptureReader(context, showBookPickerButton: true),
          ),
          VerticalDivider(width: 1, thickness: 1, color: hairline),
          Expanded(child: _buildExegesisPanel(context)),
        ],
      ),
      mobile: IndexedStack(
        index: _mobileNavIndex,
        children: [
          _buildBookNavigator(context),
          _buildScriptureReader(context, showBookPickerButton: false),
          _buildExegesisPanel(context),
        ],
      ),
    );
  }

  Widget _buildLoadingView(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final progress = _ctrl.syncProgress;
    return Center(
      key: const Key('bootstrap_loading_view'),
      child: SingleChildScrollView(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 440),
          child: Card(
            margin: const EdgeInsets.all(24),
            child: Padding(
              padding: const EdgeInsets.all(28),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.auto_stories, size: 48, color: cs.primary),
                  const SizedBox(height: 16),
                  Text(
                    '성경 자료를 준비하고 있습니다',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: cs.onSurface,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    progress?.message.isNotEmpty == true
                        ? progress!.message
                        : '오프라인 성경과 주석 자료를 불러오는 중입니다...',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 16,
                      color: cs.onSurfaceVariant,
                      height: 1.5,
                    ),
                  ),
                  const SizedBox(height: 20),
                  if (progress != null && progress.isDownloading)
                    LinearProgressIndicator(value: progress.progress)
                  else
                    const CircularProgressIndicator(),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildErrorRecoveryView(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Center(
      key: const Key('bootstrap_error_view'),
      child: SingleChildScrollView(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 480),
          child: Card(
            margin: const EdgeInsets.all(24),
            child: Padding(
              padding: const EdgeInsets.all(28),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.error_outline, size: 48, color: cs.error),
                  const SizedBox(height: 16),
                  Text(
                    '성경 자료를 불러오지 못했습니다',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: cs.onSurface,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    _ctrl.errorMessage ?? '인터넷 연결을 확인한 뒤 다시 시도해 주세요.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 15,
                      color: cs.onSurfaceVariant,
                      height: 1.6,
                    ),
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton.icon(
                    key: const Key('btn_retry_bootstrap'),
                    onPressed: _ctrl.retryBootstrap,
                    icon: const Icon(Icons.refresh),
                    label: const Text('다시 시도'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildBookNavigator(
    BuildContext context, {
    bool closeDrawerOnSelect = false,
  }) {
    final theme = Theme.of(context);
    final cs = theme.colorScheme;
    final muted = PastoralTheme.mutedInk(theme.brightness);

    return ListView.builder(
      padding: const EdgeInsets.symmetric(vertical: 8),
      itemCount: _ctrl.books.length,
      itemBuilder: (context, index) {
        final b = _ctrl.books[index];
        final isSel = b.bookId == _ctrl.selectedBookId;
        return ListTile(
          minTileHeight: 52,
          selected: isSel,
          selectedTileColor: cs.primaryContainer,
          title: Text(
            b.nameKr,
            style: TextStyle(
              fontSize: 16,
              fontWeight: isSel ? FontWeight.bold : FontWeight.w500,
              color: isSel ? cs.onPrimaryContainer : cs.onSurface,
            ),
          ),
          trailing: Text(
            '${b.totalChapters}장',
            style: TextStyle(fontSize: 13, color: muted),
          ),
          onTap: () {
            _ctrl.loadChapter(b.bookId, 1);
            if (closeDrawerOnSelect) {
              Navigator.of(context).pop();
            } else if (ResponsiveLayout.isMobile(context)) {
              setState(() => _mobileNavIndex = 1);
            }
          },
        );
      },
    );
  }

  Future<void> _openBookPickerModal(BuildContext context) async {
    var selectedTestament = _ctrl.currentBook?.testament ?? 'OT';
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (sheetContext) {
        return StatefulBuilder(
          builder: (sheetContext, setSheetState) {
            final theme = Theme.of(sheetContext);
            final cs = theme.colorScheme;
            final hairline = PastoralTheme.hairlineBorder(theme.brightness);
            final filteredBooks = _ctrl.books
                .where((b) => b.testament == selectedTestament)
                .toList();
            final visibleBooks = filteredBooks.isNotEmpty ? filteredBooks : _ctrl.books;

            return SizedBox(
              key: const Key('book_picker_modal'),
              height: MediaQuery.sizeOf(sheetContext).height * 0.72,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Padding(
                    padding: const EdgeInsets.fromLTRB(20, 14, 12, 10),
                    child: Row(
                      children: [
                        Text(
                          '성경 선택',
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                            color: cs.onSurface,
                          ),
                        ),
                        const Spacer(),
                        OutlinedButton(
                          key: const Key('btn_close_book_picker'),
                          onPressed: () => Navigator.of(sheetContext).pop(),
                          child: const Text('닫기'),
                        ),
                      ],
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 6),
                    child: SegmentedButton<String>(
                      segments: const [
                        ButtonSegment(value: 'OT', label: Text('구약')),
                        ButtonSegment(value: 'NT', label: Text('신약')),
                      ],
                      selected: {selectedTestament},
                      onSelectionChanged: (selection) {
                        setSheetState(() => selectedTestament = selection.first);
                      },
                    ),
                  ),
                  Divider(height: 1, color: hairline),
                  Expanded(
                    child: ListView.builder(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      itemCount: visibleBooks.length,
                      itemBuilder: (itemContext, index) {
                        final book = visibleBooks[index];
                        final isSelected = book.bookId == _ctrl.selectedBookId;
                        return ListTile(
                          key: Key('picker_book_${book.bookId}'),
                          minTileHeight: 52,
                          selected: isSelected,
                          selectedTileColor: cs.primaryContainer,
                          title: Text(
                            book.nameKr,
                            style: TextStyle(
                              fontSize: 17,
                              fontWeight:
                                  isSelected ? FontWeight.bold : FontWeight.w500,
                              color: isSelected
                                  ? cs.onPrimaryContainer
                                  : cs.onSurface,
                            ),
                          ),
                          trailing: Text(
                            '${book.totalChapters}장',
                            style: TextStyle(
                              fontSize: 14,
                              color: PastoralTheme.mutedInk(theme.brightness),
                            ),
                          ),
                          onTap: () {
                            _ctrl.loadChapter(book.bookId, 1);
                            Navigator.of(sheetContext).pop();
                          },
                        );
                      },
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  Future<void> _openVersionPickerModal(BuildContext context) async {
    final versions = WorkstationController.supportedVersions.entries.toList();
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (sheetContext) {
        final theme = Theme.of(sheetContext);
        final cs = theme.colorScheme;
        final hairline = PastoralTheme.hairlineBorder(theme.brightness);
        final muted = PastoralTheme.mutedInk(theme.brightness);

        return SizedBox(
          key: const Key('version_picker_modal'),
          height: MediaQuery.sizeOf(sheetContext).height * 0.72,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 14, 12, 10),
                child: Row(
                  children: [
                    Text(
                      '성경 역본 선택',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: cs.onSurface,
                      ),
                    ),
                    const Spacer(),
                    OutlinedButton(
                      key: const Key('btn_close_version_picker'),
                      onPressed: () => Navigator.of(sheetContext).pop(),
                      child: const Text('닫기'),
                    ),
                  ],
                ),
              ),
              Divider(height: 1, color: hairline),
              Expanded(
                child: ListView.builder(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  itemCount: versions.length,
                  itemBuilder: (_, index) {
                    final entry = versions[index];
                    final isSelected = entry.key == _ctrl.selectedVersionCode;
                    return ListTile(
                      key: Key('version_option_${entry.key}'),
                      minTileHeight: 52,
                      selected: isSelected,
                      selectedTileColor: cs.primaryContainer,
                      title: Text(
                        entry.value,
                        style: TextStyle(
                          fontSize: 17,
                          fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                          color: isSelected ? cs.onPrimaryContainer : cs.onSurface,
                        ),
                      ),
                      trailing: isSelected
                          ? Icon(Icons.check, color: cs.primary)
                          : Text(
                              entry.key,
                              style: TextStyle(fontSize: 13, color: muted),
                            ),
                      onTap: () {
                        Navigator.of(sheetContext).pop();
                        unawaited(_ctrl.setVersionCode(entry.key));
                      },
                    );
                  },
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Future<void> _openScriptureSearchModal(BuildContext context) async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (_) => _ScriptureSearchSheet(controller: _ctrl),
    );
  }

  Widget _buildScriptureReader(
    BuildContext context, {
    required bool showBookPickerButton,
  }) {
    final theme = Theme.of(context);
    final cs = theme.colorScheme;
    final hairline = PastoralTheme.hairlineBorder(theme.brightness);
    final subtle = PastoralTheme.subtleSurface(theme.brightness);
    final bookName = _ctrl.currentBook?.nameKr ?? '성경';
    final totalCh = _ctrl.currentBook?.totalChapters ?? 1;

    return Column(
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: BoxDecoration(
            color: cs.surface,
            border: Border(bottom: BorderSide(color: hairline)),
          ),
          child: Wrap(
            spacing: 8,
            runSpacing: 8,
            crossAxisAlignment: WrapCrossAlignment.center,
            alignment: WrapAlignment.spaceBetween,
            children: [
              Wrap(
                spacing: 8,
                runSpacing: 8,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  if (showBookPickerButton)
                    OutlinedButton.icon(
                      key: const Key('btn_tablet_book_picker'),
                      onPressed: () => _openBookPickerModal(context),
                      icon: const Icon(Icons.menu_book, size: 18),
                      label: const Text('성경 선택'),
                    ),
                  Text(
                    '$bookName ${_ctrl.selectedChapter}장',
                    key: const Key('current_chapter_heading'),
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 18,
                      color: cs.onSurface,
                    ),
                  ),
                  OutlinedButton.icon(
                    key: const Key('btn_version_picker'),
                    onPressed: () => _openVersionPickerModal(context),
                    icon: const Icon(Icons.translate, size: 18),
                    label: Text(_ctrl.selectedVersionName),
                  ),
                  OutlinedButton.icon(
                    key: const Key('btn_open_search'),
                    onPressed: () => _openScriptureSearchModal(context),
                    icon: const Icon(Icons.search, size: 18),
                    label: const Text('말씀 찾기'),
                  ),
                ],
              ),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  OutlinedButton.icon(
                    key: const Key('btn_prev_chapter'),
                    onPressed: _ctrl.selectedChapter > 1 ? _ctrl.previousChapter : null,
                    icon: const Icon(Icons.chevron_left, size: 18),
                    label: const Text('이전 장'),
                  ),
                  Text(
                    '${_ctrl.selectedChapter} / $totalCh장',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      color: cs.onSurfaceVariant,
                    ),
                  ),
                  OutlinedButton.icon(
                    key: const Key('btn_next_chapter'),
                    onPressed:
                        _ctrl.selectedChapter < totalCh ? _ctrl.nextChapter : null,
                    icon: const Icon(Icons.chevron_right, size: 18),
                    label: const Text('다음 장'),
                  ),
                ],
              ),
            ],
          ),
        ),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.all(14),
            itemCount: _ctrl.chapterVerses.length,
            itemBuilder: (context, index) {
              final v = _ctrl.chapterVerses[index];
              final isSel = v.verse == _ctrl.selectedVerseNumber;
              return Card(
                color: isSel ? cs.primaryContainer : cs.surface,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: BorderSide(
                    color: isSel ? cs.primary : hairline,
                    width: isSel ? 2.0 : 1.0,
                  ),
                ),
                child: ListTile(
                  minTileHeight: 56,
                  onTap: () => _ctrl.selectVerse(v.verse),
                  leading: Container(
                    width: 34,
                    height: 34,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: isSel ? cs.primary : subtle,
                      shape: BoxShape.circle,
                    ),
                    child: Text(
                      '${v.verse}',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                        color: isSel ? cs.onPrimary : cs.onSurface,
                      ),
                    ),
                  ),
                  title: Text(
                    v.text,
                    style: TextStyle(
                      fontSize: _ctrl.scriptureFontSize,
                      height: 1.8,
                      color: cs.onSurface,
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildExegesisPanel(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(12, 10, 12, 6),
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: SegmentedButton<int>(
              showSelectedIcon: false,
              style: const ButtonStyle(
                minimumSize: WidgetStatePropertyAll<Size>(Size(48, 48)),
                padding: WidgetStatePropertyAll<EdgeInsetsGeometry>(
                  EdgeInsets.symmetric(horizontal: 10),
                ),
              ),
              segments: const [
                ButtonSegment(value: 0, label: Text('핵심 주석')),
                ButtonSegment(value: 1, label: Text('연결 말씀')),
                ButtonSegment(value: 2, label: Text('설교 준비')),
                ButtonSegment(value: 3, label: Text('예배 예전')),
              ],
              selected: {_rightTab},
              onSelectionChanged: (s) => setState(() => _rightTab = s.first),
            ),
          ),
        ),
        Expanded(child: _buildRightTabContent(context)),
      ],
    );
  }

  Widget _buildRightTabContent(BuildContext context) {
    switch (_rightTab) {
      case 0:
        return _buildCommentariesTab(context);
      case 1:
        return _buildCrossRefsTab(context);
      case 2:
        return _buildSermonPrepTab(context);
      case 3:
        return _buildLiturgyTab(context);
      default:
        return _buildCommentariesTab(context);
    }
  }

  Widget _buildCommentariesTab(BuildContext context) {
    final theme = Theme.of(context);
    final cs = theme.colorScheme;
    final warmAccent = PastoralTheme.warmAccent(theme.brightness);

    if (_ctrl.commentaries.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            '선택한 절에 등록된 핵심 주석이 없습니다.',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: _ctrl.studyFontSize,
              color: cs.onSurfaceVariant,
            ),
          ),
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(14),
      itemCount: _ctrl.commentaries.length,
      itemBuilder: (_, i) {
        final c = _ctrl.commentaries[i];
        return Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '[${c.sourceName}] ${c.title ?? ''}'.trim(),
                  style: TextStyle(
                    fontSize: _ctrl.studyFontSize,
                    fontWeight: FontWeight.bold,
                    color: warmAccent,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  c.contentMarkdown,
                  style: TextStyle(
                    fontSize: _ctrl.studyFontSize,
                    height: 1.7,
                    color: cs.onSurface,
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildCrossRefsTab(BuildContext context) {
    final cs = Theme.of(context).colorScheme;

    if (_ctrl.crossRefs.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            '선택한 절에 연결된 말씀이 없습니다.',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: _ctrl.studyFontSize,
              color: cs.onSurfaceVariant,
            ),
          ),
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(14),
      itemCount: _ctrl.crossRefs.length,
      itemBuilder: (_, i) {
        final r = _ctrl.crossRefs[i];
        return Card(
          child: ListTile(
            minTileHeight: 56,
            title: Text(
              '${r.refString} · ${r.relationshipLabel}',
              style: TextStyle(
                fontSize: _ctrl.studyFontSize,
                color: cs.primary,
                fontWeight: FontWeight.bold,
              ),
            ),
            subtitle: Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Text(
                r.fullText,
                style: TextStyle(
                  fontSize: _ctrl.studyFontSize - 1,
                  height: 1.6,
                  color: cs.onSurface,
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildSermonPrepTab(BuildContext context) {
    final cs = Theme.of(context).colorScheme;

    return ListView(
      padding: const EdgeInsets.all(14),
      children: [
        Text(
          _ctrl.activeSermon.title,
          style: TextStyle(
            fontSize: _ctrl.studyFontSize + 2,
            fontWeight: FontWeight.bold,
            color: cs.onSurface,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          '${_ctrl.activeSermon.scriptureRef} · ${_ctrl.activeSermon.sermonDate}',
          style: TextStyle(
            fontSize: _ctrl.studyFontSize - 1,
            color: cs.onSurfaceVariant,
          ),
        ),
        const SizedBox(height: 12),
        ..._ctrl.activeSermon.outline.map(
          (o) => Card(
            child: ListTile(
              minTileHeight: 56,
              title: Text(
                '[${o.section}] ${o.title}',
                style: TextStyle(
                  fontSize: _ctrl.studyFontSize,
                  fontWeight: FontWeight.bold,
                  color: cs.onSurface,
                ),
              ),
              subtitle: Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Text(
                  o.content,
                  style: TextStyle(
                    fontSize: _ctrl.studyFontSize - 1,
                    height: 1.6,
                    color: cs.onSurfaceVariant,
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildLiturgyTab(BuildContext context) {
    final theme = Theme.of(context);
    final cs = theme.colorScheme;
    final warmAccent = PastoralTheme.warmAccent(theme.brightness);
    final muted = PastoralTheme.mutedInk(theme.brightness);

    return ListView.builder(
      key: const Key('liturgy_catalog_list'),
      padding: const EdgeInsets.all(14),
      itemCount: kOfflineWorshipLiturgies.length,
      itemBuilder: (_, index) {
        final liturgy = kOfflineWorshipLiturgies[index];
        return Card(
          key: Key('liturgy_card_${liturgy.id}'),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Wrap(
                  spacing: 8,
                  runSpacing: 6,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 4,
                      ),
                      decoration: BoxDecoration(
                        color: cs.primaryContainer,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        liturgy.category,
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: cs.onPrimaryContainer,
                        ),
                      ),
                    ),
                    Text(
                      liturgy.title,
                      style: TextStyle(
                        fontSize: _ctrl.studyFontSize + 2,
                        fontWeight: FontWeight.bold,
                        color: cs.onSurface,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  liturgy.citation,
                  style: TextStyle(
                    fontSize: _ctrl.studyFontSize - 2,
                    color: muted,
                  ),
                ),
                const SizedBox(height: 12),
                for (final slide in liturgy.slides) ...[
                  if (liturgy.slides.length > 1)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Text(
                        slide.heading,
                        style: TextStyle(
                          fontSize: _ctrl.studyFontSize - 1,
                          fontWeight: FontWeight.bold,
                          color: warmAccent,
                        ),
                      ),
                    ),
                  Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: Text(
                      slide.body,
                      style: TextStyle(
                        fontSize: _ctrl.studyFontSize,
                        height: 1.7,
                        color: cs.onSurface,
                      ),
                    ),
                  ),
                ],
                const SizedBox(height: 4),
                ElevatedButton.icon(
                  key: Key('btn_liturgy_pulpit_${liturgy.id}'),
                  onPressed: () => setState(() {
                    _pulpitOverrideSlides = _ctrl.buildLiturgySlides(liturgy);
                    _isPulpitMode = true;
                  }),
                  icon: const Icon(Icons.present_to_all, size: 18),
                  label: const Text('강단 화면으로 열기'),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _ScriptureSearchSheet extends StatefulWidget {
  final WorkstationController controller;

  const _ScriptureSearchSheet({required this.controller});

  @override
  State<_ScriptureSearchSheet> createState() => _ScriptureSearchSheetState();
}

class _ScriptureSearchSheetState extends State<_ScriptureSearchSheet> {
  late final TextEditingController _queryController;

  @override
  void initState() {
    super.initState();
    _queryController = TextEditingController(text: widget.controller.searchQuery);
  }

  @override
  void dispose() {
    _queryController.dispose();
    super.dispose();
  }

  String _bookNameForId(int bookId) {
    for (final book in widget.controller.books) {
      if (book.bookId == bookId) return book.nameKr;
    }
    return '성경';
  }

  void _runSearch() {
    unawaited(widget.controller.searchScripture(_queryController.text));
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final cs = theme.colorScheme;
    final hairline = PastoralTheme.hairlineBorder(theme.brightness);
    final bottomInset = MediaQuery.viewInsetsOf(context).bottom;

    return Padding(
      padding: EdgeInsets.only(bottom: bottomInset),
      child: SizedBox(
        key: const Key('scripture_search_modal'),
        height: MediaQuery.sizeOf(context).height * 0.72,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 14, 12, 10),
              child: Row(
                children: [
                  Text(
                    '말씀 찾기',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: cs.onSurface,
                    ),
                  ),
                  const Spacer(),
                  OutlinedButton(
                    key: const Key('btn_close_search'),
                    onPressed: () => Navigator.of(context).pop(),
                    child: const Text('닫기'),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      key: const Key('input_scripture_search'),
                      controller: _queryController,
                      textInputAction: TextInputAction.search,
                      onSubmitted: (_) => _runSearch(),
                      decoration: const InputDecoration(
                        hintText: '찾으실 말씀의 단어를 입력하세요',
                        border: OutlineInputBorder(),
                        contentPadding: EdgeInsets.symmetric(
                          horizontal: 14,
                          vertical: 12,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  ElevatedButton(
                    key: const Key('btn_execute_search'),
                    onPressed: _runSearch,
                    child: const Text('검색'),
                  ),
                ],
              ),
            ),
            Divider(height: 1, color: hairline),
            Expanded(
              child: ListenableBuilder(
                listenable: widget.controller,
                builder: (context, _) {
                  final ctrl = widget.controller;
                  if (ctrl.searchQuery.isEmpty) {
                    return Center(
                      child: Padding(
                        padding: const EdgeInsets.all(24),
                        child: Text(
                          '찾으실 말씀의 단어나 구절을 입력해 주세요.',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: ctrl.studyFontSize,
                            color: cs.onSurfaceVariant,
                          ),
                        ),
                      ),
                    );
                  }
                  if (ctrl.searchResults.isEmpty) {
                    return Center(
                      child: Padding(
                        padding: const EdgeInsets.all(24),
                        child: Text(
                          '검색 결과가 없습니다.',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: ctrl.studyFontSize,
                            color: cs.onSurfaceVariant,
                          ),
                        ),
                      ),
                    );
                  }
                  return ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: ctrl.searchResults.length,
                    itemBuilder: (_, index) {
                      final verse = ctrl.searchResults[index];
                      final bookName = _bookNameForId(verse.bookId);
                      return Card(
                        child: ListTile(
                          key: Key('search_result_${verse.verseId}'),
                          minTileHeight: 56,
                          title: Text(
                            '$bookName ${verse.chapter}:${verse.verse}',
                            style: TextStyle(
                              fontSize: ctrl.studyFontSize,
                              fontWeight: FontWeight.bold,
                              color: cs.primary,
                            ),
                          ),
                          subtitle: Padding(
                            padding: const EdgeInsets.only(top: 4),
                            child: Text(
                              verse.text,
                              style: TextStyle(
                                fontSize: ctrl.studyFontSize - 1,
                                height: 1.6,
                                color: cs.onSurface,
                              ),
                            ),
                          ),
                          onTap: () {
                            Navigator.of(context).pop();
                            unawaited(
                              ctrl.loadChapter(
                                verse.bookId,
                                verse.chapter,
                                verseNumber: verse.verse,
                              ),
                            );
                          },
                        ),
                      );
                    },
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
