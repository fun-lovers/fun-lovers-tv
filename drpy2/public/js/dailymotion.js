var rule = {
 title:'Dailymotion',host:'https://www.dailymotion.com',homeUrl:'https://www.dailymotion.com',
 searchable:1,quickSearch:1,filterable:0,headers:{'User-Agent':'Mozilla/5.0'},
 class_name:'视频',class_url:'视频',
 一级:function(tid,pg){return dmSearch(tid||'popular',pg);},
 搜索:function(wd,quick,pg){return dmSearch(wd,pg);},
 二级:function(ids){var id=Array.isArray(ids)?ids[0]:ids;VOD={vod_id:id,vod_name:id,vod_play_from:'Dailymotion官方页面',vod_play_url:'打开视频$https://www.dailymotion.com/video/'+id};},
 play:function(flag,id){return {parse:1,url:id,jx:0};}
};
function dmSearch(wd,pg){var u='https://api.dailymotion.com/videos?search='+encodeURIComponent(wd)+'&limit=20&page='+(pg||1)+'&fields=id,title,description,thumbnail_360_url,duration,owner.screenname,url';var d={};try{d=JSON.parse(request(u,{headers:rule.headers}));}catch(e){return [];}return (d.list||[]).map(function(v){return {vod_id:v.id,vod_name:v.title||v.id,vod_pic:v.thumbnail_360_url||'',vod_remarks:v.duration?String(v.duration)+'s':'',vod_content:v.description||''};});}
