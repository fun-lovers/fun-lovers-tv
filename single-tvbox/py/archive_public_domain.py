# -*- coding: utf-8 -*-
"""Internet Archive public-domain video spider for TVBox.

Only items whose metadata explicitly declares a public-domain license are listed.
This is a metadata-based filter, not a legal opinion; check each item's rights page.
"""
import json
import re
import urllib.parse
import requests

BASE = "https://archive.org"
SEARCH = BASE + "/advancedsearch.php"
UA = "single-tvbox/1.0 (TVBox public media spider)"
FIELDS = ["identifier", "title", "year", "description", "licenseurl", "mediatype"]

class Spider:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": UA})
        self.cache = {}

    def getName(self):
        return "Internet Archive 公共领域影像"

    def init(self, extend=""):
        return None

    def _get_json(self, url):
        r = self.session.get(url, timeout=25)
        r.raise_for_status()
        return r.json()

    def _search(self, query, page=1, rows=24):
        params = [("q", query), ("output", "json"), ("rows", str(rows)),
                  ("page", str(page))]
        for field in FIELDS:
            params.append(("fl[]", field))
        url = SEARCH + "?" + urllib.parse.urlencode(params)
        data = self._get_json(url)
        return data.get("response", {})

    def _public_domain(self, item):
        lic = str(item.get("licenseurl") or "").lower()
        return "publicdomain" in lic or "public-domain" in lic or "creativecommons.org/publicdomain" in lic

    def _card(self, item):
        ident = str(item.get("identifier") or "")
        title = str(item.get("title") or ident)
        desc = re.sub(r"\\s+", " ", str(item.get("description") or "")).strip()
        year = str(item.get("year") or "")
        return {"vod_id": ident, "vod_name": title, "vod_pic": "",
                "vod_remarks": year or "公共领域", "vod_year": year,
                "vod_content": desc[:500]}

    def homeContent(self, filter):
        return {"class": [
            {"type_id": "publicdomain", "type_name": "公共领域电影"},
            {"type_id": "education", "type_name": "教育与科学"},
            {"type_id": "animation", "type_name": "动画"},
            {"type_id": "silent", "type_name": "默片与历史影像"}
        ]}

    def homeVideoContent(self):
        return self.categoryContent("publicdomain", 1, False, {}) 

    def categoryContent(self, tid, pg=1, filter=False, extend=None):
        queries = {
            "publicdomain": 'mediatype:movies AND licenseurl:*publicdomain*',
            "education": 'mediatype:movies AND licenseurl:*publicdomain* AND (subject:education OR subject:science)',
            "animation": 'mediatype:movies AND licenseurl:*publicdomain* AND subject:animation',
            "silent": 'mediatype:movies AND licenseurl:*publicdomain* AND subject:"silent films"'
        }
        query = queries.get(str(tid), queries["publicdomain"])
        try:
            data = self._search(query, max(1, int(pg)), 24)
            docs = [x for x in data.get("docs", []) if self._public_domain(x)]
            return {"page": int(pg), "pagecount": max(1, (int(data.get("numFound", 0)) + 23)//24),
                    "limit": 24, "total": int(data.get("numFound", 0)),
                    "list": [self._card(x) for x in docs if x.get("identifier")]}
        except Exception:
            return {"page": int(pg), "pagecount": 1, "limit": 24, "total": 0, "list": []}

    def detailContent(self, ids):
        ident = str(ids[0]) if ids else ""
        if not re.match(r"^[A-Za-z0-9._-]+$", ident):
            return {"list": []}
        try:
            meta = self._get_json(BASE + "/metadata/" + urllib.parse.quote(ident, safe=""))
            md = meta.get("metadata", {})
            lic = str(md.get("licenseurl") or "").lower()
            if not ("publicdomain" in lic or "public-domain" in lic or "creativecommons.org/publicdomain" in lic):
                return {"list": []}
            files = meta.get("files", [])
            candidates = []
            for f in files:
                name = str(f.get("name") or "")
                low = name.lower()
                if f.get("private") == "true" or f.get("private") is True:
                    continue
                if low.endswith((".mp4", ".webm", ".ogv", ".mpg", ".mpeg")):
                    size = int(f.get("size") or 0)
                    score = (4 if low.endswith(".mp4") else 3 if low.endswith(".webm") else 1)
                    candidates.append((score, size, name))
            candidates.sort(reverse=True)
            plays = []
            for _, _, name in candidates[:5]:
                url = BASE + "/download/" + urllib.parse.quote(ident, safe="") + "/" + urllib.parse.quote(name, safe="/")
                plays.append(name + "$" + url)
            vod = self._card({"identifier": ident, "title": md.get("title"),
                              "year": md.get("year"), "description": md.get("description")})
            vod.update({"vod_play_from": "Internet Archive", "vod_play_url": "#".join(plays)})
            return {"list": [vod]} if plays else {"list": []}
        except Exception:
            return {"list": []}

    def searchContent(self, key, quick=False, pg=1):
        query = 'mediatype:movies AND licenseurl:*publicdomain* AND title:(' + str(key).replace('"', '') + ')'
        try:
            data = self._search(query, max(1, int(pg)), 24)
            docs = [x for x in data.get("docs", []) if self._public_domain(x)]
            return {"page": int(pg), "pagecount": 1, "limit": 24,
                    "total": int(data.get("numFound", 0)), "list": [self._card(x) for x in docs]}
        except Exception:
            return {"page": int(pg), "pagecount": 1, "limit": 24, "total": 0, "list": []}

    def playerContent(self, flag, pid, vipFlags):
        return {"parse": 0, "playUrl": "", "url": pid,
                "header": {"User-Agent": UA}}

    def isVideoFormat(self, url):
        return any(url.lower().split("?")[0].endswith(x) for x in (".mp4", ".webm", ".ogv", ".mpg", ".mpeg"))

    def manualVideoCheck(self):
        return False
