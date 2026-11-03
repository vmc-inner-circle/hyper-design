"""결과물의 부품 구성 측정 — 화면당 부품 종류 수, v19 새 부품(* 표시)·시트·promos 사용, 블록·목록 행·큰 머리글·하단 고정 버튼 비율.
python3 loop/parts.py <이름> <결과 폴더> [<이름> <결과 폴더> …]
"""
import re,glob,sys,collections,json,os
PART={'appbar':'앱바','hero':'큰 머리글','block':'블록','row':'목록 행','badge':'배지','chips':'칩','seg':'세그먼트','btn':'버튼','cta':'하단 고정 버튼','tabbar':'탭바','sheet':'시트','search':'검색','switch':'스위치','check':'체크','field':'입력','progress':'진행 막대','rating':'별점','range':'범위','timeline':'타임라인','photo':'사진','thumb':'썸네일','photo-grid':'사진 모음','compare':'전후 비교','avatar':'아바타','info':'안내 한 줄','done':'완료 표시','empty':'빈 상태','accent-text':'강조 글자',
 'tabs':'상단 탭*','toolbar':'정렬·필터 바*','menu-grid':'아이콘 격자*','scroller':'가로 스크롤*','s-circle':'동그란 썸네일*','product-grid':'카드 격자*','price':'가격*','like':'찜*','fab':'FAB*','banner':'배너*','strip':'띠 배너*','coupon':'쿠폰*','countdown':'남은 시간*'}
def scan(d):
    m=json.load(open(d+'/screens.json')); res={}
    for s in m['screens']:
        f=os.path.join(d,s['file']) if os.path.exists(os.path.join(d,s['file'])) else os.path.join(d,'screens',os.path.basename(s['file']))
        if not os.path.exists(f): continue
        cl={c for v in re.findall(r'class="([^"]*)"',open(f).read()) for c in v.split()}
        res[s['id']]={PART[k] for k in PART if k in cl}
    return res,m
rows=[]
for name,d in [(a,b) for a,b in zip(sys.argv[1::2],sys.argv[2::2])]:
    r,m=scan(d); n=len(r); c=collections.Counter(p for v in r.values() for p in v)
    new=sorted([k for k in c if k.endswith('*')],key=lambda k:-c[k])
    print(f"{name}: 화면 {n} · 화면당 부품 종류 {sum(map(len,r.values()))/n:.1f} · 앱 전체 종류 {len(c)} · 시트 {sum(1 for s in m['screens'] if s.get('kind')=='sheet')} · promos {len(m.get('promos') or [])}")
    print("   새 부품:", ", ".join(f"{k}{c[k]}" for k in new) or "없음")
    print("   카드 블록·목록 행·큰 제목 비율:", ", ".join(f"{k} {100*c[k]/n:.0f}%" for k in ['블록','목록 행','큰 머리글','하단 고정 버튼']))
