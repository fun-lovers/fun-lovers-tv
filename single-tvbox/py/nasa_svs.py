# -*- coding: utf-8 -*-
"""NASA Scientific Visualization Studio (SVS) public-media spider."""
import re
import urllib.parse
import requests

BASE = "https://svs.gsfc.nasa.gov"
UA = "single-tvbox/1.0 (NASA SVS public media spider)"

class Spider:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": UA})

    def getName(self):
        return "NASA 科学影像"

    def init(self, extend=""):
        return None

    def _json(self, url):
        r = self.session.get(url, timeout=25)
        r.raise_for_status()
        return r.json()

    def _search(self, term, page=1):
        params = {"search": term, "limit": 24, "offset": (max(1, int(page))-1)*24}
        return self._json(BASE + "/api/search/?" + urllib.parse.urlencode(params))

    def _card(self, item):
        ident = str(item.get("id") or "")
        image = item.get("main_image") or {}
        return {"vod_id": ident, "vod_name": str(item.get("title") or "NASA SVS"),
                "vod_pic": str(image.get("url") or ""),
                "vod_remarks": str(item.get("release_date") or "")[:10],
                "vod_year": str(item.get("release_date") or "")[:4],
                "vod_content": re.sub(r"\\s+", " ", str(item.get("description") or "")).strip()[:500]}

    def homeContent(self, filter):
        return {"class": [
            {"type_id": "latest", "type_name": "最新科学影像"},
            {"type_id": "earth", "type_name": "地球与气候"},
            {"type_id": "solar", "type_name": "太阳系与行星"},
            {"type_id": "space", "type_name": "太空探索"},
            {"type_id": "climate", "type_name": "气候变化"}
        ]}

    def homeVideoContent(self):
        return self.categoryContent("latest", 1, False, {})

    def categoryContent(self, tid, pg=1, filter=False, extend=None):
        terms = {"latest": "", "earth": "Earth", "solar": "Solar System",
                 "space": "space exploration", "climate": "climate change"}
        term = terms.get(str(tid), "")
        try:
            data = self._search(term, pg)
            docs = data.get("results") or []
            return {"page": int(pg), "pagecount": max(1, (int(data.get("count", 0))+23)//24),
                    "limit": 24, "total": int(data.get("count", 0)),
                    "list": [self._card(x) for x in docs if x.get("id")]}
        except Exception:
            return {"page": int(pg), "pagecount": 1, "limit": 24, "total": 0, "list": []}

    def detailContent(self, ids):
        ident = str(ids[0]) if ids else ""
        if not ident.isdigit():
            return {"list": []}
        try:
            data = self._json(BASE + "/api/" + ident + "/")
            plays = []
            main = data.get("main_video") or {}
            if main.get("url") and str(main.get("url")).lower().split("?")[0].endswith((".mp4", ".webm")):
                plays.append(str(main.get("filename") or "主视频") + "$" + main["url"])
            for group in data.get("media_groups") or []:
                for item in group.get("items") or []:
                    media = item.get("media") or item.get("instance") or {}
                    url = str(media.get("url") or "")
                    if url.lower().split("?")[0].endswith((".mp4", ".webm")):
                        label = str(media.get("filename") or item.get("title") or "视频")
                        if not any(p.endswith("$"+url) for p in plays):
                            plays.append(label + "$" + url)
            card = self._card(data)
            card.update({"vod_play_from": "NASA SVS", "vod_play_url": "#".join(plays[:12])})
            return {"list": [card]} if plays else {"list": []}
        except Exception:
            return {"list": []}

    def searchContent(self, key, quick=False, pg=1):
        try:
            data = self._search(str(key), pg)
            docs = data.get("results") or []
            return {"page": int(pg), "pagecount": max(1, (int(data.get("count", 0))+23)//24),
                    "limit": 24, "total": int(data.get("count", 0)),
                    "list": [self._card(x) for x in docs if x.get("id")]}
        except Exception:
            return {"page": int(pg), "pagecount": 1, "limit": 24, "total": 0, "list": []}

    def playerContent(self, flag, pid, vipFlags):
        return {"parse": 0, "playUrl": "", "url": pid,
                "header": {"User-Agent": UA}}

    def isVideoFormat(self, url):
        return url.lower().split("?")[0].endswith((".mp4", ".webm"))

    def manualVideoCheck(self):
        return False
