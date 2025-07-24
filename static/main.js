document.addEventListener('DOMContentLoaded', () => {
    const generateBtn = document.getElementById('generateBtn');
    const folderPathInput = document.getElementById('folderPath');
    const flowchartDiv = document.getElementById('flowchart');
    const summaryContent = document.getElementById('summary-content');
    const tooltip = document.getElementById('edge-tooltip');

    let summaries = {};
    let edgeDetails = {};

    const renderFlowchart = async (mermaidGraph) => {
        try {
            const { svg } = await mermaid.render('graph', mermaidGraph);
            flowchartDiv.innerHTML = svg;
            addInteractivity();
        } catch (error) {
            flowchartDiv.innerHTML = `<p style="color: red;">Error rendering graph: ${error.message}</p>`;
        }
    };

    const addInteractivity = () => {
        // Node click listeners for summaries
        const nodes = flowchartDiv.querySelectorAll('.node');
        nodes.forEach(node => {
            node.addEventListener('click', (event) => {
                const nodeId = event.currentTarget.id;
                const cleanId = nodeId.replace(/^flowchart-/i, '').replace(/-[0-9]+$/, '');
                document.querySelectorAll('.node.selected').forEach(n => n.classList.remove('selected'));
                event.currentTarget.classList.add('selected');
                summaryContent.textContent = summaries[cleanId] || 'No summary available for this node.';
            });
        });

        // Edge hover listeners for tooltips
        const edges = flowchartDiv.querySelectorAll('.edgePath');
        edges.forEach(edge => {
            // Mermaid uses classes like LS-node1 LE-node2 to identify edge endpoints
            const classList = Array.from(edge.classList);
            const startNodeClass = classList.find(c => c.startsWith('LS-'));
            const endNodeClass = classList.find(c => c.startsWith('LE-'));

            if (startNodeClass && endNodeClass) {
                const startNodeId = startNodeClass.substring(3);
                const endNodeId = endNodeClass.substring(3);
                const edgeKey = `${startNodeId}_${endNodeId}`;
                
                const details = edgeDetails[edgeKey];
                if (!details) return;

                edge.addEventListener('mouseover', (event) => {
                    let tooltipContent = `<h4>${details[0].from} → ${details[0].to}</h4>`;
                    details.forEach(d => {
                        tooltipContent += `<pre>${d.snippet}</pre>`;
                    });
                    tooltip.innerHTML = tooltipContent;
                    tooltip.classList.remove('hidden');
                });

                edge.addEventListener('mousemove', (event) => {
                    tooltip.style.left = `${event.pageX + 15}px`;
                    tooltip.style.top = `${event.pageY + 15}px`;
                });

                edge.addEventListener('mouseout', () => {
                    tooltip.classList.add('hidden');
                });
            }
        });
    };

    generateBtn.addEventListener('click', async () => {
        const path = folderPathInput.value;
        if (!path) {
            alert('Please enter a folder path.');
            return;
        }

        flowchartDiv.innerHTML = 'Analyzing...';
        summaryContent.textContent = '...';

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'An unknown error occurred.');
            }

            const data = await response.json();
            summaries = data.summaries;
            edgeDetails = data.edge_details;
            
            await renderFlowchart(data.mermaid);

        } catch (error) {
            flowchartDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
        }
    });
});