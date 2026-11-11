var rule = {
    title: '哔哩哔哩 · 体育',
    host: 'https://www.bilibili.com',
    homeUrl: 'https://www.bilibili.com',
    searchable: 1,
    quickSearch: 1,
    filterable: 0,
    headers: {'User-Agent':'Mozilla/5.0','Referer':'https://www.bilibili.com/'},
    class_name: '体育',
    class_url: '体育',
    play_parse: true,
    一级: function (tid, pg) {
        var kw = (tid && tid !== '体育') ? tid : '体育';
        return biliSearch(kw, pg || 1);
    },
    二级: function (ids) {
        var bvid = Array.isArray(ids) ? ids[0] : ids;
        var d = {};
        try { d = JSON.parse(request('https://api.bilibili.com/x/web-interface/view?bvid=' + encodeURIComponent(bvid), {headers: rule.headers})); } catch(e) {}
        var v = d && d.data || {};
        VOD = {vod_id:bvid, vod_name:v.title || bvid, vod_pic:v.pic || '', vod_actor:v.owner && v.owner.name || '', vod_content:v.desc || 'Bilibili公开页面信息', vod_play_from:'官方网页', vod_play_url:'打开官方页面$https://www.bilibili.com/video/' + bvid};
    },
    搜索: function (wd, quick, pg) {
        return biliSearch('体育 ' + wd, pg || 1);
    },
    play: function (flag, id) { return {parse:1, url:id, jx:0}; }
};
function biliSearch(keyword, page) {
    var url = 'https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword=' + encodeURIComponent(keyword) + '&page=' + page;
    var d = {};
    try { d = JSON.parse(request(url, {headers:rule.headers})); } catch(e) { return []; }
    var rows = d && d.data && d.data.result || [];
    return rows.filter(function(x){return x && x.bvid;}).map(function(x){
        return {vod_id:x.bvid, vod_name:String(x.title || '').replace(/<[^>]+>/g,''), vod_pic:x.pic ? (String(x.pic).indexOf('//')===0 ? 'https:'+x.pic : x.pic) : '', vod_remarks:x.duration || '', vod_content:x.description || ''};
    });
}
