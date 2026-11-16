import { useState } from 'react'
import './App.css'

const DISCLAIMER = 'AI 初稿，仅供参考，请以原文和专业判断为准。'

interface KundokuResult {
  hakubun: string
  kaeriten_text: string
  kakikudashi: string
  modern: string
  glossary: string[]
  error?: string
}

interface OcrResult {
  hakubun: string
  status: string
  note: string
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
      setOcrNote(data.note || data.status)
    } catch {
      setOcrNote('OCR 接口调用失败（后端未启动？）')
    } finally {
      setOcrBusy(false)
    }
  }

  async function runKundoku() {
    const text = hakubun.trim()
    if (!text) {
      setErrMsg('白文为空，请先粘贴漢文或手动输入。')
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
      } else {
        setResult(data)
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
        <p className="sub">Night 1 骨架：UD-Kundoku 本地引擎 / OCR 占位 / LLM 占位</p>
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
              {ocrBusy && <p className="muted">上传中…</p>}
              {ocrNote && <p className="warn">{ocrNote}</p>}
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
            <pre>{result?.kaeriten_text || '—'}</pre>
            <p className="muted small">{DISCLAIMER}</p>
          </div>
          <div className="out">
            <h3>② 書き下し文</h3>
            <pre>{result?.kakikudashi || '—'}</pre>
            <p className="muted small">{DISCLAIMER}</p>
          </div>
          <div className="out">
            <h3>③ 現代語訳</h3>
            <pre className="placeholder">待接入 LLM（占位）</pre>
            <p className="muted small">{DISCLAIMER}</p>
          </div>
          <div className="out">
            <h3>④ 語釈</h3>
            <pre className="placeholder">待接入 LLM（占位）</pre>
            <p className="muted small">{DISCLAIMER}</p>
          </div>
        </div>
      </section>
    </div>
  )
}
