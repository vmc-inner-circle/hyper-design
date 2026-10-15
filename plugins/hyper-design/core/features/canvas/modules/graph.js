/* Model — 링크 그래프 하나. 화면(노드) + 연결(간선).
   kind:'flow' = screens.json branches(회색 갈래 화살표), kind:'link' = 화면 안 링크(hd-links 답, 색 링크).
   순수 함수만(DOM 없음). */
(function () {
'use strict';
var HD = globalThis.HD = globalThis.HD || {};

// D(캔버스 데이터) → {screens:[{id,title,row,group,file,state}], edges:[{from,to,kind:'flow',label}]}
function fromData(D) {
  D = D || {};
  var screens = [];
  (D.rows || []).forEach(function (row, ri) {
    (row.screens || []).forEach(function (s) {
      screens.push({id: s.id, title: s.title, row: ri, group: row.group, file: s.file, state: !!s.state});
    });
  });
  var edges = (D.arrows || []).map(function (a) { return {from: a.from, to: a.to, kind: 'flow', label: a.label || ''}; });
  return {screens: screens, edges: edges};
}

// hd-links 답(links:[{to,path,text,rect}])을 그 화면의 kind:'link' 간선으로 — 그 화면의 예전 link 간선은 바꿔 끼운다.
function addLinks(g, screenId, links) {
  var keep = (g.edges || []).filter(function (e) { return !(e.kind === 'link' && e.from === screenId); });
  var add = (links || []).map(function (l) {
    return {from: screenId, to: l.to, kind: 'link', label: l.text, via: {path: l.path, text: l.text, rect: l.rect}};
  });
  return {screens: g.screens, edges: keep.concat(add)};
}

// id 에서 나가는 간선(id 가 null 이면 전부), kind 로 거른다.
function edgesFrom(g, id, kind) {
  return (g.edges || []).filter(function (e) { return (id == null || e.from === id) && (!kind || e.kind === kind); });
}

// 같은 대상끼리 묶는다 → [{to, edges:[...], k}] (k = 처음 나온 순서)
function groupByTarget(edges) {
  var out = [], at = {};
  (edges || []).forEach(function (e) {
    if (!(e.to in at)) { at[e.to] = out.length; out.push({to: e.to, edges: [], k: out.length}); }
    out[at[e.to]].edges.push(e);
  });
  return out;
}

HD.graph = {fromData: fromData, addLinks: addLinks, edgesFrom: edgesFrom, groupByTarget: groupByTarget};
})();
