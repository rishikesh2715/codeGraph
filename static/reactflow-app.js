// /static/reactflow-app.js
// Minimal, dependency-free entry that lazy-loads React + @xyflow/react from ESM CDNs.

let React, ReactDOM, ReactFlowPkg;

async function ensureLibsLoaded() {
  if (React && ReactDOM && ReactFlowPkg) return;

  // Load React 18+ and ReactDOM from esm.sh (ESM-only; UMD builds are gone). :contentReference[oaicite:2]{index=2}
  const [{ default: ReactNS }, { createRoot }] = await Promise.all([
    import('https://esm.sh/react@18'),
    import('https://esm.sh/react-dom@18/client'),
  ]);

  // Load React Flow v12 package. We keep React externals to avoid duplicate Reacts. :contentReference[oaicite:3]{index=3}
  const RF = await import('@xyflow/react');

  React = ReactNS;
  ReactDOM = { createRoot };
  ReactFlowPkg = RF;
}

export async function renderReactFlow(containerId, graph, onNodeClick) {
  await ensureLibsLoaded();

  // Enable stylesheet (must be loaded) :contentReference[oaicite:4]{index=4}
  const link = document.getElementById('rf-style');
  if (link) link.disabled = false;

  const container = document.getElementById(containerId);
  container.style.display = 'block';

  const nodes = (graph.nodes || []).map((n, idx) => ({
    id: n.id,
    position: n.position || { x: idx * 50, y: idx * 25 },
    data: { label: n.label || n.id },
    // You can add className or style here to theme nodes later
  }));

  const edges = (graph.edges || []).map((e, idx) => ({
    id: `${e.from}-${e.to}-${idx}`,
    source: e.from,
    target: e.to,
    label: e.label, // simple text label for now
    type: 'default',
  }));

  const { ReactFlow, Background, Controls, MiniMap } = ReactFlowPkg;

  function RFApp() {
    const onNodeClickInternal = (_, node) => {
      if (typeof onNodeClick === 'function') onNodeClick(node.id);
    };
    return React.createElement(
      'div',
      { style: { width: '100%', height: '100%' } },
      React.createElement(
        ReactFlow,
        {
          nodes,
          edges,
          fitView: true,
          onNodeClick: onNodeClickInternal,
        }
      ),
      React.createElement(Background, null),
      React.createElement(Controls, null),
      React.createElement(MiniMap, null),
    );
  }

  const root = ReactDOM.createRoot(container);
  root.render(React.createElement(RFApp, null));
}
