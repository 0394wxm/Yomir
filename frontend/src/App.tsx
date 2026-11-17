import { useState } from 'react'
import './App.css'

const DISCLAIMER = 'AI 初稿，仅供参考，请以原文和专业判断为准。'

// udkanbun 的返り点合字（U+3191–U+319F）→ 通用写法
const KAERITEN_MAP: Record<string, string> = {
  '㆑': 'レ',
  '㆒': '一', '㆓': '二', '㆔': '三', '㆕': '四',
  '㆖': '上', '㆗': '中', '㆘': '下',
  '㆙': '甲', '㆚': '乙', '㆛': '丙', '㆜': '丁',
  '㆝': '天', '㆞': '地', '㆟': '人',
}
interface KaeritenChar { base: string; rt: string }

// 把 raw 返り点文本（含合字）解析成 [字, 返り点] 序列。合字紧跟在字后面，无歧义。
function parseKaeriten(line: string): KaeritenChar[] {
  const out: KaeritenChar[] = []
  let i = 0
  while (i < line.length) {
    const ch = line[i]
    if (KAERITEN_MAP[ch] !== undefined) {
      i += 1
      continue
    }
    let j = i + 1
    let rt = ''
    while (j < line.length && KAERITEN_MAP[line[j]] !== undefined) {
      rt += KAERITEN_MAP[line[j]]
      j += 1
    }
    out.push({ base: ch, rt })
    i = j
  }
  return out
}

function KaeritenLine({ line }: { line: string }) {
  const chars = parseKaeriten(line)
  return (
    <div className="vcol">
      {chars.map((c, idx) =>
        c.rt ? (
          <ruby key={idx}>{c.base}<rt>{c.rt}</rt></ruby>
        ) : (
          <ruby key={idx}>{c.base}<rt></rt></ruby>
        ),
      )}
    </div>
  )
}

function VerticalKaeriten({ raw }: { raw: string }) {
  const lines = raw.replace(/\r/g, '').split('\n').filter((l) => l.trim() !== '')
  return (
    <div className="vertical">
      {lines.map((l, i) => <KaeritenLine key={i} line={l} />)}
    </div>
  )
}

function VerticalPlain({ text }: { text: string }) {
  const lines = text.replace(/\r/g, '').split('\n').filter((l) => l.trim() !== '')
  return (
    <div className="vertical">
      {lines.map((l, i) => <div key={i} className="vcol">{l}</div>)}
    </div>
  )
}

interface KundokuResult {
  hakubun: string
  kaeriten_text: string
  kaeriten_text_raw?: string
  kakikudashi: string
  modern: string
  glossary: { word: string; reading?: string; meaning?: string }[]
  text_type?: string
  note?: string
  request_id?: number
  error?: string
}

interface OcrResult {
  hakubun: string
  status: string
  note?: string
  line_count?: number
}

interface HistoryItem {
  id: number
  hakubun: string
  created_at: string
  kaeriten_text?: string
  kakikudashi?: string
}

export default function App() {
  const [inputText, setInputText] = useState('')
  const [ocrNote, setOcrNote] = useState('')
  const [ocrBusy, setOcrBusy] = useState(false)
  const [ocrHakubun, setOcrHakubun] = useState('')       // OCR 原始白文（纠错基线）
  const [ocrImgUrl, setOcrImgUrl] = useState('')         // 原图预览
  const [hakubun, setHakubun] = useState('')
  const [result, setResult] = useState<KundokuResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [errMsg, setErrMsg] = useState('')
  // NIGHT7: 历史翻回
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([])
  const [historyOpen, setHistoryOpen] = useState(false)
  const [lastRequestId, setLastRequestId] = useState<number | null>(null)

  function sendToHakubun() {
    setErrMsg('')
    setHakubun(inputText.trim())
  }

  async function handleUpload(file: File) {
    setOcrBusy(true)
    setOcrNote('')
    setErrMsg('')
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await fetch('/api/ocr', { method: 'POST', body: fd })
      const data: OcrResult = await res.json()
      if (data.status === 'ok' && data.hakubun) {
        setHakubun(data.hakubun)
        setOcrHakubun(data.hakubun)                     // 纠错基线
        setOcrImgUrl(URL.createObjectURL(file))         // 行对照用原图
        setOcrNote(
          `OCR 完成（${data.line_count ?? '?'} 行）。白文已填入下方，可用「行別対照」逐行校改。${DISCLAIMER}`,
        )
      } else {
        setOcrNote(data.note || data.status)
      }
    } catch {
      setOcrNote('OCR 接口调用失败（后端未启动？）')
    } finally {
      setOcrBusy(false)
    }
  }

  async function runKundoku() {
    const text = hakubun.trim()
    if (!text) {
      setErrMsg('白文为空，请先粘贴漢文、上传图片或手动输入。')
      return
    }
    setBusy(true)
    setErrMsg('')
    try {
      const res = await fetch('/api/kundoku', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          ocr_hakubun: ocrHakubun,
          prev_request_id: lastRequestId,
        }),
      })
      const data = await res.json()
      if (!res.ok) {
        setResult(null)
        setErrMsg(typeof data.detail === 'string' ? data.detail : JSON.stringify(data))
      } else if (data.text_type === 'kana') {
        setResult(null)
        setErrMsg(data.note || '假名文学文本不适用漢文訓読。')
      } else {
        setResult(data)
        if (data.request_id) setLastRequestId(data.request_id)
        setErrMsg('')
      }
    } catch {
      setResult(null)
      setErrMsg('后端调用失败：请确认 uvicorn 已在 8000 端口启动。')
    } finally {
      setBusy(false)
    }
  }

  // NIGHT7: 行別対照——OCR 行与当前白文行并排，改过的行高亮
  const ocrLines = ocrHakubun ? ocrHakubun.replace(/\r/g, '').split('\n').filter((l) => l.trim() !== '') : []
  const curLines = hakubun ? hakubun.replace(/\r/g, '').split('\n').filter((l) => l.trim() !== '') : []

  function editLine(idx: number, newText: string) {
    const lines = [...curLines]
    while (lines.length <= idx) lines.push('')
    lines[idx] = newText
    setHakubun(lines.join('\n'))
  }

  async function loadHistory() {
    try {
      const res = await fetch('/api/history?limit=20')
      const data = await res.json()
      setHistoryItems(data.items || [])
      setHistoryOpen(true)
    } catch {
      setErrMsg('履歴の取得に失敗（后端未启动？）')
    }
  }

  function restoreHistory(item: HistoryItem) {
    setHakubun(item.hakubun)
    if (item.kaeriten_text && item.kakikudashi) {
      setResult({
        hakubun: item.hakubun,
        kaeriten_text: item.kaeriten_text,
        kakikudashi: item.kakikudashi,
        modern: '',
        glossary: [],
        request_id: item.id,
      })
      setLastRequestId(item.id)
    }
    setErrMsg('')
  }

  return (
    <div className="layout">
      <header className="header">
        <h1>漢文 → 書き下し文</h1>
        <p className="sub">Night 7：OCR 行別対照 + 纠错 + 历史翻回 / 訓読 UD-Kundoku / LLM 占位</p>
      </header>

      <div className="left-pane">
        <section className="card">
          <h2>输入</h2>
          <div className="entries">
            <div className="entry">
              <h3>入口 A：粘贴漢文文本</h3>
              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder={'例：王顧左右而言他'}
                rows={5}
              />
              <button onClick={sendToHakubun} disabled={!inputText.trim()}>
                → 送入白文
              </button>
            </div>
            <div className="entry">
              <h3>入口 B：上传图片（くずし字）</h3>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => {
                  const f = e.target.files?.[0]
                  if (f) void handleUpload(f)
                }}
                disabled={ocrBusy}
              />
              {ocrBusy && <p className="muted">OCR 处理中…（首次调用要加载模型，请稍候）</p>}
              {ocrNote && <p className={ocrNote.startsWith('OCR 完成') ? 'muted' : 'warn'}>{ocrNote}</p>}
            </div>
          </div>
        </section>

        <section className="card">
          <h2>白文（可编辑）</h2>
          <textarea
            value={hakubun}
            onChange={(e) => setHakubun(e.target.value)}
            placeholder={'OCR / 粘贴得到的白文会显示在这里，可直接修改后重新訓読。'}
            rows={6}
          />
          <div className="row">
            <button onClick={runKundoku} disabled={busy || !hakubun.trim()}>
              {busy ? '訓読中…' : '重新訓読'}
            </button>
            <button className="ghost" onClick={loadHistory}>履歴（翻回上一条）</button>
          </div>
          {errMsg && <p className="error">{errMsg}</p>}
        </section>

        {/* NIGHT7: 行別対照（OCR ↔ 手改） */}
        {ocrLines.length > 0 && (
          <section className="card">
            <h2>行別対照（改过的行会高亮，重新訓読只重算提交的文本）</h2>
            <div className="linecompare">
              <div className="imgcol">
                {ocrImgUrl && <img src={ocrImgUrl} alt="原图" />}
              </div>
              <div className="linescol">
                {curLines.map((line, idx) => {
                  const orig = ocrLines[idx] ?? ''
                  const changed = line !== orig
                  return (
                    <div key={idx} className={'linerow' + (changed ? ' changed' : '')}>
                      <span className="lineno">{idx + 1}</span>
                      <span className="origline">{orig || '（新行）'}</span>
                      <input
                        value={line}
                        onChange={(e) => editLine(idx, e.target.value)}
                      />
                    </div>
                  )
                })}
                {curLines.length === 0 && <p className="muted">白文为空。</p>}
              </div>
            </div>
          </section>
        )}

        {/* NIGHT7: 历史翻回 */}
        {historyOpen && (
          <section className="card">
            <h2>履歴（最近 20 条，点一条翻回）</h2>
            <ul className="historylist">
              {historyItems.map((h) => (
                <li key={h.id}>
                  <button className="ghost small" onClick={() => restoreHistory(h)}>
                    #{h.id} {h.created_at} — {h.hakubun.slice(0, 24)}…
                  </button>
                </li>
              ))}
              {historyItems.length === 0 && <li className="muted">还没有记录。</li>}
            </ul>
          </section>
        )}
      </div>

      <section className="card output-pane">
        <h2>输出</h2>
        <div className="outputs">
          <div className="out">
            <h3>① 返り点付き原文</h3>
            {result ? (
              <VerticalKaeriten raw={result.kaeriten_text_raw || result.kaeriten_text} />
            ) : (
              <pre>—</pre>
            )}
            <p className="muted small">{DISCLAIMER}</p>
          </div>
          <div className="out">
            <h3>② 書き下し文</h3>
            {result?.kakikudashi ? <VerticalPlain text={result.kakikudashi} /> : <pre>—</pre>}
            <p className="muted small">{DISCLAIMER}</p>
          </div>
          <div className="out">
            <h3>③ 現代語訳</h3>
            <pre className="placeholder">{result?.modern || '待接入 LLM（占位）'}</pre>
            <p className="muted small">{DISCLAIMER}</p>
          </div>
          <div className="out">
            <h3>④ 語釈</h3>
            {result && result.glossary.length > 0 ? (
              <ul className="glossary">
                {result.glossary.map((g, i) => (
                  <li key={i}>
                    {g.word}
                    {g.reading ? `（${g.reading}）` : ''}： {g.meaning}
                  </li>
                ))}
              </ul>
            ) : (
              <pre className="placeholder">待接入 LLM（占位）</pre>
            )}
            <p className="muted small">{DISCLAIMER}</p>
          </div>
        </div>
      </section>
    </div>
  )
}
