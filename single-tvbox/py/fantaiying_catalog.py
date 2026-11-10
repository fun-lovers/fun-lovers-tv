# -*- coding: utf-8 -*-
"""饭太硬 TVBox 多仓配置适配器。

读取上游 TVBox 配置，筛选声明为 MacCMS/vod API 的站点，并将其
映射为单个 TVBox Python Spider。此脚本不绕过付费、登录或访问控制。
上游配置及其站点随时可能变化；只展示可识别的 type=1/API 项。
"""
import json
import re
import urllib.parse
import requests

CONFIG_URL = "http://www.xn--fhq1a75e.cc/tv"
UA = "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 TVBox"
TIMEOUT = 18


class Spider:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": UA})
        self.config = None
        self.selected = {}
        self.classes = {}

    def getName(self):
        return "饭太硬点播聚合"

    def init(self, extend=""):
        self._load_config()

    def _request_json(self, url, params=None):
        response = self.session.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()

    def _load_config(self):
        if self.config is not None:
            return
        response = self.session.get(CONFIG_URL, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("上游配置不是 JSON 对象")
        sites = data.get("sites") or []
        for site in sites:
            if not isinstance(site, dict):
                continue
            api = str(site.get("api") or "").strip()
            kind = site.get("type")
            # 仅接入标准 MacCMS API；忽略脚本、解析器、网盘和其他类型。
            if kind == 1 and api.startswith(("http://", "https://")):
                key = str(site.get("key") or site.get("name") or "")
                if key:
                    self.selected[key] = site
        self.config = data

    def _site(self, key):
        self._load_config()
        return self.selected.get(str(key))

    def homeContent(self, filter):
        try:
            self._load_config()
            classes = []
            for key, site in self.selected.items():
                name = str(site.get("name") or key)
                classes.append({"type_id": key, "type_name": name})
            return {"class": classes}
        except Exception:
            return {"class": []}

    def homeVideoContent(self):
        self._load_config()
        cards = []
        # 首页每个上游站点取少量最新数据，限制请求量。
        for key in list(self.selected.keys())[:8]:
            try:
                data = self._request_json(self.selected[key]["api"], {"ac": "videolist", "pg": 1})
                cards.extend(self._cards(data)[:6])
            except Exception:
                continue
        return {"list": cards}

    def _cards(self, data, site_key=None):
        if isinstance(data, list):
            rows = data
        elif isinstance(data, dict):
            rows = data.get("list") or data.get("data") or []
            if isinstance(rows, dict):
                rows = rows.get("list") or []
        else:
            rows = []
        result = []
        for item in rows:
            if not isinstance(item, dict):
                continue
            ident = item.get("vod_id") or item.get("id")
            name = item.get("vod_name") or item.get("name")
            if ident is None or not name:
                continue
            result.append({
                "vod_id": (str(site_key) + "@@" + str(ident)) if site_key else str(ident),
                "vod_name": str(name),
                "vod_pic": str(item.get("vod_pic") or item.get("pic") or ""),
                "vod_remarks": str(item.get("vod_remarks") or item.get("remarks") or ""),
                "vod_year": str(item.get("vod_year") or ""),
                "vod_content": str(item.get("vod_content") or item.get("content") or "")[:500]
            })
        return result

    def categoryContent(self, tid, pg=1, filter=False, extend=None):
        site = self._site(tid)
        if not site:
            return {"list": [], "page": int(pg), "pagecount": 1, "limit": 20, "total": 0}
        try:
            data = self._request_json(site["api"], {"ac": "videolist", "pg": max(1, int(pg))})
            cards = self._cards(data, str(tid))
            total = 0
            if isinstance(data, dict):
                total = int(data.get("total") or data.get("pagecount") or 0)
            return {"list": cards, "page": int(pg), "pagecount": max(1, total), "limit": 20, "total": total}
        except Exception:
            return {"list": [], "page": int(pg), "pagecount": 1, "limit": 20, "total": 0}

    def searchContent(self, key, quick=False, pg=1):
        self._load_config()
        cards = []
        for site in list(self.selected.values())[:10]:
            try:
                data = self._request_json(site["api"], {
                    "ac": "videolist", "wd": str(key), "pg": max(1, int(pg))
                })
                cards.extend(self._cards(data, str(site.get("key") or site.get("name") or "")))
            except Exception:
                continue
        return {"list": cards, "page": int(pg), "pagecount": 1, "limit": len(cards), "total": len(cards)}

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        # 聚合站点详情 ID 使用 key@@vod_id，避免不同资源站 ID 冲突。
        raw = str(ids[0])
        if "@@" not in raw:
            return {"list": []}
        key, vod_id = raw.split("@@", 1)
        site = self._site(key)
        if not site:
            return {"list": []}
        try:
            data = self._request_json(site["api"], {"ac": "detail", "ids": vod_id})
            rows = data.get("list") or data.get("data") or [] if isinstance(data, dict) else []
            if isinstance(rows, dict):
                rows = [rows]
            if not rows:
                return {"list": []}
            item = rows[0]
            play_from = str(item.get("vod_play_from") or "")
            play_url = str(item.get("vod_play_url") or "")
            item["vod_id"] = raw
            item["vod_play_from"] = play_from
            item["vod_play_url"] = play_url
            return {"list": [item]}
        except Exception:
            return {"list": []}

    def playerContent(self, flag, pid, vipFlags):
        return {"parse": 0, "playUrl": "", "url": pid}

    def isVideoFormat(self, url):
        return str(url).lower().split("?")[0].endswith((".m3u8", ".mp4", ".mpd", ".flv"))

    def manualVideoCheck(self):
        return False
