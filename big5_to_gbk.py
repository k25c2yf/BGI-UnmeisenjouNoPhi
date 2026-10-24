# -*- coding: utf-8 -*-
# 繁體中文轉簡體中文 (big5 TC txt -> gbk SC txt)
# 用法：在專案根目錄執行  python 繁體中文轉簡體中文.py
# 讀 ./big5/*.txt，寫 ./gbk/（同檔名，UTF-8，保留各檔 BOM 有無與換行方式）
# 依賴：opencc-python-reimplemented
#
# 1. 有 ./sc_override/<同檔名> 時直接原樣複製（Custom、SetupForEtc 的人工校訂簡中）
# 2. 只轉換 ●ID● 之後的文字；ID、<...> 標籤、__ 控制碼行、jp/jpname 中列出的說話人行一律不動
# 3. opencc t2s 後再套用補正表（著→着 依語境、妳→你、想像→想象…）
# [φ版修改 20261024]
#  a. 路徑以本檔所在資料夾為準（可在任何 cwd 執行）
#  b. jp/jpname/<base>.txt 由 make_jpname.py 依 bytecode 產生：0x140 說話人參數 + 0x15a 第1參數（系統名）
#  c. jp/display/<base>.txt 列出 0x15a 第2參數（名牌顯示名）ID，強制轉換、絕不當說話人行保留
#  e. SPEAKER_CONVERT：說話人行（jpname 保留行）全文等於鍵時才轉換（伊織 無 0x15a 顯示名，名牌直接顯示說話人字串）
#  d. FIX 表追加 φ 專用補正（言霊→言灵、魟、鮟鱇、著→着 誤保留、暱伕菓）
import os, re, sys, shutil
import opencc

_HERE = os.path.dirname(os.path.abspath(__file__))
SRC, DST, OVR, JPN = [os.path.join(_HERE, x) for x in ('big5', 'gbk', 'sc_override', os.path.join('jp', 'jpname'))]
DSP = os.path.join(_HERE, 'jp', 'display')  # [φ] 0x15a 第2參數 ID（必轉）
cc = opencc.OpenCC('t2s')

# 「著」保留的詞（著作義）；其餘一律改「着」
KEEP_ZHU = ['著名', '著作', '著者', '著称', '著述', '著录', '显著', '名著', '原著', '拙著',
            '论著', '专著', '巨著', '编著', '昭著', '卓著', '土著', '遗著', '新著', '译著']
FIX = [('妳', '你'), ('想像', '想象'), ('瞇', '眯'), ('搆', '够'), ('摀', '捂'), ('睪', '睾'),
       ('痺', '痹'), ('砲', '炮'), ('悪', '恶'), ('艶', '艳'), ('簷', '檐'), ('撢', '掸'), ('牠', '它'),
       # [φ] 追加補正
       ('霊', '灵'),                                   # 言霊→言灵（含「言、霊……」、斩之言霊）
       ('𫚉', '魟'), ('𩽾𩾌', '安康'),                  # OpenCC 產生罕用擴展字：魟魚、鮟鱇魚肝
       ('讨论著', '讨论着'), ('带著名', '带着名'),       # 「论著」「著名」「著称」誤判為著作義
       ('写著名', '写着名'), ('笑著称', '笑着称'),
       ('暱', '昵'), ('伕', '夫'), ('和菓子', '和果子')]
TAG = re.compile(r'(<[^>]*>)')
# [φ] 只對「全文完全相等」的保留行轉換；其他說話人行與 0x15a 第1參數一律不動
SPEAKER_CONVERT = {'伊織': '伊织'}

def fix_zhu(s):
    s = s.replace('彰显著', '彰显着')
    keep = {}
    for i, w in enumerate(KEEP_ZHU):
        if w in s:
            k = '\uE000%d\uE001' % i; keep[k] = w; s = s.replace(w, k)
    s = s.replace('著', '着')
    for k, w in keep.items(): s = s.replace(k, w)
    return s

def conv_text(t):
    out = []
    for part in TAG.split(t):
        if not part or TAG.fullmatch(part):
            out.append(part); continue
        p = cc.convert(part)
        for a, b in FIX: p = p.replace(a, b)
        out.append(fix_zhu(p))
    return ''.join(out)

def speaker_ids(fn):
    base = fn[:-7] if fn.endswith('_tc.txt') else fn[:-4]
    p = os.path.join(JPN, base + '.txt'); ids = set()
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8-sig') as f:
            for l in f:
                if l.startswith('●') and len(l) > 8: ids.add(l[1:7])
    q = os.path.join(DSP, base + '.txt')  # [φ] 名牌顯示名一律轉換
    if os.path.exists(q):
        with open(q, 'r', encoding='utf-8-sig') as f:
            for l in f:
                if l.startswith('●') and len(l) > 8: ids.discard(l[1:7])
    return ids

def main():
    if not os.path.isdir(SRC):
        print('找不到 ' + SRC); sys.exit(1)
    os.makedirs(DST, exist_ok=True)
    nfile = nover = nline = nskip = nspk = 0
    for fn in sorted(os.listdir(SRC)):
        if not fn.endswith('.txt'): continue
        nfile += 1
        if os.path.exists(os.path.join(OVR, fn)):
            shutil.copyfile(os.path.join(OVR, fn), os.path.join(DST, fn)); nover += 1
            print('[override] ' + fn); continue
        raw = open(os.path.join(SRC, fn), 'rb').read()
        bom = raw.startswith(b'\xef\xbb\xbf')
        text = raw.decode('utf-8-sig')
        sp = speaker_ids(fn)
        lines = text.splitlines(True)  # 保留原換行
        res = []
        for l in lines:
            body = l.rstrip('\r\n'); eol = l[len(body):]
            if body.startswith('●') and len(body) >= 8 and body[7] == '●':
                i, t = body[1:7], body[8:]
                if i in sp and t in SPEAKER_CONVERT:  # [φ]
                    nspk += 1; res.append(body[:8] + SPEAKER_CONVERT[t] + eol); continue
                if i in sp or t.startswith('__'):
                    nskip += 1; res.append(l); continue
                nt = conv_text(t)
                if nt != t: nline += 1
                res.append(body[:8] + nt + eol)
            else:
                res.append(l)
        data = ''.join(res).encode('utf-8')
        if bom: data = b'\xef\xbb\xbf' + data
        open(os.path.join(DST, fn), 'wb').write(data)
    print('完成：%d 檔（override %d），轉換 %d 行，保留說話人／控制行 %d 行' % (nfile, nover, nline, nskip))
    print('[φ] 說話人名轉換 %d 行（%s）' % (nspk, '、'.join('%s→%s' % kv for kv in SPEAKER_CONVERT.items())))
    cnt = {}
    for fn in os.listdir(DST):
        if fn.endswith('.txt'):
            t = open(os.path.join(DST, fn), encoding='utf-8-sig').read()
            for ch in ('著', '妳'): cnt[ch] = cnt.get(ch, 0) + t.count(ch)
    print('剩餘：著 %d（著作義保留），妳 %d' % (cnt.get('著', 0), cnt.get('妳', 0)))

if __name__ == '__main__':
    main()
