import json,sys
ids=sys.argv[1].split(",")
m=json.load(open("out/screens.json"));inv=json.load(open("out/spec_inventory.json"))
base={i.split("--")[0] for i in ids}
for s in m["screens"]:
    if s["id"] in ids: print("SCREEN",json.dumps(s,ensure_ascii=False))
for it in inv["items"]:
    cov=set(it.get("covered_by") or [])|{it.get("target"),it.get("policy")}
    if cov & base: print("SPEC",it["id"],it["kind"],it["name"],"|",it["quote"],"|",it.get("target",""),it.get("state",""),("policy:"+it["policy"]) if it.get("policy") else "")
