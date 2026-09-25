import 'package:flutter/material.dart';

enum DeviceLayoutType {
  mobileFolded, // Z Fold 6 Cover screen or normal phone (< 600px)
  tabletFoldedUnfolded, // Z Fold 6 Unfolded or iPad portrait (600px ~ 1023px)
  desktopWide, // PC Desktop / iPad landscape (>= 1024px)
}

class ResponsiveLayout extends StatelessWidget {
  final Widget mobile;
  final Widget tablet;
  final Widget desktop;

  const ResponsiveLayout({
    super.key,
    required this.mobile,
    required this.tablet,
    required this.desktop,
  });

  static DeviceLayoutType getDeviceType(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    if (width < 600) {
      return DeviceLayoutType.mobileFolded;
    } else if (width < 1024) {
      return DeviceLayoutType.tabletFoldedUnfolded;
    } else {
      return DeviceLayoutType.desktopWide;
    }
  }

  static bool isDesktop(BuildContext context) =>
      MediaQuery.of(context).size.width >= 1024;

  static bool isFoldableOrTablet(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    return width >= 600 && width < 1024;
  }

  static bool isMobile(BuildContext context) =>
      MediaQuery.of(context).size.width < 600;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= 1024) {
          return desktop;
        } else if (constraints.maxWidth >= 600) {
          return tablet;
        } else {
          return mobile;
        }
      },
    );
  }
}
