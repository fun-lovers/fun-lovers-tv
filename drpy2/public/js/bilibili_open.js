var rule = {
    title: '哔哩哔哩（官方公开元数据）',
    host: 'https://www.bilibili.com',
    homeUrl: 'https://www.bilibili.com',
    searchable: 1,
    quickSearch: 1,
    filterable: 0,
    headers: {
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://www.bilibili.com/'
    },
    class_name: '综合',
    class_url: '综合',
    play_parse: true,

    一级: function (tid, pg, filter, extend) {
        var keyword = (tid && tid !== '综合') ? tid : '热门';
        var api = 'https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword='
            + encodeURIComponent(keyword) + '&page=' + (pg || 1);
        var data = {};
        try { data = JSON.parse(request(api, { headers: rule.headers })); } catch (e) { return []; }
        var rows = data && data.data && data.data.result || [];
        return rows.filter(function (v) { return v && v.bvid; }).map(function (v) {
            return {
                vod_id: v.bvid,
                vod_name: String(v.title || '').replace(/<[^>]+>/g, ''),
                vod_pic: v.pic ? (String(v.pic).indexOf('//') === 0 ? 'https:' + v.pic : v.pic) : '',
                vod_remarks: v.duration || '',
                vod_content: v.description || ''
            };
        });
    },

    二级: function (ids) {
        var bvid = Array.isArray(ids) ? ids[0] : ids;
        var api = 'https://api.bilibili.com/x/web-interface/view?bvid=' + encodeURIComponent(bvid);
        var data = {};
        try { data = JSON.parse(request(api, { headers: rule.headers })); } catch (e) {}
        var v = data && data.data || {};
        VOD = {
            vod_id: bvid,
            vod_name: v.title || bvid,
            vod_pic: v.pic || '',
            vod_actor: v.owner && v.owner.name || '',
            vod_content: v.desc || '公开页面信息',
            vod_play_from: '官方页面',
            vod_play_url: '打开官方页面$https://www.bilibili.com/video/' + bvid
        };
    },

    搜索: function (wd, quick, pg) {
        var api = 'https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword='
            + encodeURIComponent(wd) + '&page=' + (pg || 1);
        var data = {};
        try { data = JSON.parse(request(api, { headers: rule.headers })); } catch (e) { return []; }
        var rows = data && data.data && data.data.result || [];
        return rows.filter(function (v) { return v && v.bvid; }).map(function (v) {
            return {
                vod_id: v.bvid,
                vod_name: String(v.title || '').replace(/<[^>]+>/g, ''),
                vod_pic: v.pic ? (String(v.pic).indexOf('//') === 0 ? 'https:' + v.pic : v.pic) : '',
                vod_remarks: v.duration || '',
                vod_content: v.description || ''
            };
        });
    },

    play: function (flag, id, flags) {
        return { parse: 1, url: id, jx: 0 };
    }
};
