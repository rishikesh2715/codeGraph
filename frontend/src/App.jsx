import React, { useState } from 'react'
import { ReactFlow, Background, Controls, MiniMap } from '@xyflow/react'
import '@xyflow/react/dist/style.css'

export default function App() {
  const [nodes, setNodes] = useState([])
  const [edges, setEdges] = useState([])
  const [summary, setSummary] = useState('Click on a node to see its summary.')
  const [summaries, setSummaries] = useState({})
  const [useMock, setUseMock] = useState(true)
  const [mockFilename, setMockFilename] = useState('mock_graph.json')
  const [path, setPath] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const loadGraph = async () => {
    setLoading(true)
    setError('')
    setSummary('...')
    try {
      const body = useMock ? { use_mock: true, mock_filename: mockFilename } : { path }
      const res = await fetch('/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const e = await res.json().catch(() => ({}))
        throw new Error(e.error || 'Request failed')
      }
      const data = await res.json()
      setSummaries(data.summaries || {})

      // ---- normalize positions from backend (Graphviz) ----
      const rawNodes = data.graph?.nodes || []
      const hasPositions = rawNodes.every(
        n => n.position && typeof n.position.x === 'number' && typeof n.position.y === 'number'
      )

      let rfNodes
      if (hasPositions) {
        const xs = rawNodes.map(n => n.position.x)
        const ys = rawNodes.map(n => n.position.y)
        const minX = Math.min(...xs)
        const minY = Math.min(...ys)
        const maxY = Math.max(...ys)
        const SCALE = 1.0 // tweak if spacing feels too tight

        rfNodes = rawNodes.map(n => ({
          id: n.id,
          data: { label: n.label || n.id },
          position: {
            x: (n.position.x - minX) * SCALE,
            y: (maxY - n.position.y) * SCALE, // flip Y
          },
        }))
      } else {
        // fallback to a simple grid if no positions
        rfNodes = rawNodes.map((n, i) => ({
          id: n.id,
          data: { label: n.label || n.id },
          position: { x: (i % 5) * 220, y: Math.floor(i / 5) * 140 },
        }))
      }

      const rfEdges = (data.graph?.edges || []).map((e, idx) => ({
        id: `${e.from}-${e.to}-${idx}`,
        source: e.from,
        target: e.to,
        label: e.label,
        type: 'default',
      }))

      setNodes(rfNodes)
      setEdges(rfEdges)
      setSummary('Loaded. Click a node to see its summary.')
    } catch (err) {
      setError(String(err.message || err))
      setSummary('Error.')
    } finally {
      setLoading(false)
    }
  }

  const onNodeClick = (_, node) => {
    setSummary(summaries[node.id] || 'No summary available for this node.')
  }

  return (
    <div style={{ width: '100vw', height: '100vh', display: 'grid', gridTemplateColumns: '3fr 1fr' }}>
      <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
        <h2 style={{ margin: 0 }}>AI Interactive Flowchart (React Flow)</h2>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <button onClick={loadGraph} disabled={loading}>
            {loading ? 'Analyzing…' : 'Generate Flowchart'}
          </button>

          <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <input
              type="checkbox"
              checked={useMock}
              onChange={(e) => setUseMock(e.target.checked)}
            />
            Use local JSON
          </label>

          {useMock ? (
            <input
              placeholder="mock_graph.json"
              value={mockFilename}
              onChange={(e) => setMockFilename(e.target.value)}
              style={{ width: 220 }}
            />
          ) : (
            <input
              placeholder="D:\\Documents\\your-project"
              value={path}
              onChange={(e) => setPath(e.target.value)}
              style={{ width: 320 }}
            />
          )}
        </div>

        {error && <div style={{ color: 'red' }}>{error}</div>}

        <div style={{ flex: 1, border: '1px solid #dfe4e8', borderRadius: 8, overflow: 'hidden' }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodeClick={onNodeClick}
            fitView
          >
            <Background />
            <Controls />
            <MiniMap />
          </ReactFlow>
        </div>
      </div>

      <aside style={{ padding: 12, borderLeft: '1px solid #eee', background: '#fafafa' }}>
        <h3 style={{ marginTop: 0 }}>File Summary</h3>
        <pre style={{ whiteSpace: 'pre-wrap' }}>{summary}</pre>
      </aside>
    </div>
  )
}
