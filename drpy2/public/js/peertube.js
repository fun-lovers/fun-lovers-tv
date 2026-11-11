var rule = {
 title:'PeerTube 联邦视频', host:'https://peertube.cpy.re', homeUrl:'https://peertube.cpy.re',
 searchable:1, quickSearch:1, filterable:0, headers:{'User-Agent':'Mozilla/5.0'},
 class_name:'联邦视频',class_url:'联邦视频',
 一级:function(tid,pg){return ptSearch(tid||'popular',pg);},
 搜索:function(wd,quick,pg){return ptSearch(wd,pg);},
 二级:function(ids){var id=Array.isArray(ids)?ids[0]:ids;var d={};try{d=JSON.parse(request(rule.host+'/api/v1/videos/'+encodeURIComponent(id)));}catch(e){};var v=d||{};VOD={vod_id:id,vod_name:v.name||id,vod_pic:v.thumbnailPath?rule.host+v.thumbnailPath:'',vod_actor:v.account&&v.account.displayName||'',vod_content:v.description||'',vod_play_from:'PeerTube官方页面',vod_play_url:'打开视频$'+(v.url||rule.host+'/videos/watch/'+id)};},
 play:function(flag,id){return {parse:1,url:id,jx:0};}
};
function ptSearch(wd,pg){var u=rule.host+'/api/v1/search/videos?search='+encodeURIComponent(wd)+'&start='+(((parseInt(pg,10)||1)-1)*20)+'&count=20&sort=-publishedAt';var d={};try{d=JSON.parse(request(u,{headers:rule.headers}));}catch(e){return [];}return (d.data||[]).map(function(v){return {vod_id:String(v.id),vod_name:v.name||'',vod_pic:v.thumbnailPath?rule.host+v.thumbnailPath:'',vod_remarks:v.duration||'',vod_content:v.description||''};});}
