/**
 * Cognitive-Twin Web Interface - Enhanced JavaScript
 * 
 * Provides interactive functionality, real-time updates, and WebSocket communication
 * for the Cognitive-Twin web interface.
 */

// Global variables
let websocket = null;
let reconnectAttempts = 0;
let maxReconnectAttempts = 5;
let reconnectDelay = 1000;

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Cognitive-Twin Web Interface Initialized');
    
    // Initialize components
    initializeUI();
    initializeTooltips();
    initializeCharts();
    initializeDigitalTwinChat();
    initializeKnowledgeGraph();
    initializeDataImport();
    initializeAnalysisControls();
    setupEventListeners();
    initializeWebSocket();
    setupTheme();
    
    // Initialize real-time features
    initializeRealTimeUpdates();
});

/**
 * Initialize the main UI components
 */
function initializeUI() {
    // Add loading states
    document.body.classList.add('loaded');
    
    // Initialize mobile sidebar toggle
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    if (!sidebarToggle && window.innerWidth <= 768) {
        createMobileToggle();
    }
    
    // Initialize notification container
    if (!document.querySelector('.notification-container')) {
        const container = document.createElement('div');
        container.className = 'notification-container';
        document.body.appendChild(container);
    }
    
    // Add keyboard shortcuts
    setupKeyboardShortcuts();
}

/**
 * Create mobile toggle button
 */
function createMobileToggle() {
    const header = document.querySelector('.main-header');
    if (header) {
        const toggle = document.createElement('button');
        toggle.className = 'sidebar-toggle';
        toggle.innerHTML = '<i class="fas fa-bars"></i>';
        toggle.onclick = toggleSidebar;
        header.insertBefore(toggle, header.firstChild);
    }
}

/**
 * Toggle mobile sidebar
 */
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.toggle('sidebar-open');
    }
}

/**
 * Initialize tooltips with improved positioning
 */
function initializeTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', function(e) {
            showTooltip(e.target, e.target.getAttribute('data-tooltip'));
        });
        
        element.addEventListener('mouseleave', function() {
            hideTooltip();
        });
    });
}

/**
 * Show tooltip with smart positioning
 */
function showTooltip(element, text) {
    hideTooltip(); // Remove any existing tooltip
    
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = text;
    
    document.body.appendChild(tooltip);
    
    // Position tooltip
    const rect = element.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();
    
    let top = rect.bottom + 10;
    let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
    
    // Adjust if tooltip would go off screen
    if (left < 10) left = 10;
    if (left + tooltipRect.width > window.innerWidth - 10) {
        left = window.innerWidth - tooltipRect.width - 10;
    }
    
    if (top + tooltipRect.height > window.innerHeight - 10) {
        top = rect.top - tooltipRect.height - 10;
    }
    
    tooltip.style.top = top + 'px';
    tooltip.style.left = left + 'px';
    tooltip.style.opacity = '1';
}

/**
 * Hide tooltip
 */
function hideTooltip() {
    const existingTooltip = document.querySelector('.tooltip');
    if (existingTooltip) {
        existingTooltip.remove();
    }
}

/**
 * Enhanced chart initialization with error handling
 */
function initializeCharts() {
    // Check if Plotly is available
    if (typeof Plotly === 'undefined') {
        console.warn('Plotly library not loaded - charts will not be available');
        return;
    }
    
    // Initialize charts if they exist
    const chartContainers = document.querySelectorAll('.chart-container[data-chart-type]');
    
    chartContainers.forEach(container => {
        try {
            const chartType = container.getAttribute('data-chart-type');
            let chartData = {};
            let chartLayout = {};
            
            try {
                chartData = JSON.parse(container.getAttribute('data-chart-data') || '{}');
                chartLayout = JSON.parse(container.getAttribute('data-chart-layout') || '{}');
            } catch (e) {
                console.warn('Invalid chart data:', e);
                return;
            }
            
            // Create chart based on type
            switch (chartType) {
                case 'bar':
                    createBarChart(container.id, chartData, chartLayout);
                    break;
                case 'line':
                    createLineChart(container.id, chartData, chartLayout);
                    break;
                case 'pie':
                    createPieChart(container.id, chartData, chartLayout);
                    break;
                case 'scatter':
                    createScatterPlot(container.id, chartData, chartLayout);
                    break;
                case 'heatmap':
                    createHeatmap(container.id, chartData, chartLayout);
                    break;
                default:
                    console.warn(`Unknown chart type: ${chartType}`);
            }
        } catch (error) {
            console.error('Error initializing chart:', error);
            showChartError(container);
        }
    });
}

/**
 * Show chart error message
 */
function showChartError(container) {
    container.innerHTML = `
        <div class="chart-error">
            <i class="fas fa-exclamation-triangle"></i>
            <p>Unable to load chart</p>
        </div>
    `;
}

/**
 * Create enhanced bar chart
 */
function createBarChart(containerId, data, layout) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const plotData = [{
        x: data.x || [],
        y: data.y || [],
        type: 'bar',
        marker: {
            color: data.color || '#3498db',
            line: {
                color: 'rgba(52, 152, 219, 0.8)',
                width: 1
            }
        },
        hovertemplate: '<b>%{x}</b><br>%{y}<extra></extra>'
    }];
    
    const plotLayout = {
        title: {
            text: layout.title || '',
            font: { size: 16, color: '#2c3e50' }
        },
        xaxis: {
            title: layout.xaxis?.title || '',
            gridcolor: '#e9ecef'
        },
        yaxis: {
            title: layout.yaxis?.title || '',
            gridcolor: '#e9ecef'
        },
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)',
        font: { family: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto' },
        ...layout
    };
    
    const config = {
        responsive: true,
        displayModeBar: false
    };
    
    Plotly.newPlot(containerId, plotData, plotLayout, config);
}

/**
 * Create enhanced line chart
 */
function createLineChart(containerId, data, layout) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const plotData = [];
    
    // Handle multiple series
    if (data.series && Array.isArray(data.series)) {
        data.series.forEach((series, index) => {
            plotData.push({
                x: series.x || [],
                y: series.y || [],
                type: 'scatter',
                mode: 'lines+markers',
                name: series.label || `Series ${index + 1}`,
                line: {
                    color: series.color || getColorByIndex(index),
                    width: 3
                },
                marker: {
                    size: 6
                },
                hovertemplate: '<b>%{fullData.name}</b><br>%{x}: %{y}<extra></extra>'
            });
        });
    } else {
        // Single series
        plotData.push({
            x: data.x || [],
            y: data.y || [],
            type: 'scatter',
            mode: 'lines+markers',
            line: {
                color: data.color || '#3498db',
                width: 3
            },
            marker: {
                size: 6
            },
            hovertemplate: '%{x}: %{y}<extra></extra>'
        });
    }
    
    const plotLayout = {
        title: {
            text: layout.title || '',
            font: { size: 16, color: '#2c3e50' }
        },
        xaxis: {
            title: layout.xaxis?.title || '',
            gridcolor: '#e9ecef'
        },
        yaxis: {
            title: layout.yaxis?.title || '',
            gridcolor: '#e9ecef'
        },
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)',
        font: { family: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto' },
        showlegend: plotData.length > 1,
        ...layout
    };
    
    const config = {
        responsive: true,
        displayModeBar: false
    };
    
    Plotly.newPlot(containerId, plotData, plotLayout, config);
}

/**
 * Create enhanced pie chart
 */
function createPieChart(containerId, data, layout) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const plotData = [{
        values: data.values || [],
        labels: data.categories || [],
        type: 'pie',
        hole: 0.3,
        marker: {
            colors: data.colors || getColorPalette(data.values?.length || 0)
        },
        textinfo: 'label+percent',
        textposition: 'outside',
        hovertemplate: '<b>%{label}</b><br>%{value} (%{percent})<extra></extra>'
    }];
    
    const plotLayout = {
        title: {
            text: layout.title || '',
            font: { size: 16, color: '#2c3e50' }
        },
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)',
        font: { family: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto' },
        showlegend: true,
        legend: {
            orientation: 'v',
            x: 1.05,
            y: 0.5
        },
        ...layout
    };
    
    const config = {
        responsive: true,
        displayModeBar: false
    };
    
    Plotly.newPlot(containerId, plotData, plotLayout, config);
}

/**
 * Get color by index for multiple series
 */
function getColorByIndex(index) {
    const colors = [
        '#3498db', '#e74c3c', '#2ecc71', '#f39c12', 
        '#9b59b6', '#1abc9c', '#34495e', '#e67e22'
    ];
    return colors[index % colors.length];
}

/**
 * Get color palette for charts
 */
function getColorPalette(count) {
    const baseColors = [
        '#3498db', '#e74c3c', '#2ecc71', '#f39c12', 
        '#9b59b6', '#1abc9c', '#34495e', '#e67e22'
    ];
    
    const colors = [];
    for (let i = 0; i < count; i++) {
        colors.push(baseColors[i % baseColors.length]);
    }
    return colors;
}

/**
 * Enhanced digital twin chat initialization
 */
function initializeDigitalTwinChat() {
    const chatContainer = document.querySelector('.chat-container');
    if (!chatContainer) return;
    
    const chatForm = chatContainer.querySelector('.chat-form');
    const chatInput = chatContainer.querySelector('.chat-input input');
    const chatMessages = chatContainer.querySelector('.chat-messages');
    
    if (!chatForm || !chatInput || !chatMessages) return;
    
    // Scroll to bottom of messages
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Handle form submission
    chatForm.addEventListener('submit', handleChatSubmission);
    
    // Handle input focus/blur for better UX
    chatInput.addEventListener('focus', function() {
        chatContainer.classList.add('input-focused');
    });
    
    chatInput.addEventListener('blur', function() {
        chatContainer.classList.remove('input-focused');
    });
    
    // Auto-resize input if needed
    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = this.scrollHeight + 'px';
    });
    
    // Handle Enter key (send message, Shift+Enter for new line)
    chatInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });
}

/**
 * Handle chat form submission with enhanced error handling
 */
async function handleChatSubmission(event) {
    event.preventDefault();
    
    const form = event.target;
    const input = form.querySelector('input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Disable input and show loading
    input.disabled = true;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnHTML = submitBtn.innerHTML;
    submitBtn.innerHTML = '<div class="loading"></div>';
    
    // Clear input
    input.value = '';
    
    // Add user message to chat
    addChatMessage(message, 'user');
    
    // Get session ID
    const chatContainer = document.querySelector('.chat-container');
    const sessionId = chatContainer?.getAttribute('data-session-id') || 'default';
    
    try {
        // Show typing indicator
        showTypingIndicator();
        
        // Send message to API
        const response = await fetch('/api/v1/twin/message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                text: message,
                user_id: 'current_user',
                context: {
                    session_id: sessionId,
                    timestamp: new Date().toISOString()
                }
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Hide typing indicator
        hideTypingIndicator();
        
        // Add twin response to chat
        if (data.text) {
            addChatMessage(data.text, 'twin', data.metadata);
        } else if (data.error) {
            addChatMessage(`Error: ${data.error}`, 'system');
        } else {
            addChatMessage('I received your message but had trouble generating a response.', 'system');
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        hideTypingIndicator();
        
        let errorMessage = 'Sorry, I encountered an error. Please try again.';
        if (error.message.includes('404')) {
            errorMessage = 'Chat service is not available right now.';
        } else if (error.message.includes('500')) {
            errorMessage = 'Server error occurred. Please try again later.';
        }
        
        addChatMessage(errorMessage, 'system');
    } finally {
        // Re-enable input
        input.disabled = false;
        submitBtn.innerHTML = originalBtnHTML;
        input.focus();
    }
}

/**
 * Add a message to the chat with enhanced features
 */
function addChatMessage(text, sender, metadata = null) {
    const messagesContainer = document.querySelector('.chat-messages');
    if (!messagesContainer) return;
    
    const messageEl = document.createElement('div');
    messageEl.className = `message message-${sender}`;
    
    const timestamp = new Date().toLocaleTimeString();
    const messageId = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    let metadataHTML = '';
    if (metadata && sender === 'twin') {
        metadataHTML = `
            <div class="message-metadata">
                <small>
                    ${metadata.model_used ? `Model: ${metadata.model_used}` : ''}
                    ${metadata.confidence ? `• Confidence: ${Math.round(metadata.confidence * 100)}%` : ''}
                </small>
            </div>
        `;
    }
    
    messageEl.innerHTML = `
        <div class="message-content">${escapeHtml(text)}</div>
        <div class="message-timestamp">${timestamp}</div>
        ${metadataHTML}
        <div class="message-actions">
            <button class="message-action-btn" onclick="copyMessage('${messageId}')" title="Copy">
                <i class="fas fa-copy"></i>
            </button>
            ${sender === 'twin' ? `
                <button class="message-action-btn" onclick="likeMessage('${messageId}')" title="Like">
                    <i class="fas fa-thumbs-up"></i>
                </button>
                <button class="message-action-btn" onclick="dislikeMessage('${messageId}')" title="Dislike">
                    <i class="fas fa-thumbs-down"></i>
                </button>
            ` : ''}
        </div>
    `;
    
    messageEl.setAttribute('data-message-id', messageId);
    
    // Insert before typing indicator
    const typingIndicator = messagesContainer.querySelector('.typing-indicator');
    if (typingIndicator) {
        messagesContainer.insertBefore(messageEl, typingIndicator);
    } else {
        messagesContainer.appendChild(messageEl);
    }
    
    // Animate message appearance
    messageEl.style.opacity = '0';
    messageEl.style.transform = 'translateY(20px)';
    setTimeout(() => {
        messageEl.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        messageEl.style.opacity = '1';
        messageEl.style.transform = 'translateY(0)';
    }, 10);
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Update message count if element exists
    const messageCountEl = document.getElementById('messageCount');
    if (messageCountEl) {
        const currentCount = parseInt(messageCountEl.textContent) || 0;
        messageCountEl.textContent = currentCount + 1;
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    let indicator = document.querySelector('.typing-indicator');
    if (!indicator) {
        const messagesContainer = document.querySelector('.chat-messages');
        if (messagesContainer) {
            indicator = document.createElement('div');
            indicator.className = 'typing-indicator';
            indicator.innerHTML = `
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
                Your twin is thinking...
            `;
            messagesContainer.appendChild(indicator);
        }
    }
    
    if (indicator) {
        indicator.style.display = 'flex';
        const messagesContainer = document.querySelector('.chat-messages');
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }
}

/**
 * Hide typing indicator
 */
function hideTypingIndicator() {
    const indicator = document.querySelector('.typing-indicator');
    if (indicator) {
        indicator.style.display = 'none';
    }
}

/**
 * Copy message to clipboard
 */
function copyMessage(messageId) {
    const messageEl = document.querySelector(`[data-message-id="${messageId}"]`);
    if (messageEl) {
        const text = messageEl.querySelector('.message-content').textContent;
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Message copied to clipboard', 'success');
        }).catch(() => {
            showNotification('Failed to copy message', 'error');
        });
    }
}

/**
 * Like message
 */
function likeMessage(messageId) {
    const button = document.querySelector(`[data-message-id="${messageId}"] .fa-thumbs-up`).parentElement;
    button.innerHTML = '<i class="fas fa-thumbs-up" style="color: #2ecc71;"></i>';
    button.disabled = true;
    showNotification('Feedback recorded', 'success');
    
    // Send feedback to API (optional)
    sendMessageFeedback(messageId, 'like');
}

/**
 * Dislike message
 */
function dislikeMessage(messageId) {
    const button = document.querySelector(`[data-message-id="${messageId}"] .fa-thumbs-down`).parentElement;
    button.innerHTML = '<i class="fas fa-thumbs-down" style="color: #e74c3c;"></i>';
    button.disabled = true;
    showNotification('Feedback recorded', 'info');
    
    // Send feedback to API (optional)
    sendMessageFeedback(messageId, 'dislike');
}

/**
 * Send message feedback to API
 */
async function sendMessageFeedback(messageId, feedback) {
    try {
        await fetch('/api/digital-twin/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message_id: messageId, feedback })
        });
    } catch (error) {
        console.warn('Failed to send feedback:', error);
    }
}

/**
 * Enhanced knowledge graph initialization
 */
function initializeKnowledgeGraph() {
    const graphContainer = document.querySelector('.graph-container');
    if (!graphContainer) return;
    
    // Check if D3 is available
    if (typeof d3 === 'undefined') {
        console.warn('D3 library not loaded - knowledge graph will not be available');
        showGraphError(graphContainer);
        return;
    }
    
    try {
        // Get graph data
        let graphData = { nodes: [], links: [] };
        const dataAttr = graphContainer.getAttribute('data-graph');
        if (dataAttr) {
            graphData = JSON.parse(dataAttr);
        }
        
        // Create enhanced graph visualization
        createKnowledgeGraph(graphContainer, graphData);
        
    } catch (error) {
        console.error('Error initializing knowledge graph:', error);
        showGraphError(graphContainer);
    }
}

/**
 * Show graph error message
 */
function showGraphError(container) {
    container.innerHTML = `
        <div class="graph-error">
            <i class="fas fa-exclamation-triangle"></i>
            <p>Unable to load knowledge graph</p>
            <button class="btn btn-primary" onclick="location.reload()">Retry</button>
        </div>
    `;
}

/**
 * Create enhanced knowledge graph
 */
function createKnowledgeGraph(container, graphData) {
    // Clear container
    container.innerHTML = '';
    
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    // Create SVG
    const svg = d3.select(container)
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('class', 'knowledge-graph-svg');
    
    // Create graph container group
    const g = svg.append('g');
    
    // Add zoom and pan behavior
    const zoom = d3.zoom()
        .scaleExtent([0.1, 10])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        });
    
    svg.call(zoom);
    
    // Create simulation
    const simulation = d3.forceSimulation(graphData.nodes)
        .force('link', d3.forceLink(graphData.links).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(30));
    
    // Create links
    const link = g.selectAll('.link')
        .data(graphData.links)
        .enter().append('line')
        .attr('class', 'link')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', d => Math.sqrt(d.value || 1) * 2);
    
    // Create nodes
    const node = g.selectAll('.node')
        .data(graphData.nodes)
        .enter().append('circle')
        .attr('class', 'node')
        .attr('r', d => d.size || 8)
        .attr('fill', d => getNodeColor(d.group))
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .style('cursor', 'pointer')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));
    
    // Add node labels
    const nodeLabel = g.selectAll('.node-label')
        .data(graphData.nodes)
        .enter().append('text')
        .attr('class', 'node-label')
        .attr('dx', 12)
        .attr('dy', '.35em')
        .attr('font-family', 'sans-serif')
        .attr('font-size', '12px')
        .attr('fill', '#2c3e50')
        .text(d => d.label || d.id);
    
    // Add tooltips
    node.append('title')
        .text(d => d.description || d.label || d.id);
    
    // Add click handling
    node.on('click', function(event, d) {
        console.log('Node clicked:', d);
        showNodeDetails(d);
    });
    
    // Update positions on each tick
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        node
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);
        
        nodeLabel
            .attr('x', d => d.x)
            .attr('y', d => d.y);
    });
    
    // Drag functions
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}

/**
 * Get node color based on group
 */
function getNodeColor(group) {
    const colorMap = {
        'person': '#3498db',
        'organization': '#e74c3c',
        'event': '#2ecc71',
        'concept': '#f39c12',
        'location': '#9b59b6'
    };
    return colorMap[group] || '#34495e';
}

/**
 * Show node details in a modal or sidebar
 */
function showNodeDetails(node) {
    showNotification(`Node: ${node.label || node.id}`, 'info');
    // TODO: Implement detailed node view
}

/**
 * Enhanced data import functionality
 */
function initializeDataImport() {
    const importForm = document.querySelector('.import-form');
    if (!importForm) return;
    
    importForm.addEventListener('submit', handleDataImport);
    
    // Add drag and drop functionality
    const dropZone = document.querySelector('.upload-drop-zone');
    if (dropZone) {
        setupFileDropZone(dropZone);
    }
}

/**
 * Handle data import with progress tracking
 */
async function handleDataImport(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const submitButton = form.querySelector('button[type="submit"]');
    
    if (!submitButton) return;
    
    // Show loading state
    const originalText = submitButton.textContent;
    submitButton.innerHTML = '<div class="loading"></div> Importing...';
    submitButton.disabled = true;
    
    // Create progress bar
    const progressContainer = createProgressBar();
    form.insertAdjacentElement('afterend', progressContainer);
    
    try {
        const response = await fetch('/api/v1/data/sources', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        // Update progress to 100%
        updateProgress(progressContainer, 100);
        
        if (data.success) {
            showNotification('Data imported successfully!', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } else {
            throw new Error(data.error || 'Import failed');
        }
        
    } catch (error) {
        console.error('Import error:', error);
        showNotification(`Import failed: ${error.message}`, 'error');
    } finally {
        // Clean up
        setTimeout(() => {
            submitButton.textContent = originalText;
            submitButton.disabled = false;
            if (progressContainer.parentNode) {
                progressContainer.remove();
            }
        }, 3000);
    }
}

/**
 * Create progress bar element
 */
function createProgressBar() {
    const container = document.createElement('div');
    container.className = 'progress-container';
    container.innerHTML = `
        <div class="progress-bar">
            <div class="progress-fill" style="width: 0%"></div>
        </div>
        <div class="progress-text">0%</div>
    `;
    return container;
}

/**
 * Update progress bar
 */
function updateProgress(container, percent) {
    const fill = container.querySelector('.progress-fill');
    const text = container.querySelector('.progress-text');
    
    if (fill && text) {
        fill.style.width = percent + '%';
        text.textContent = Math.round(percent) + '%';
    }
}

/**
 * Enhanced analysis controls
 */
function initializeAnalysisControls() {
    const analysisForm = document.querySelector('.analysis-form');
    if (!analysisForm) return;
    
    analysisForm.addEventListener('submit', handleAnalysisSubmission);
    
    // Add real-time validation
    const requiredFields = analysisForm.querySelectorAll('[required]');
    requiredFields.forEach(field => {
        field.addEventListener('blur', validateField);
        field.addEventListener('input', clearFieldError);
    });
}

/**
 * Validate individual form field
 */
function validateField(event) {
    const field = event.target;
    const errorElement = field.parentNode.querySelector('.field-error');
    
    if (!field.value.trim() && field.hasAttribute('required')) {
        addFieldError(field, 'This field is required');
    } else if (errorElement) {
        errorElement.remove();
    }
}

/**
 * Add error message to field
 */
function addFieldError(field, message) {
    clearFieldError({ target: field });
    
    const errorElement = document.createElement('div');
    errorElement.className = 'field-error';
    errorElement.textContent = message;
    field.parentNode.appendChild(errorElement);
    field.classList.add('error');
}

/**
 * Clear field error
 */
function clearFieldError(event) {
    const field = event.target;
    const errorElement = field.parentNode.querySelector('.field-error');
    if (errorElement) {
        errorElement.remove();
    }
    field.classList.remove('error');
}

/**
 * Handle analysis form submission
 */
async function handleAnalysisSubmission(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.textContent;
    
    submitButton.innerHTML = '<div class="loading"></div> Analyzing...';
    submitButton.disabled = true;
    
    try {
        const response = await fetch('/api/v1/analysis/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.id) {
            showNotification('Analysis started successfully!', 'success');
            setTimeout(() => {
                window.location.href = `/analysis/${result.id}`;
            }, 1500);
        } else {
            throw new Error(result.error || 'Analysis failed to start');
        }
        
    } catch (error) {
        console.error('Analysis error:', error);
        showNotification(`Analysis failed: ${error.message}`, 'error');
    } finally {
        submitButton.textContent = originalText;
        submitButton.disabled = false;
    }
}

/**
 * Setup comprehensive event listeners
 */
function setupEventListeners() {
    // Responsive sidebar toggle
    setupSidebarToggle();
    
    // Tab navigation
    setupTabNavigation();
    
    // Dropdown menus
    setupDropdownMenus();
    
    // Modal handling
    setupModalHandling();
    
    // Infinite scroll (if needed)
    setupInfiniteScroll();
    
    // Keyboard navigation
    setupKeyboardNavigation();
}

/**
 * Setup sidebar toggle for mobile
 */
function setupSidebarToggle() {
    const toggleButton = document.querySelector('.sidebar-toggle');
    if (toggleButton) {
        toggleButton.addEventListener('click', toggleSidebar);
    }
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(e) {
        const sidebar = document.querySelector('.sidebar');
        const toggle = document.querySelector('.sidebar-toggle');
        
        if (sidebar && sidebar.classList.contains('sidebar-open')) {
            if (!sidebar.contains(e.target) && !toggle?.contains(e.target)) {
                sidebar.classList.remove('sidebar-open');
            }
        }
    });
}

/**
 * Setup tab navigation
 */
function setupTabNavigation() {
    const tabLinks = document.querySelectorAll('.tab-link');
    
    tabLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const tabId = this.getAttribute('data-tab');
            if (!tabId) return;
            
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Deactivate all tab links
            tabLinks.forEach(otherLink => {
                otherLink.classList.remove('active');
            });
            
            // Show selected tab content
            const targetTab = document.getElementById(tabId);
            if (targetTab) {
                targetTab.classList.add('active');
                this.classList.add('active');
            }
        });
    });
}

/**
 * Setup dropdown menus
 */
function setupDropdownMenus() {
    const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
    
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const dropdown = this.nextElementSibling;
            if (!dropdown) return;
            
            // Close other dropdowns
            document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                if (menu !== dropdown) {
                    menu.classList.remove('show');
                }
            });
            
            // Toggle current dropdown
            dropdown.classList.toggle('show');
        });
    });
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function() {
        document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
            menu.classList.remove('show');
        });
    });
}

/**
 * Setup modal handling
 */
function setupModalHandling() {
    // Modal open triggers
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-modal-target]')) {
            const modalId = e.target.getAttribute('data-modal-target');
            openModal(modalId);
        }
        
        if (e.target.matches('.modal-close') || e.target.closest('.modal-close')) {
            closeModal();
        }
        
        if (e.target.matches('.modal-backdrop')) {
            closeModal();
        }
    });
    
    // Close modal with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

/**
 * Open modal
 */
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
        document.body.classList.add('modal-open');
        
        // Focus first focusable element
        const focusable = modal.querySelector('input, button, textarea, select');
        if (focusable) {
            focusable.focus();
        }
    }
}

/**
 * Close modal
 */
function closeModal() {
    const openModal = document.querySelector('.modal.show');
    if (openModal) {
        openModal.classList.remove('show');
        document.body.classList.remove('modal-open');
    }
}

/**
 * Setup keyboard shortcuts
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + / for search
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            const searchInput = document.querySelector('.search-input');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Ctrl/Cmd + K for quick actions
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            showQuickActions();
        }
        
        // Escape to close overlays
        if (e.key === 'Escape') {
            // Close notifications
            document.querySelectorAll('.notification.show').forEach(notif => {
                notif.classList.remove('show');
            });
            
            // Close dropdowns
            document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                menu.classList.remove('show');
            });
        }
    });
}

/**
 * Show quick actions menu
 */
function showQuickActions() {
    showNotification('Quick actions: Coming soon!', 'info');
}

/**
 * Setup keyboard navigation
 */
function setupKeyboardNavigation() {
    // Navigate with arrow keys in lists
    document.addEventListener('keydown', function(e) {
        const focused = document.activeElement;
        
        if (focused && focused.closest('.list-item')) {
            const list = focused.closest('.list');
            if (!list) return;
            
            const items = Array.from(list.querySelectorAll('.list-item [tabindex], .list-item a, .list-item button'));
            const currentIndex = items.indexOf(focused);
            
            let nextIndex = currentIndex;
            
            if (e.key === 'ArrowDown' && currentIndex < items.length - 1) {
                nextIndex = currentIndex + 1;
            } else if (e.key === 'ArrowUp' && currentIndex > 0) {
                nextIndex = currentIndex - 1;
            }
            
            if (nextIndex !== currentIndex) {
                e.preventDefault();
                items[nextIndex].focus();
            }
        }
    });
}

/**
 * Initialize WebSocket connection for real-time features
 */
function initializeWebSocket() {
    if (!window.WebSocket) {
        console.warn('WebSocket not supported');
        return;
    }
    
    connectWebSocket();
}

/**
 * Connect to WebSocket
 */
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/digital-twin`;
    
    try {
        websocket = new WebSocket(wsUrl);
        
        websocket.onopen = function() {
            console.log('WebSocket connected');
            reconnectAttempts = 0;
            reconnectDelay = 1000;
            updateConnectionStatus(true);
        };
        
        websocket.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        websocket.onclose = function() {
            console.log('WebSocket disconnected');
            updateConnectionStatus(false);
            attemptReconnect();
        };
        
        websocket.onerror = function(error) {
            console.error('WebSocket error:', error);
            updateConnectionStatus(false);
        };
        
    } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
        updateConnectionStatus(false);
    }
}

/**
 * Handle WebSocket messages
 */
function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'chat_response':
            if (data.text) {
                hideTypingIndicator();
                addChatMessage(data.text, 'twin', data.metadata);
            }
            break;
            
        case 'system_notification':
            showNotification(data.message, data.level || 'info');
            break;
            
        case 'real_time_update':
            handleRealTimeUpdate(data);
            break;
            
        default:
            console.log('Unknown WebSocket message type:', data.type);
    }
}

/**
 * Handle real-time updates
 */
function handleRealTimeUpdate(data) {
    // Update dashboard stats
    if (data.dashboard_stats) {
        updateDashboardStats(data.dashboard_stats);
    }
    
    // Update activity feed
    if (data.activity) {
        addActivityItem(data.activity);
    }
    
    // Update system health
    if (data.health_status) {
        updateHealthStatus(data.health_status);
    }
}

/**
 * Update dashboard statistics
 */
function updateDashboardStats(stats) {
    Object.entries(stats).forEach(([key, value]) => {
        const element = document.querySelector(`[data-stat="${key}"]`);
        if (element) {
            animateValueChange(element, value);
        }
    });
}

/**
 * Animate value change
 */
function animateValueChange(element, newValue) {
    const currentValue = parseInt(element.textContent) || 0;
    const duration = 1000;
    const steps = 30;
    const stepValue = (newValue - currentValue) / steps;
    let step = 0;
    
    const interval = setInterval(() => {
        step++;
        const value = Math.round(currentValue + (stepValue * step));
        element.textContent = value;
        
        if (step >= steps) {
            clearInterval(interval);
            element.textContent = newValue;
        }
    }, duration / steps);
}

/**
 * Attempt WebSocket reconnection
 */
function attemptReconnect() {
    if (reconnectAttempts >= maxReconnectAttempts) {
        console.log('Max reconnection attempts reached');
        return;
    }
    
    reconnectAttempts++;
    console.log(`Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts})...`);
    
    setTimeout(() => {
        connectWebSocket();
    }, reconnectDelay);
    
    // Exponential backoff
    reconnectDelay = Math.min(reconnectDelay * 2, 30000);
}

/**
 * Update connection status indicator
 */
function updateConnectionStatus(connected) {
    const indicators = document.querySelectorAll('.connection-status');
    indicators.forEach(indicator => {
        indicator.classList.toggle('connected', connected);
        indicator.classList.toggle('disconnected', !connected);
        indicator.title = connected ? 'Connected' : 'Disconnected';
    });
}

/**
 * Setup theme management
 */
function setupTheme() {
    // Load saved theme
    const savedTheme = localStorage.getItem('cognitive-twin-theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Update theme toggle icon
    updateThemeToggleIcon(savedTheme);
    
    // Listen for system theme changes
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            if (!localStorage.getItem('cognitive-twin-theme')) {
                const newTheme = e.matches ? 'dark' : 'light';
                document.documentElement.setAttribute('data-theme', newTheme);
                updateThemeToggleIcon(newTheme);
            }
        });
    }
}

/**
 * Toggle theme
 */
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('cognitive-twin-theme', newTheme);
    updateThemeToggleIcon(newTheme);
    
    showNotification(`Switched to ${newTheme} theme`, 'info');
}

/**
 * Update theme toggle icon
 */
function updateThemeToggleIcon(theme) {
    const toggles = document.querySelectorAll('.theme-toggle i');
    toggles.forEach(icon => {
        icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    });
}

/**
 * Initialize real-time updates
 */
function initializeRealTimeUpdates() {
    // Auto-refresh data every 30 seconds
    setInterval(refreshDashboardData, 30000);
    
    // Initialize activity stream
    initializeActivityStream();
    
    // Setup notification system
    setupNotificationSystem();
}

/**
 * Refresh dashboard data
 */
async function refreshDashboardData() {
    try {
        const response = await fetch('/api/v1/dashboard/stats');
        if (response.ok) {
            const data = await response.json();
            updateDashboardStats(data);
        }
    } catch (error) {
        console.warn('Failed to refresh dashboard data:', error);
    }
}

/**
 * Enhanced notification system
 */
function showNotification(message, type = 'info', duration = 5000) {
    const container = document.querySelector('.notification-container') || document.body;
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    const icon = getNotificationIcon(type);
    notification.innerHTML = `
        <div class="notification-content">
            <i class="${icon}"></i>
            <span>${escapeHtml(message)}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(notification);
    
    // Animate in
    setTimeout(() => notification.classList.add('show'), 10);
    
    // Auto-remove
    if (duration > 0) {
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }
    
    return notification;
}

/**
 * Get notification icon
 */
function getNotificationIcon(type) {
    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };
    return icons[type] || icons.info;
}

/**
 * Setup notification system
 */
function setupNotificationSystem() {
    // Create notification container if it doesn't exist
    if (!document.querySelector('.notification-container')) {
        const container = document.createElement('div');
        container.className = 'notification-container';
        document.body.appendChild(container);
    }
    
    // Add notification styles if not present
    if (!document.querySelector('#notification-styles')) {
        const styles = document.createElement('style');
        styles.id = 'notification-styles';
        styles.textContent = `
            .notification-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                pointer-events: none;
            }
            
            .notification {
                background: white;
                border-radius: 8px;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
                margin-bottom: 10px;
                padding: 16px;
                min-width: 300px;
                max-width: 400px;
                transform: translateX(100%);
                transition: transform 0.3s ease, opacity 0.3s ease;
                pointer-events: all;
                border-left: 4px solid;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            .notification.show {
                transform: translateX(0);
            }
            
            .notification-success { border-left-color: #2ecc71; }
            .notification-error { border-left-color: #e74c3c; }
            .notification-warning { border-left-color: #f39c12; }
            .notification-info { border-left-color: #3498db; }
            
            .notification-content {
                display: flex;
                align-items: center;
                gap: 10px;
                flex: 1;
            }
            
            .notification-close {
                background: none;
                border: none;
                cursor: pointer;
                color: #666;
                padding: 4px;
                border-radius: 4px;
                transition: background-color 0.2s ease;
            }
            
            .notification-close:hover {
                background: #f0f0f0;
            }
        `;
        document.head.appendChild(styles);
    }
}

// Expose global functions
window.toggleTheme = toggleTheme;
window.showNotification = showNotification;
window.copyMessage = copyMessage;
window.likeMessage = likeMessage;
window.dislikeMessage = dislikeMessage;