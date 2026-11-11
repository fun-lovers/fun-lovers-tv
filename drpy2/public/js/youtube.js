var rule = {
 title:'YouTube', host:'https://www.youtube.com', homeUrl:'https://www.youtube.com',
 searchable:1, quickSearch:1, filterable:0,
 headers:{'User-Agent':'Mozilla/5.0'},
 key:'', // 在此填写 YouTube Data API v3 Key；不要提交真实密钥到公开仓库
 class_name:'视频', class_url:'视频',
 一级:function(tid,pg){ return ytSearch(tid || 'trending',pg); },
 搜索:function(wd,quick,pg){ return ytSearch(wd,pg); },
 二级:function(ids){ var id=Array.isArray(ids)?ids[0]:ids; VOD={vod_id:id,vod_name:id,vod_play_from:'YouTube官方页面',vod_play_url:'打开视频$https://www.youtube.com/watch?v='+id}; },
 play:function(flag,id){return {parse:1,url:id,jx:0};}
};
function ytSearch(wd,pg){
 if(!rule.key) return [];
 var u='https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults=20&pageToken=&q='+encodeURIComponent(wd)+'&key='+encodeURIComponent(rule.key);
 var d={}; try{d=JSON.parse(request(u,{headers:rule.headers}));}catch(e){return [];}
 return (d.items||[]).map(function(x){var s=x.snippet||{},id=x.id&&x.id.videoId;return id?{vod_id:id,vod_name:s.title||id,vod_pic:s.thumbnails&&s.thumbnails.medium&&s.thumbnails.medium.url||'',vod_content:s.description||'',vod_remarks:s.channelTitle||''}:null;}).filter(Boolean);
}
