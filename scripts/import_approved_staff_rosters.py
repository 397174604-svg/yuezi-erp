#!/usr/bin/env python3
"""Import approved roster master data without importing sensitive identity fields."""
from __future__ import annotations
import json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
import pymysql

CONFIRM = "ROSTER_FROM_APPROVED_PDF"
SOURCE = "APPROVED_STAFF_ROSTER_20260801"
TENANT_ID = 1

ROSTERS = {
 "建设路店（中心店）": {"store_id": 1, "departments": {
  "总经办": [("张帅","总经理"),("李慧娟","人事主管"),("段瑞雪","财务专员"),("王文洁","企划专员")],
  "销售部": [(n,"销售顾问") for n in ("关丽荣","孔晓燕","苏利珍","张兆宇")],
  "护理部": [("张玉洁","护理主任"),("桑旭","护理组长")]+[(n,"护理人员") for n in ("杨浩然","刘素平","胜欣欣","赵闪闪","乔盼盼","杨爱引","王亚潇","王素芳","李文文","田雪丽","曹甜甜","魏云茹","梁梦真","王丽姣","马胜男","孙晓静","寇丽鸽")],
  "产康部": [("贾慧丽","产康经理")]+[(n,"产康师") for n in ("赵贞贞","张春霞","刘娅芳","刘荣艳")],
  "膳食部": [(n,"膳食员工") for n in ("郑世杰","王天雨","武正围","张坤","孙会敏","魏叔萍","闫梅芳","李爱民")],
  "客房部": [("李艳玲","客房管家")]+[(n,"客房服务") for n in ("朱翠敏","赵利佩","韩拥贞","杨森","马素君")],
 }},
 "黄河路店": {"store_id": 2, "departments": {
  "销售部": [(n,"销售顾问") for n in ("韩新","李攀","王璇","李倩")],
  "护理部": [(n,"护理人员") for n in ("张艳丽","姚赛玉","孙晓慧","段圣美","杨国慧","卢梦瑶","任叶","陈相朵","刘艳艳","陈杰","毕梦妍","杨霞","刘亚欣","卢琳颖","李瑞岩","储君婷","李慧节","谷雪珂","张心悦")],
  "产康部": [(n,"产康师") for n in ("于翠红","许曼曼","曹美玲","张会娟")],
  "膳食部": [(n,"膳食员工") for n in ("刘筱松","闫明明","闫书凯","娄素萍","赵兰姣","胡彦红","赵兰竹")],
  "客房部": [("董丽霞","客房管家")]+[(n,"客房服务") for n in ("郭敬敏","曹淑红","沈艳甫","王小彦","杨梅","王淑芝")],
 }},
}
ROLE = {"总经理":"总经理","人事主管":"人事主管","财务专员":"财务专员","企划专员":"企划专员","销售顾问":"销售顾问","护理主任":"护理主任","护理组长":"护理人员","护理人员":"护理人员","产康经理":"产康经理","产康师":"产康师","膳食员工":"膳食员工","客房管家":"客房管家","客房服务":"客房管家"}
def code(v): return "".join(ch for ch in v.upper() if ch.isalnum())[:48] or "DEFAULT"
def main():
 if os.environ.get("ERP_STAFF_ROSTER_CONFIRM") != CONFIRM: raise SystemExit("Set ERP_STAFF_ROSTER_CONFIRM=ROSTER_FROM_APPROVED_PDF before import.")
 if os.environ.get("ERP_DB_HOST","127.0.0.1") not in {"127.0.0.1","localhost","::1"}: raise SystemExit("Roster import is restricted to a loopback database.")
 db=pymysql.connect(host=os.environ.get("ERP_DB_HOST","127.0.0.1"),port=int(os.environ.get("ERP_DB_PORT","3306")),user=os.environ["ERP_DB_USER"],password=os.environ["ERP_DB_PASSWORD"],database=os.environ.get("ERP_DB_NAME","yuezi"),charset="utf8mb4",autocommit=False)
 out={"created":0,"updated":0,"departments":0,"positions":0,"stores":{}}
 try:
  with db.cursor() as c:
   for store_name,roster in ROSTERS.items():
    store_id=roster["store_id"]; c.execute("SELECT 1 FROM stores WHERE tenant_id=%s AND store_id=%s",(TENANT_ID,store_id))
    if not c.fetchone(): raise RuntimeError(f"Active store {store_id} missing")
    stats={"created":0,"updated":0}; sequence=0
    for dept,people in roster["departments"].items():
     c.execute("SELECT department_id FROM departments WHERE tenant_id=%s AND store_id=%s AND code=%s",(TENANT_ID,store_id,code(dept))); row=c.fetchone()
     if row: dept_id=int(row[0])
     else:
      c.execute("INSERT INTO departments(tenant_id,store_id,code,name,status,sort_order) VALUES(%s,%s,%s,%s,'ACTIVE',0)",(TENANT_ID,store_id,code(dept),dept)); dept_id=int(c.lastrowid); out["departments"]+=1
     for name,position in people:
      sequence+=1; pcode=code(position)
      c.execute("SELECT position_id FROM positions WHERE tenant_id=%s AND department_id=%s AND code=%s",(TENANT_ID,dept_id,pcode)); row=c.fetchone()
      if row: pos_id=int(row[0])
      else:
       c.execute("INSERT INTO positions(tenant_id,department_id,code,name,job_family,is_manager,status) VALUES(%s,%s,%s,%s,%s,%s,'ACTIVE')",(TENANT_ID,dept_id,pcode,position,dept,int(position.endswith("经理") or position.endswith("主任") or position.endswith("主管")))); pos_id=int(c.lastrowid); out["positions"]+=1
      c.execute("SELECT staff_id FROM staff WHERE tenant_id=%s AND store_id=%s AND name=%s ORDER BY staff_id LIMIT 2",(TENANT_ID,store_id,name)); found=c.fetchall()
      if len(found)>1: raise RuntimeError(f"Duplicate staff requires manual resolution: {store_name}/{name}")
      params=(dept_id,pos_id,f"ROSTER-{store_id}-{sequence:03d}",dept,position,ROLE[position],SOURCE,TENANT_ID,store_id,name)
      if found:
       c.execute("UPDATE staff SET department_id=%s,position_id=%s,employee_no=%s,department=%s,position=%s,role=%s,employment_status='ACTIVE',status='ACTIVE',source_file=%s,source_page=NULL,source_row=NULL,review_status='APPROVED',updated_at=NOW() WHERE tenant_id=%s AND store_id=%s AND name=%s",params); out["updated"]+=1; stats["updated"]+=1
      else:
       c.execute("INSERT INTO staff(tenant_id,store_id,employee_no,department_id,position_id,name,employment_status,role,position,department,status,source_file,review_status,created_at,updated_at) VALUES(%s,%s,%s,%s,%s,%s,'ACTIVE',%s,%s,%s,'ACTIVE',%s,'APPROVED',NOW(),NOW())",(TENANT_ID,store_id,f"ROSTER-{store_id}-{sequence:03d}",dept_id,pos_id,name,ROLE[position],position,dept,SOURCE)); out["created"]+=1; stats["created"]+=1
    out["stores"][store_name]=stats
  db.commit()
 except Exception:
  db.rollback(); raise
 finally: db.close()
 print(json.dumps({"status":"imported","source":SOURCE,**out},ensure_ascii=False,indent=2))
if __name__ == "__main__": main()
