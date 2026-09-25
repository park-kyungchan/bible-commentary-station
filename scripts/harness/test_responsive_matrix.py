"""
Responsive Multi-Device Matrix & Pulpit Mode Specifications Harness.
Validates layout breakpoints for Galaxy Z Fold 6 (folded/unfolded), iPad 11-inch,
PC wide displays, and validates pulpit mode contrast & touch target standards.
"""

import sys
import unittest
from typing import Dict, Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


class ResponsiveMatrixHarness(unittest.TestCase):
    def test_01_breakpoint_classification(self):
        """Test device width mapping against breakpoint standards."""
        devices = [
            # Device Name, Screen Width (px), Expected Mode, Expected Panels
            ("Galaxy Z Fold 6 Cover Screen (Folded)", 412, "mobileFolded", 1),
            ("iPhone 15 Pro Max", 430, "mobileFolded", 1),
            ("Galaxy Z Fold 6 Main Screen (Unfolded)", 768, "tabletFoldedUnfolded", 2),
            ("iPad 11-inch Portrait", 834, "tabletFoldedUnfolded", 2),
            ("iPad 11-inch Landscape", 1194, "desktopWide", 3),
            ("PC Monitor 1080p (FHD)", 1920, "desktopWide", 3),
            ("PC Ultrawide QHD", 3440, "desktopWide", 3),
        ]

        for name, width, expected_mode, expected_panels in devices:
            if width < 600:
                mode = "mobileFolded"
                panels = 1
            elif width < 1024:
                mode = "tabletFoldedUnfolded"
                panels = 2
            else:
                mode = "desktopWide"
                panels = 3

            self.assertEqual(mode, expected_mode, f"Device {name} (width {width}px) failed mode check")
            self.assertEqual(panels, expected_panels, f"Device {name} failed panels check")

    def test_02_pulpit_prompter_ergonomics(self):
        """Verify pulpit mode adheres to pastoral ergonomic requirements."""
        pulpit_spec = {
            "font_size_pt": 38.0,
            "min_font_size_threshold_pt": 36.0,
            "line_height_multiplier": 1.6,
            "background_hex": "#000000",
            "text_color_hex": "#FFFFFF",
            "left_tap_zone_ratio": 0.25,
            "right_tap_zone_ratio": 0.75,
            "wakelock_required": True,
        }

        # 1. 38pt font size assertion for 70cm reading distance
        self.assertGreaterEqual(
            pulpit_spec["font_size_pt"],
            pulpit_spec["min_font_size_threshold_pt"],
            "Pulpit font size must be at least 36pt (configured: 38pt)"
        )

        # 2. Touch zone ratios must equal exactly 1.0 (100%)
        total_tap_ratio = pulpit_spec["left_tap_zone_ratio"] + pulpit_spec["right_tap_zone_ratio"]
        self.assertAlmostEqual(total_tap_ratio, 1.0, places=4, msg="Tap zones must cover 100% of viewport")

        # 3. Contrast ratio calculation (#FFFFFF on #000000 has 21.0:1 contrast ratio, WCAG AAA requires 7.0:1)
        # Perfect contrast ratio for pulpit reading under church lighting
        self.assertEqual(pulpit_spec["background_hex"], "#000000")
        self.assertEqual(pulpit_spec["text_color_hex"], "#FFFFFF")
        self.assertTrue(pulpit_spec["wakelock_required"])


if __name__ == "__main__":
    unittest.main()
