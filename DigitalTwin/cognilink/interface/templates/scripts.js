/**
 * CogniLink Report Scripts
 * 
 * This file contains JavaScript functionality for CogniLink HTML reports.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all interactive elements
    initSmoothScrolling();
    initExpandableCards();
    initChartInteractions();
    initTableSorting();
    initDarkModeToggle();
    initPrintButton();
    initTooltips();
});

/**
 * Initialize smooth scrolling for anchor links
 */
function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                
                // Update URL without page reload
                history.pushState(null, null, targetId);
            }
        });
    });
}

/**
 * Initialize expandable cards for detailed information
 */
function initExpandableCards() {
    const expandableCards = document.querySelectorAll('.expandable-card');
    
    expandableCards.forEach(card => {
        const header = card.querySelector('.card-header');
        const content = card.querySelector('.card-content');
        
        if (header && content) {
            // Initially hide content
            content.style.display = 'none';
            
            // Add expand/collapse functionality
            header.addEventListener('click', () => {
                const isExpanded = content.style.display !== 'none';
                
                // Toggle content visibility
                content.style.display = isExpanded ? 'none' : 'block';
                
                // Update header indicator
                header.classList.toggle('expanded', !isExpanded);
                
                // Update aria attributes for accessibility
                header.setAttribute('aria-expanded', !isExpanded);
                content.setAttribute('aria-hidden', isExpanded);
            });
            
            // Set initial aria attributes
            header.setAttribute('aria-expanded', 'false');
            content.setAttribute('aria-hidden', 'true');
        }
    });
}

/**
 * Initialize chart interactions for visualizations
 */
function initChartInteractions() {
    const visualizations = document.querySelectorAll('.visualization');
    
    visualizations.forEach(viz => {
        const img = viz.querySelector('img');
        
        if (img) {
            // Add lightbox functionality
            img.addEventListener('click', () => {
                createLightbox(img.src, img.alt);
            });
            
            // Add hover effect
            img.style.cursor = 'pointer';
            img.title = 'Click to enlarge';
        }
    });
}

/**
 * Create a lightbox for enlarged image viewing
 */
function createLightbox(src, alt) {
    // Create lightbox container
    const lightbox = document.createElement('div');
    lightbox.className = 'lightbox';
    lightbox.style.position = 'fixed';
    lightbox.style.top = '0';
    lightbox.style.left = '0';
    lightbox.style.width = '100%';
    lightbox.style.height = '100%';
    lightbox.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
    lightbox.style.display = 'flex';
    lightbox.style.justifyContent = 'center';
    lightbox.style.alignItems = 'center';
    lightbox.style.zIndex = '1000';
    lightbox.style.padding = '20px';
    
    // Create image element
    const image = document.createElement('img');
    image.src = src;
    image.alt = alt;
    image.style.maxWidth = '90%';
    image.style.maxHeight = '90%';
    image.style.objectFit = 'contain';
    image.style.border = '2px solid white';
    image.style.borderRadius = '4px';
    
    // Create close button
    const closeBtn = document.createElement('button');
    closeBtn.textContent = '×';
    closeBtn.style.position = 'absolute';
    closeBtn.style.top = '20px';
    closeBtn.style.right = '20px';
    closeBtn.style.fontSize = '30px';
    closeBtn.style.color = 'white';
    closeBtn.style.background = 'none';
    closeBtn.style.border = 'none';
    closeBtn.style.cursor = 'pointer';
    
    // Add close functionality
    closeBtn.addEventListener('click', () => {
        document.body.removeChild(lightbox);
    });
    
    // Close on background click
    lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox) {
            document.body.removeChild(lightbox);
        }
    });
    
    // Add elements to lightbox
    lightbox.appendChild(image);
    lightbox.appendChild(closeBtn);
    
    // Add lightbox to document
    document.body.appendChild(lightbox);
}

/**
 * Initialize table sorting functionality
 */
function initTableSorting() {
    const tables = document.querySelectorAll('table');
    
    tables.forEach(table => {
        const headers = table.querySelectorAll('th');
        
        headers.forEach((header, index) => {
            // Add sort indicator and styling
            header.style.cursor = 'pointer';
            header.style.userSelect = 'none';
            
            // Add sort direction indicator
            const indicator = document.createElement('span');
            indicator.className = 'sort-indicator';
            indicator.textContent = ' ↕️';
            indicator.style.fontSize = '0.8em';
            indicator.style.opacity = '0.5';
            header.appendChild(indicator);
            
            // Add click handler for sorting
            header.addEventListener('click', () => {
                sortTable(table, index);
                
                // Update all indicators
                table.querySelectorAll('.sort-indicator').forEach(ind => {
                    ind.textContent = ' ↕️';
                    ind.style.opacity = '0.5';
                });
                
                // Update this indicator
                const currentDirection = header.getAttribute('data-sort-direction');
                indicator.textContent = currentDirection === 'asc' ? ' 🔼' : ' 🔽';
                indicator.style.opacity = '1';
            });
        });
    });
}

/**
 * Sort a table by the specified column index
 */
function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const header = table.querySelectorAll('th')[columnIndex];
    
    // Determine sort direction
    const currentDirection = header.getAttribute('data-sort-direction') || 'none';
    const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
    
    // Update header attribute
    header.setAttribute('data-sort-direction', newDirection);
    
    // Sort the rows
    rows.sort((rowA, rowB) => {
        const cellA = rowA.querySelectorAll('td')[columnIndex].textContent.trim();
        const cellB = rowB.querySelectorAll('td')[columnIndex].textContent.trim();
        
        // Try to sort as numbers if possible
        const numA = parseFloat(cellA.replace(/[^0-9.-]+/g, ''));
        const numB = parseFloat(cellB.replace(/[^0-9.-]+/g, ''));
        
        if (!isNaN(numA) && !isNaN(numB)) {
            return newDirection === 'asc' ? numA - numB : numB - numA;
        }
        
        // Otherwise sort as strings
        return newDirection === 'asc' 
            ? cellA.localeCompare(cellB) 
            : cellB.localeCompare(cellA);
    });
    
    // Remove existing rows
    rows.forEach(row => tbody.removeChild(row));
    
    // Add sorted rows
    rows.forEach(row => tbody.appendChild(row));
}

/**
 * Initialize dark mode toggle
 */
function initDarkModeToggle() {
    // Create toggle button
    const toggleBtn = document.createElement('button');
    toggleBtn.id = 'dark-mode-toggle';
    toggleBtn.innerHTML = '🌙';
    toggleBtn.title = 'Toggle Dark Mode';
    toggleBtn.style.position = 'fixed';
    toggleBtn.style.bottom = '20px';
    toggleBtn.style.right = '20px';
    toggleBtn.style.width = '50px';
    toggleBtn.style.height = '50px';
    toggleBtn.style.borderRadius = '50%';
    toggleBtn.style.backgroundColor = 'var(--card-background)';
    toggleBtn.style.border = '2px solid var(--border-color)';
    toggleBtn.style.fontSize = '20px';
    toggleBtn.style.cursor = 'pointer';
    toggleBtn.style.zIndex = '100';
    toggleBtn.style.boxShadow = '0 2px 5px var(--shadow-color)';
    
    // Add toggle functionality
    toggleBtn.addEventListener('click', () => {
        const isDarkMode = document.body.classList.toggle('dark-mode');
        toggleBtn.innerHTML = isDarkMode ? '☀️' : '🌙';
        
        // Store preference
        localStorage.setItem('darkMode', isDarkMode);
    });
    
    // Add to document
    document.body.appendChild(toggleBtn);
    
    // Check for saved preference
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
        toggleBtn.innerHTML = '☀️';
    }
}

/**
 * Initialize print button
 */
function initPrintButton() {
    // Create print button
    const printBtn = document.createElement('button');
    printBtn.id = 'print-button';
    printBtn.innerHTML = '🖨️';
    printBtn.title = 'Print Report';
    printBtn.style.position = 'fixed';
    printBtn.style.bottom = '20px';
    printBtn.style.right = '80px';
    printBtn.style.width = '50px';
    printBtn.style.height = '50px';
    printBtn.style.borderRadius = '50%';
    printBtn.style.backgroundColor = 'var(--card-background)';
    printBtn.style.border = '2px solid var(--border-color)';
    printBtn.style.fontSize = '20px';
    printBtn.style.cursor = 'pointer';
    printBtn.style.zIndex = '100';
    printBtn.style.boxShadow = '0 2px 5px var(--shadow-color)';
    
    // Add print functionality
    printBtn.addEventListener('click', () => {
        window.print();
    });
    
    // Add to document
    document.body.appendChild(printBtn);
}

/**
 * Initialize tooltips for data points
 */
function initTooltips() {
    const dataPoints = document.querySelectorAll('[data-tooltip]');
    
    dataPoints.forEach(point => {
        const tooltipText = point.getAttribute('data-tooltip');
        
        if (tooltipText) {
            // Create tooltip element
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = tooltipText;
            tooltip.style.position = 'absolute';
            tooltip.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
            tooltip.style.color = 'white';
            tooltip.style.padding = '5px 10px';
            tooltip.style.borderRadius = '4px';
            tooltip.style.fontSize = '14px';
            tooltip.style.zIndex = '100';
            tooltip.style.pointerEvents = 'none';
            tooltip.style.opacity = '0';
            tooltip.style.transition = 'opacity 0.3s';
            
            // Add tooltip to document
            document.body.appendChild(tooltip);
            
            // Show tooltip on hover
            point.addEventListener('mouseenter', (e) => {
                const rect = point.getBoundingClientRect();
                tooltip.style.left = `${rect.left + window.scrollX}px`;
                tooltip.style.top = `${rect.bottom + window.scrollY + 5}px`;
                tooltip.style.opacity = '1';
            });
            
            // Hide tooltip on mouse leave
            point.addEventListener('mouseleave', () => {
                tooltip.style.opacity = '0';
            });
        }
    });
}