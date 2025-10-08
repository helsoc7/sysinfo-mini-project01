import unittest, json
import sysinfo as s

class T(unittest.TestCase):
    def test_render_text_sections(self):
        d = {
            "timestamp": "2025-01-01_12-00-00",
            "cpu":{"usage_percent": 33.3},
            "memory":{"total_mb":1000,"used_mb":400,"free_mb":600},
            "disk":{"root":{"size":"10G","used":"4G","avail":"6G","use_percent":"40%","mount":"/"}},
            "network":{"target":"8.8.8.8","reachable": True}
        }
        t = s.render_text(d)
        for word in ["System Report","CPU","Memory","Disk","Network"]:
            self.assertIn(word, t)

    def test_html_title(self):
        d = {
            "timestamp": "2025-01-01_12-00-00",
            "cpu":{"usage_percent": 10.0},
            "memory":{"total_mb":1000,"used_mb":100,"free_mb":900},
            "disk":{"root":{"size":"10G","used":"1G","avail":"9G","use_percent":"10%","mount":"/"}},
            "network":{"skipped": True}
        }
        h = s.render_html(d)
        self.assertIn("<title>System Report</title>", h)

if __name__ == "__main__":
    unittest.main()

