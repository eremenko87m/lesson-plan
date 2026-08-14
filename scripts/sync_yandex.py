#!/usr/bin/env python3
"""LessonFlow Yandex synchronizer.
Reads ONLY the PLAN sheet. GROUPS and MY BASE are ignored.
Uses private Yandex Disk API when YANDEX_TOKEN + YANDEX_FILE_PATH are present;
otherwise falls back to the public workbook link for testing.
Standard library only.
"""
from __future__ import annotations
import os, io, re, json, hashlib, zipfile, urllib.request, urllib.parse, datetime, posixpath, mimetypes
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'lessons.json'; GEN=ROOT/'assets'/'generated'
DEFAULT_PUBLIC_URL='https://disk.yandex.ru/i/8Hx5gthiZ0-IJQ'
PUBLIC_URL=(os.getenv('YANDEX_PUBLIC_URL') or DEFAULT_PUBLIC_URL).strip()
TOKEN=(os.getenv('YANDEX_TOKEN') or '').strip()
FILE_PATH=(os.getenv('YANDEX_FILE_PATH') or '').strip()
PLAN_SHEET='PLAN'
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships','xdr':'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing','a':'http://schemas.openxmlformats.org/drawingml/2006/main','rel':'http://schemas.openxmlformats.org/package/2006/relationships'}
DATE_IDS={14,15,16,17,18,19,20,21,22,27,28,29,30,31,32,33,34,35,36,45,46,47,50,51,52,53,54,55,56,57,58}

def req_json(url, headers=None):
    r=urllib.request.Request(url,headers=headers or {'User-Agent':'LessonFlow/1.0'})
    with urllib.request.urlopen(r,timeout=45) as x:return json.loads(x.read().decode('utf-8'))
def req_bytes(url, headers=None, max_bytes=120_000_000):
    r=urllib.request.Request(url,headers=headers or {'User-Agent':'LessonFlow/1.0'})
    with urllib.request.urlopen(r,timeout=90) as x:
        data=x.read(max_bytes+1); ctype=x.headers.get('Content-Type','')
    if len(data)>max_bytes: raise RuntimeError('Downloaded file is too large')
    return data,ctype

def normalize_disk_path(p):
    p=p.strip()
    if p.startswith('disk:/'):return p
    if p.startswith('/') :return 'disk:'+p
    return 'disk:/'+p

def private_download_href(path):
    q=urllib.parse.urlencode({'path':normalize_disk_path(path)})
    return req_json('https://cloud-api.yandex.net/v1/disk/resources/download?'+q,{'Authorization':'OAuth '+TOKEN,'User-Agent':'LessonFlow/1.0'})['href']
def public_download_href(url):
    q=urllib.parse.urlencode({'public_key':url})
    return req_json('https://cloud-api.yandex.net/v1/disk/public/resources/download?'+q)['href']
def get_workbook():
    if TOKEN and FILE_PATH:
        href=private_download_href(FILE_PATH); mode='private-api'
    elif PUBLIC_URL:
        href=public_download_href(PUBLIC_URL); mode='public-link'
    else: raise RuntimeError('Configure YANDEX_TOKEN + YANDEX_FILE_PATH, or YANDEX_PUBLIC_URL')
    b,_=req_bytes(href); return b,mode

def colnum(ref):
    m=re.match(r'([A-Z]+)',ref.upper()); n=0
    for ch in m.group(1):n=n*26+ord(ch)-64
    return n

def shared_strings(z):
    if 'xl/sharedStrings.xml' not in z.namelist():return []
    root=ET.fromstring(z.read('xl/sharedStrings.xml')); out=[]
    for si in root.findall('m:si',NS):out.append(''.join((t.text or '') for t in si.iter('{%s}t'%NS['m'])))
    return out

def styles(z):
    if 'xl/styles.xml' not in z.namelist():return [],{}
    root=ET.fromstring(z.read('xl/styles.xml')); custom={}
    nf=root.find('m:numFmts',NS)
    if nf is not None:
        for x in nf.findall('m:numFmt',NS):custom[int(x.attrib.get('numFmtId','0'))]=x.attrib.get('formatCode','')
    xfs=root.find('m:cellXfs',NS); ids=[]
    if xfs is not None:
        ids=[int(x.attrib.get('numFmtId','0')) for x in xfs.findall('m:xf',NS)]
    return ids,custom

def is_date_style(style_idx,style_ids,custom):
    if style_idx is None or style_idx>=len(style_ids):return False
    n=style_ids[style_idx]
    if n in DATE_IDS:return True
    f=custom.get(n,'').lower(); f=re.sub(r'"[^"]*"','',f)
    return bool(re.search(r'[dmyhs]',f))
def excel_date(v):
    try:
        x=float(v)
        dt=datetime.datetime(1899,12,30)+datetime.timedelta(days=x)
        # Excel/Yandex stores a time-only cell as a fraction of one day.
        # 0.5 = 12:00, 0.75 = 18:00, etc.
        if 0 <= x < 1:
            return dt.strftime('%H:%M')
        return dt.date().isoformat()
    except:
        return str(v)

def rels(z,path):
    if path not in z.namelist():return {}
    r=ET.fromstring(z.read(path)); return {x.attrib['Id']:x.attrib.get('Target','') for x in r.findall('rel:Relationship',NS)}
def workbook_sheet_path(z,name):
    w=ET.fromstring(z.read('xl/workbook.xml')); rs=rels(z,'xl/_rels/workbook.xml.rels')
    for s in w.findall('m:sheets/m:sheet',NS):
        if s.attrib.get('name')==name:
            t=rs.get(s.attrib.get('{%s}id'%NS['r']));
            if not t:break
            return posixpath.normpath(posixpath.join('xl',t))
    raise RuntimeError(f'Sheet {name!r} not found. Rename the first working sheet to PLAN.')
def sheet_rels_path(sheet_path):return posixpath.join(posixpath.dirname(sheet_path),'_rels',posixpath.basename(sheet_path)+'.rels')
def parse_plan(z,sheet_path):
    ss=shared_strings(z); style_ids,custom=styles(z); root=ET.fromstring(z.read(sheet_path)); sr=rels(z,sheet_rels_path(sheet_path))
    hyper={}
    hp=root.find('m:hyperlinks',NS)
    if hp is not None:
        for h in hp.findall('m:hyperlink',NS):
            ref=h.attrib.get('ref',''); rid=h.attrib.get('{%s}id'%NS['r']);
            if rid and rid in sr:hyper[ref]=sr[rid]
    rows={}
    sd=root.find('m:sheetData',NS)
    if sd is None:return [],{},root,sr
    for row in sd.findall('m:row',NS):
        rn=int(row.attrib.get('r','0')); cells={}
        for c in row.findall('m:c',NS):
            ref=c.attrib.get('r',''); typ=c.attrib.get('t',''); st=c.attrib.get('s'); st=int(st) if st is not None else None
            val=''
            if ref in hyper:val=hyper[ref]
            elif typ=='inlineStr':val=''.join((t.text or '') for t in c.iter('{%s}t'%NS['m']))
            else:
                v=c.find('m:v',NS); raw=v.text if v is not None and v.text is not None else ''
                if typ=='s' and raw!='':
                    try:val=ss[int(raw)]
                    except:val=raw
                elif typ in ('str','e'):val=raw
                elif raw!='' and is_date_style(st,style_ids,custom):val=excel_date(raw)
                else:val=raw
            cells[colnum(ref)]=val
        rows[rn]=cells
    hdr=rows.get(1,{})
    headers={str(v).strip().upper():c for c,v in hdr.items() if str(v).strip()}
    out=[]
    for rn in sorted(k for k in rows if k>1):
        obj={'__row':rn}
        for h,c in headers.items():obj[h]=rows[rn].get(c,'')
        if any(str(v).strip() for k,v in obj.items() if k!='__row'):out.append(obj)
    return out,headers,root,sr

def extract_images(z,sheet_path,sheet_root,sheet_rels,headers):
    wanted={headers.get('IMAGE_1'):0,headers.get('IMAGE_2'):1}; wanted={k:v for k,v in wanted.items() if k}
    dr=sheet_root.find('m:drawing',NS)
    if dr is None or not wanted:return {},False
    rid=dr.attrib.get('{%s}id'%NS['r']); target=sheet_rels.get(rid)
    if not target:return {},False
    dp=posixpath.normpath(posixpath.join(posixpath.dirname(sheet_path),target))
    if dp not in z.namelist():return {},False
    droot=ET.fromstring(z.read(dp)); drp=posixpath.join(posixpath.dirname(dp),'_rels',posixpath.basename(dp)+'.rels'); drel=rels(z,drp)
    byrow={}
    for tag in ('twoCellAnchor','oneCellAnchor'):
        for a in droot.findall('xdr:'+tag,NS):
            fr=a.find('xdr:from',NS); pic=a.find('xdr:pic',NS)
            if fr is None or pic is None:continue
            col=int(fr.findtext('xdr:col','-1',NS))+1; row=int(fr.findtext('xdr:row','-1',NS))+1
            if col not in wanted or row<2:continue
            blip=pic.find('xdr:blipFill/a:blip',NS); erid=blip.attrib.get('{%s}embed'%NS['r']) if blip is not None else None; t=drel.get(erid)
            if not t:continue
            media=posixpath.normpath(posixpath.join(posixpath.dirname(dp),t));
            if media not in z.namelist():continue
            ext=Path(media).suffix or '.png'; fn=f'row{row}_image{wanted[col]+1}{ext.lower()}'; (GEN/fn).write_bytes(z.read(media))
            byrow.setdefault(row,[None,None])[wanted[col]]=f'assets/generated/{fn}'
    rich=any(n.startswith('xl/richData/') or n.endswith('cellimages.xml') for n in z.namelist())
    return {r:[x for x in v if x] for r,v in byrow.items()},rich

def clean(v):return str(v or '').strip()
def number(v,default=0):
    try:return int(float(str(v).replace(',','.')))
    except:return default
def date_norm(v):
    s=clean(v)
    if not s:return ''
    if re.match(r'^\d{4}-\d{2}-\d{2}$',s):return s
    m=re.match(r'^(\d{1,2})[./](\d{1,2})[./](\d{4})$',s)
    if m:return f'{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}'
    return s
def time_norm(v):
    s=clean(v)
    if re.match(r'^\d{1,2}:\d{2}',s):
        h,m=s.split(':')[:2];return f'{int(h):02d}:{int(m):02d}'
    try:
        x=float(s); mins=round((x%1)*1440);return f'{mins//60%24:02d}:{mins%60:02d}'
    except:return s

def safe_slug(s):
    s=re.sub(r'[^a-zA-Z0-9а-яА-Я_-]+','-',s).strip('-').lower();return s[:50] or 'lesson'
def audio_download(value,label,lesson_id,order):
    u=clean(value)
    if not u:return None
    try:
        if u.startswith(('disk:/','/')) and TOKEN:
            href=private_download_href(u)
        elif re.search(r'(disk\.yandex|yadi\.sk|ya\.cc)',u,re.I):href=public_download_href(u)
        elif re.match(r'^https?://',u,re.I):href=u
        else:return {'src':u,'label':label or 'Audio'}
        b,ctype=req_bytes(href,max_bytes=80_000_000)
        ext=mimetypes.guess_extension((ctype.split(';')[0] if ctype else '')) or Path(urllib.parse.urlparse(href).path).suffix or '.mp3'
        if ext=='.jpe':ext='.jpg'
        if ext not in ('.mp3','.m4a','.mp4','.ogg','.wav','.aac','.webm'): ext='.mp3'
        fn=f'{safe_slug(lesson_id)}_{order:02d}_audio{ext}';(GEN/fn).write_bytes(b);return {'src':f'assets/generated/{fn}','label':label or 'Audio'}
    except Exception as e:
        print(f'WARNING audio {lesson_id}/{order}: {e}');return {'src':u,'label':label or 'Audio'}

def build(rows,images):
    required={'DATE','TIME','STUDENT','LEVEL','TOPIC','FOCUS','LESSON_MIN','ACTIVITY','MIN','LINK','IMAGE_1','IMAGE_2','AUDIO','AUDIO_LABEL','NOTE'}
    # Missing optional columns are tolerated except core fields.
    lessons=[]; cur=None; last_date=''; used={}
    palette=['violet','cyan','lime','orange','rose','blue']
    for r in rows:
        row_date=date_norm(r.get('DATE')) or last_date
        starts=bool(clean(r.get('TIME')) or clean(r.get('STUDENT')))
        if starts:
            if not row_date:raise RuntimeError(f'PLAN row {r["__row"]}: DATE is required for the first lesson of a day')
            last_date=row_date
            t=time_norm(r.get('TIME')); student=clean(r.get('STUDENT')) or 'Student'; base=f'{row_date}-{t.replace(":","")}-{safe_slug(student)}'; used[base]=used.get(base,0)+1; lid=base if used[base]==1 else f'{base}-{used[base]}'
            cur={'id':lid,'date':row_date,'time':t,'student':student,'level':clean(r.get('LEVEL')),'topic':clean(r.get('TOPIC')) or 'Lesson','focus':clean(r.get('FOCUS')),'duration':number(r.get('LESSON_MIN'),0),'accent':palette[len(lessons)%len(palette)],'activities':[]};lessons.append(cur)
        if cur is None:continue
        title=clean(r.get('ACTIVITY'))
        if title:
            order=len(cur['activities'])+1; imgs=list(images.get(r['__row'],[]))
            for k in ('IMAGE_1','IMAGE_2'):
                u=clean(r.get(k));
                if re.match(r'^https?://',u,re.I) and u not in imgs:imgs.append(u)
            link=clean(r.get('LINK')); audio=audio_download(r.get('AUDIO'),clean(r.get('AUDIO_LABEL')),cur['id'],order)
            cur['activities'].append({'order':order,'title':title,'minutes':number(r.get('MIN'),0),'url':link,'note':clean(r.get('NOTE')),'images':imgs,'audio':audio})
    for l in lessons:
        if not l['duration']:l['duration']=sum(a['minutes'] for a in l['activities'])
    return lessons

def main():
    wb,mode=get_workbook(); fp=hashlib.sha256(wb).hexdigest()
    if DATA.exists():
        try:
            old=json.loads(DATA.read_text('utf-8'))
            if old.get('sourceFingerprint')==fp:
                print('Workbook unchanged — nothing to update.');return
        except:pass
    GEN.mkdir(parents=True,exist_ok=True)
    for p in GEN.iterdir():
        if p.is_file():p.unlink()
    with zipfile.ZipFile(io.BytesIO(wb)) as z:
        sp=workbook_sheet_path(z,PLAN_SHEET); rows,headers,sroot,srels=parse_plan(z,sp)
        core={'TIME','STUDENT','ACTIVITY'}
        missing=core-set(headers)
        if missing:raise RuntimeError('PLAN is missing required columns: '+', '.join(sorted(missing)))
        images,rich=extract_images(z,sp,sroot,srels,headers)
        if rich and not images:print('WARNING: in-cell RichData images detected. For guaranteed extraction use Ctrl+V and place the image OVER IMAGE_1 / IMAGE_2.')
        lessons=build(rows,images)
    payload={'updatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceMode':mode,'sourceSheet':'PLAN','sourceFingerprint':fp,'lessons':lessons}
    DATA.write_text(json.dumps(payload,ensure_ascii=False,indent=2),'utf-8')
    print(f'Synced {len(lessons)} lessons from PLAN; extracted {sum(len(v) for v in images.values())} image(s). GROUPS and MY BASE were ignored.')
if __name__=='__main__':main()
