"""Tests for subtitle_qc.py. Run: python3 -m unittest discover tests"""

import io
import json
import os
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, 'plugins', 'subtitle-qc', 'skills', 'subtitle-qc')
FIXTURES = os.path.join(ROOT, 'tests', 'fixtures')
sys.path.insert(0, os.path.join(SKILL, 'scripts'))

import subtitle_qc as qc  # noqa: E402

VARIANTS = 'ABCDEFGJKLMNOPQ'  # same three cues, different encodings/quirks


def fixture(name):
    return os.path.join(FIXTURES, name)


def run(*argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = qc.main(list(argv))
    return code, buf.getvalue()


def words(cues):
    text = ' '.join(qc.visible(c.text) for c in cues)
    return re.findall(r'\w+', text)


class ParseTest(unittest.TestCase):
    def test_variants_parse_to_the_same_three_cues(self):
        names = [f for f in os.listdir(FIXTURES) if f[0] in VARIANTS and f[1] == '_']
        self.assertEqual(len(names), len(VARIANTS))
        for name in names:
            with self.subTest(name=name):
                sub = qc.parse(fixture(name))
                self.assertEqual(len(sub.cues), 3)
                self.assertEqual(sub.cues[0].start, 0)
                self.assertEqual(sub.cues[0].end, 1680)
                self.assertTrue(qc.visible(sub.cues[2].text).startswith('corner of Mill'))

    def test_tags_do_not_count_as_characters(self):
        plain = qc.parse(fixture('A_valid.srt')).cues[0]
        tagged = qc.parse(fixture('L_html_tags.srt')).cues[0]
        self.assertEqual(plain.chars, tagged.chars)

    def test_hard_problems(self):
        overlap = qc.hard_problems(qc.parse(fixture('H_overlap.srt')).cues)
        self.assertEqual(overlap[0]['cue'], 2)
        self.assertIn('overlaps', overlap[0]['problem'])
        reversed_ = qc.hard_problems(qc.parse(fixture('I_end_before_start.srt')).cues)
        self.assertIn('not after start', reversed_[0]['problem'])

    def test_latin1_falls_back_with_warning(self):
        sub = qc.parse(fixture('Q_latin1.srt'))
        self.assertIn('café', sub.cues[0].text)
        self.assertTrue(sub.warnings)

    def test_cjk_detection(self):
        self.assertTrue(qc.is_cjk_text('大家好，欢迎回到我们的频道。'))
        self.assertFalse(qc.is_cjk_text('Welcome back to Small Shop Stories.'))


class FixTest(unittest.TestCase):
    def thresholds(self, cues):
        return qc.pick_thresholds(cues, qc.main.__globals__['argparse'].Namespace(
            preset=None, cps=None, max_chars=None, max_lines=None,
            min_duration=None, max_duration=None, min_gap=None))

    def test_fix_never_changes_words(self):
        for name in ('word_timed.srt', 'whisper_back_to_back.srt', 'cjk.srt', 'M_ass_position.srt'):
            with self.subTest(name=name):
                cues = qc.parse(fixture(name)).cues
                fixed, _ = qc.fix(cues, self.thresholds(cues), ['extend', 'merge', 'gaps', 'lines'])
                self.assertEqual(words(cues), words(fixed))
                self.assertEqual(
                    ''.join(qc.visible(c.text) for c in cues).replace(' ', '').replace('\n', ''),
                    ''.join(qc.visible(c.text) for c in fixed).replace(' ', '').replace('\n', ''),
                )

    def test_fix_reduces_failures_and_keeps_order(self):
        cues = qc.parse(fixture('word_timed.srt')).cues
        th = self.thresholds(cues)
        fixed, _ = qc.fix(cues, th, ['extend', 'merge', 'gaps', 'lines'])
        before = qc.summarize(cues, th)
        after = qc.summarize(fixed, th)
        self.assertLess(after['over_cps'], before['over_cps'])
        self.assertEqual(after['hard_problems'], [])
        for a, b in zip(fixed, fixed[1:]):
            self.assertGreaterEqual(b.start - a.end, 0)
            self.assertLessEqual(a.dur, th.max_dur_ms)

    def test_no_merge_across_speaker_change(self):
        cues = qc.parse(fixture('word_timed.srt')).cues
        fixed, _ = qc.fix(cues, self.thresholds(cues), ['extend', 'merge'])
        dialogue = [c for c in fixed if c.text.startswith('- Is it free?')]
        self.assertEqual(dialogue[0].text, '- Is it free?\n- Yes.')

    def test_hard_problem_cues_untouched(self):
        cues = qc.parse(fixture('H_overlap.srt')).cues
        fixed, _ = qc.fix(cues, self.thresholds(cues), ['extend', 'merge', 'gaps', 'lines'])
        self.assertEqual((fixed[1].start, fixed[1].end, fixed[1].lines),
                         (cues[1].start, cues[1].end, cues[1].lines))

    def test_refuses_to_overwrite_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'a.srt')
            with open(fixture('A_valid.srt'), 'rb') as src, open(path, 'wb') as dst:
                dst.write(src.read())
            with self.assertRaises(SystemExit):
                run('fix', path, '-o', path)


class RoundTripTest(unittest.TestCase):
    def test_formats_survive(self):
        cases = {
            'D_crlf.srt': lambda b: b'\r\n' in b,
            'C_bom.srt': lambda b: b.startswith(b'\xef\xbb\xbf'),
            'whisper_back_to_back.vtt': lambda b: b.startswith(b'WEBVTT') and b'.000 -->' in b,
            'P_coords_after_time.srt': lambda b: b'X1:100 X2:600' in b,
        }
        with tempfile.TemporaryDirectory() as tmp:
            for name, ok in cases.items():
                with self.subTest(name=name):
                    out = os.path.join(tmp, name)
                    run('fix', fixture(name), '-o', out)
                    with open(out, 'rb') as f:
                        self.assertTrue(ok(f.read()))
                    self.assertEqual(len(qc.parse(out).cues) > 0, True)


class ApplyTest(unittest.TestCase):
    def test_text_split_and_time_edits(self):
        with tempfile.TemporaryDirectory() as tmp:
            edits = os.path.join(tmp, 'edits.json')
            out = os.path.join(tmp, 'out.srt')
            with open(edits, 'w', encoding='utf-8') as f:
                json.dump({'cues': [
                    {'cue': 1, 'text': '大家好，欢迎回来。'},
                    {'cue': 4, 'split': [{'text': '如果字幕闪得太快，'}, {'text': '观众就读不完。'}]},
                    {'cue': 2, 'end': '00:00:01,900'},
                ]}, f, ensure_ascii=False)
            run('apply', fixture('cjk.srt'), edits, '-o', out)
            cues = qc.parse(out).cues
            self.assertEqual(len(cues), 5)
            self.assertEqual(cues[0].text, '大家好，欢迎回来。')
            self.assertEqual(cues[1].end, 1900)
            self.assertEqual(cues[3].start, 5500)
            self.assertEqual(cues[4].end, 8000)
            self.assertEqual(cues[4].start - cues[3].end, 80)
            # 9 vs 7 characters share the 2.42 s that is left after the gap.
            self.assertAlmostEqual(cues[3].dur / (cues[3].dur + cues[4].dur), 9 / 16, places=2)


if __name__ == '__main__':
    unittest.main()
