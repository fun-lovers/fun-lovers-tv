var rule = {
 title:'Vimeo',host:'https://vimeo.com',homeUrl:'https://vimeo.com',
 searchable:1,quickSearch:1,filterable:0,headers:{'User-Agent':'Mozilla/5.0'},
 token:'', // 填写 Vimeo public-scope access token；不要提交真实令牌
 class_name:'视频',class_url:'视频',
 一级:function(tid,pg){return vmSearch(tid||'staff picks',pg);},
 搜索:function(wd,quick,pg){return vmSearch(wd,pg);},
 二级:function(ids){var id=Array.isArray(ids)?ids[0]:ids;VOD={vod_id:id,vod_name:id,vod_play_from:'Vimeo官方页面',vod_play_url:'打开视频$https://vimeo.com/'+id};},
 play:function(flag,id){return {parse:1,url:id,jx:0};}
};
function vmSearch(wd,pg){if(!rule.token)return [];var u='https://api.vimeo.com/videos?query='+encodeURIComponent(wd)+'&per_page=20&page='+(pg||1);var d={};try{d=JSON.parse(request(u,{headers:{'Authorization':'bearer '+rule.token,'Accept':'application/vnd.vimeo.*+json;version=3.4'}}));}catch(e){return [];}return (d.data||[]).map(function(v){var pic=v.pictures&&v.pictures.sizes&&v.pictures.sizes.length?v.pictures.sizes[v.pictures.sizes.length-1].link:'';return {vod_id:String(v.uri||'').split('/').pop(),vod_name:v.name||'',vod_pic:pic,vod_content:v.description||'',vod_remarks:v.user&&v.user.name||''};});}
