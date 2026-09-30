"""무드 시안 비교 페이지: out/ask/mood-*.html 을 나란히 보여주는 index.html 생성."""
import sys, pathlib, html
d = pathlib.Path(sys.argv[1])
files = sorted(d.glob("mood-*.html"))
cols = "".join(
    f'<figure><div class="label">{f.stem.split("-")[-1].upper()}</div>'
    f'<iframe src="{f.name}" loading="eager"></iframe></figure>' for f in files)
(d / "index.html").write_text(f"""<!doctype html><html lang="ko"><meta charset="utf-8">
<title>어떤 느낌이 좋으세요?</title>
<style>
body{{margin:0;background:#f2f2f0;font-family:-apple-system,'Pretendard',sans-serif;color:#1a1a1a}}
h1{{text-align:center;font-size:28px;margin:40px 0 8px}} p{{text-align:center;color:#666;margin:0 0 32px;font-size:17px}}
.row{{display:flex;gap:40px;justify-content:center;padding:0 40px 60px}}
figure{{margin:0;text-align:center}} .label{{font-size:40px;font-weight:800;margin-bottom:12px}}
iframe{{width:375px;height:812px;border:0;border-radius:28px;background:#fff;box-shadow:0 8px 30px rgba(0,0,0,.12)}}
</style>
<h1>세 가지 중 이 앱에 가장 어울리는 느낌은?</h1><p>내용은 같고 느낌만 다릅니다. 글자 하나로 답해주세요.</p>
<div class="row">{cols}</div></html>""", encoding="utf-8")
print("wrote", d / "index.html", len(files), "options")
