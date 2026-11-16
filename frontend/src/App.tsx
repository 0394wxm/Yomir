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
const KAERITEN_RX = /[㆑㆒㆓㆔㆕㆖㆗㆘㆙㆚㆛㆜㆝㆞㆟]+/g

interface KaeritenChar { base: string; rt: string }

// 把 raw 返り点文本（含合字）解析成 [字, 返り点] 序列。合字紧跟在字后面，无歧义。
function parseKaeriten(line: string): KaeritenChar[] {
  const out: KaeritenChar[] = []
  let i = 0
  while (i < line.length) {
    const ch = line[i]
    if (KAERITEN_MAP[ch] !== undefined) {
      // 开头就出现合字（不该发生）：跳过
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
  error?: string
}

interface OcrResult {
  hakubun: string
  status: string
  note?: string
  line_count?: number
}

export default function App() {
  // 输入区（入口 A：粘贴文本）
  const [inputText, setInputText] = useState('')
  // 入口 B：上传图片
  const [ocrNote, setOcrNote] = useState('')
  const [ocrBusy, setOcrBusy] = useState(false)
  // 白文编辑区
  const [hakubun, setHakubun] = useState('')
  // 输出区
  const [result, setResult] = useState<KundokuResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [errMsg, setErrMsg] = useState('')

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
        setOcrNote(
          `OCR 完成（${data.line_count ?? '?'} 行）。白文已填入下方，可直接修改后点「重新訓読」。${DISCLAIMER}`,
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
        body: JSON.stringify({ text }),
      })
      const data = await res.json()
      if (!res.ok) {
        setResult(null)
        setErrMsg(typeof data.detail === 'string' ? data.detail : JSON.stringify(data))
      } else if (data.text_type === 'kana') {
        // NIGHT3: 假名白文分流——不进訓読，只提示
        setResult(null)
        setErrMsg(data.note || '假名文学文本不适用漢文訓読。')
      } else {
        setResult(data)
        setErrMsg('')
      }
    } catch {
      setResult(null)
      setErrMsg('后端调用失败：请确认 uvicorn 已在 8000 端口启动。')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="layout">
      <header className="header">
        <h1>漢文 → 書き下し文</h1>
        <p className="sub">Night 2：OCR 已接通（NDL 古典籍 OCR-Lite）/ 訓読 UD-Kundoku / LLM 占位</p>
      </header>

      <div className="left-pane">
        {/* 左上：输入区，两个入口并排 */}
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

        {/* 左下：白文编辑区 */}
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
          </div>
          {errMsg && <p className="error">{errMsg}</p>}
        </section>
      </div>

      {/* 右侧：输出区，四栏并列 */}
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
