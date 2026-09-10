#!/usr/bin/env python3
"""Offline unit tests for the plausibility gate in fetch.py (contract §3). Run: python3 tests/test_fetch_gate.py"""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import fetch  # noqa: E402

NAV_ONLY = "[Skip to main content](https://museum.example/#main)\n\n" + "## Main navigation\n\n" + "".join(
    f"*   [— Menu item number {i}](https://museum.example/section/{i})\n" for i in range(60)
) + "\n## Footer Legal Links\n\n*   [Privacy policy](https://museum.example/privacy)\n*   [Cookies](https://museum.example/cookies)\n\n© 2026 The Trustees\n"

PROSE = ("In July 1799, a group of soldiers stumbled upon an object that changed the understanding of the ancient world. "
         "The fragment of a stela carries the same decree in three scripts, and it became the key to a script nobody had read for centuries. "
         "The museum received the object in 1802 and it has been on public display almost continuously since then, apart from wartime storage. ") * 4

SIDEBAR_HEAVY = NAV_ONLY + "\n\n" + PROSE  # documentation page: big menu, but real prose under it


WILEY_WALL = ("Journal\n\nArticles\n\nActions\n\nTools\n\nFollow journal\n\nCookies disabled\n\n"
              "Cookies are disabled for this browser. Wiley Online Library requires cookies for authentication and use of other site features; "
              "therefore, cookies must be enabled to browse the site. Detailed information on how Wiley uses cookies can be found in our Privacy Policy.\n\n"
              "Log in to Wiley Online Library\n\nNEW USER >\n\nINSTITUTIONAL LOGIN >\n\nChange Password\n\nPassword Changed Successfully\n\n"
              "Your password has been changed\n\nCreate a new account\n\nReturning user\n\nForgot your password?\n\nEnter your email address below.\n\nPlease check your email\n" * 2)


class GateTest(unittest.TestCase):
    def test_wiley_cookie_wall_is_consent_wall(self):
        self.assertGreaterEqual(len(WILEY_WALL), fetch.MIN_CHARS)
        self.assertEqual(fetch.gate(WILEY_WALL), "failed:consent-wall")

    def test_nav_only_fails(self):
        self.assertGreaterEqual(len(NAV_ONLY), fetch.MIN_CHARS)
        share, words = fetch.nav_stats(NAV_ONLY)
        self.assertGreaterEqual(share, fetch.NAV_SHARE_MAX)
        self.assertLess(words, fetch.NAV_PROSE_MIN)
        self.assertEqual(fetch.gate(NAV_ONLY), "failed:nav-only")

    def test_prose_passes(self):
        self.assertEqual(fetch.gate(PROSE), "passed")

    def test_sidebar_with_prose_passes(self):
        share, words = fetch.nav_stats(SIDEBAR_HEAVY)
        self.assertGreaterEqual(share, 0.5)
        self.assertGreaterEqual(words, fetch.NAV_PROSE_MIN)
        self.assertEqual(fetch.gate(SIDEBAR_HEAVY), "passed")

    def test_hard_wrapped_text_passes(self):
        # RFC / PDF style: 72-column lines with no Markdown; must not be read as navigation
        wrapped = "\n".join(PROSE[i:i + 72] for i in range(0, len(PROSE), 72))
        self.assertEqual(fetch.gate(wrapped), "passed")

    def test_short_page_is_length_not_nav(self):
        self.assertEqual(fetch.gate("[Home](https://x.example)\n[About](https://x.example/about)\n"), "failed:length")


if __name__ == "__main__":
    unittest.main()
