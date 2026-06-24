#!/usr/bin/env python3
# 埼京線・京浜東北線の運行情報を Yahoo!路線情報 から取得し delay.json を生成。
# 依存ゼロ(標準ライブラリのみ)。GitHub Actions から10分毎に実行する想定。
# 出力は旧rti-giken互換の配列(=問題のある路線だけ要素が入る)。平常時は [] 。
import json, re, sys, urllib.request, datetime

# 監視対象: (出力路線名, Yahoo運行情報の詳細ページURL)
# ※URLは Yahoo!路線情報で該当路線を開いて一度だけコピペ:
#    https://transit.yahoo.co.jp/diainfo/detail/<id>/0
TARGETS = [
    ("埼京線",     "https://transit.yahoo.co.jp/diainfo/50/0"),
    ("京浜東北線", "https://transit.yahoo.co.jp/diainfo/22/0"),
]
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ja"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "replace")

def status_of(html):
    # ServiceStatus ブロック内の最初の <dd class="..."> を見る (normal / trouble など)
    m = re.search(r'ServiceStatus.*?<dd class="([A-Za-z]+)">(.*?)</dd>', html, re.S)
    if not m:
        return None, ""
    cls = m.group(1)
    text = re.sub(r"<[^>]+>", "", m.group(2))
    text = re.sub(r"\s+", " ", text).strip()
    return cls, text

def main():
    out = []
    for name, url in TARGETS:
        if url.startswith("<<"):
            print(f"[skip] {name}: URL未設定", file=sys.stderr); continue
        try:
            cls, text = status_of(fetch(url))
        except Exception as e:
            print(f"[err]  {name}: {e}", file=sys.stderr); continue
        print(f"[ok]   {name}: {cls} / {text[:50]}", file=sys.stderr)
        if cls and cls != "normal":   # normal以外(trouble等)＝何か起きてる
            out.append({
                "name": name, "company": "JR東日本",
                "status": text, "cls": cls,
                "lastupdate_gmt": int(datetime.datetime.utcnow().timestamp()),
                "source": "Yahoo路線情報"
            })
    with open("delay.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"wrote delay.json (問題のある路線 {len(out)} 件)", file=sys.stderr)

if __name__ == "__main__":
    main()
