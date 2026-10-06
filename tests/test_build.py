from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("builder", ROOT / "build.py")
builder = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = builder
spec.loader.exec_module(builder)

xml = (ROOT / "tests" / "sample_rss.xml").read_bytes()
posts = builder.parse_rss(xml, max_posts=10, excerpt_chars=100)

assert len(posts) == 2
assert posts[0].post_id == "223123456789"
assert posts[1].post_id == "223000000001"
assert "HTML" in posts[0].excerpt
assert "<strong>" not in posts[0].excerpt
print("OK: RSS parser tests passed")
