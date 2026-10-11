/**
 * =============================================================================
 * RAPIDREQ - Priority-Based Emergency Request & Dispatch System
 * Dashboard Client Script & Chart.js Visualizations
 * =============================================================================
 * Fetches real aggregated telemetry from Flask backend (/api/analytics)
 * and renders 4 responsive Chart.js visual models:
 *  1. Emergency Requests by Type (Bar)
 *  2. Priority Distribution (Doughnut)
 *  3. Requests by Hour (Line)
 *  4. Average Response Time by Priority (Bar)
 * =============================================================================
 */

const RapidReqDashboard = (function() {
    // Chart instances storage to allow re-rendering
    const chartInstances = {};

    // Standard Palette Matching Priority UI
    const colors = {
        p1: '#dc2626', // Critical
        p2: '#ea580c', // High
        p3: '#d97706', // Medium
        p4: '#16a34a', // Low
        primary: '#2563eb',
        primaryAlpha: 'rgba(37, 99, 235, 0.2)',
        success: '#10b981',
        warning: '#f59e0b',
        info: '#06b6d4',
        typeColors: [
            '#ef4444', // Accident
            '#3b82f6', // Medical
            '#f97316', // Fire
            '#10b981', // Rescue
            '#8b5cf6'  // Other
        ]
    };

    /**
     * Fetches analytics data from MySQL via the /api/analytics endpoint
     */
    async function fetchAnalyticsData() {
        try {
            const response = await fetch('/api/analytics');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('[RAPIDREQ] Failed to load analytics from server:', error);
            return null;
        }
    }

    /**
     * Initializes all Chart.js instances
     * @param {Object} options - { previewOnly: Boolean }
     */
    async function initCharts(options = { previewOnly: false }) {
        const data = await fetchAnalyticsData();
        if (!data) return;

        if (options.previewOnly) {
            // Dashboard Preview Mode (renders typeChart & priorityChart on main dashboard)
            renderTypeChart('typeChart', data.by_type);
            renderPriorityChart('priorityChart', data.by_priority);
        } else {
            // Full Analytics View Mode (renders all 4 required charts)
            renderTypeChart('typeChartFull', data.by_type);
            renderPriorityChart('priorityChartFull', data.by_priority);
            renderHourlyChart('hourlyChartFull', data.by_hour);
            renderResponseTimeChart('responseTimeChartFull', data.resp_by_priority);
        }
    }

    /**
     * Chart 1: Emergency Requests by Type (Bar Chart)
     */
    function renderTypeChart(canvasId, typeData) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        if (chartInstances[canvasId]) {
            chartInstances[canvasId].destroy();
        }

        const labels = typeData.map(d => d.emergency_type);
        const counts = typeData.map(d => d.count);

        chartInstances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Emergency Incidents',
                    data: counts,
                    backgroundColor: [
                        '#ef4444',
                        '#3b82f6',
                        '#f97316',
                        '#10b981',
                        '#8b5cf6'
                    ],
                    borderRadius: 6,
                    borderWidth: 1,
                    borderColor: 'rgba(0,0,0,0.05)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ` Incidents: ${ctx.raw}`
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }

    /**
     * Chart 2: Priority Distribution (Doughnut Chart)
     */
    function renderPriorityChart(canvasId, priorityData) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        if (chartInstances[canvasId]) {
            chartInstances[canvasId].destroy();
        }

        const labels = priorityData.map(d => d.label);
        const counts = priorityData.map(d => d.count);
        const bgColors = priorityData.map(d => {
            if (d.priority === 1) return colors.p1;
            if (d.priority === 2) return colors.p2;
            if (d.priority === 3) return colors.p3;
            return colors.p4;
        });

        chartInstances[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: counts,
                    backgroundColor: bgColors,
                    hoverOffset: 8,
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '62%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 12,
                            padding: 12,
                            font: { family: 'Inter', size: 11, weight: '600' }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ` ${ctx.label}: ${ctx.raw} requests`
                        }
                    }
                }
            }
        });
    }

    /**
     * Chart 3: Requests by Hour of the Day (Line Chart)
     */
    function renderHourlyChart(canvasId, hourlyData) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        if (chartInstances[canvasId]) {
            chartInstances[canvasId].destroy();
        }

        // Fill full 24-hour spectrum or active hours
        const activeHours = new Map(hourlyData.map(d => [d.hour, d.count]));
        const hoursLabels = [];
        const hourCounts = [];

        // Generate hours from 06:00 to 22:00 or active span
        for (let h = 0; h < 24; h++) {
            if (activeHours.has(h) || (h >= 7 && h <= 20)) {
                const label = `${h.toString().padStart(2, '0')}:00`;
                hoursLabels.push(label);
                hourCounts.push(activeHours.get(h) || 0);
            }
        }

        chartInstances[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: hoursLabels,
                datasets: [{
                    label: 'Requests by Hour',
                    data: hourCounts,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.12)',
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: '#10b981',
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }

    /**
     * Chart 4: Average Response Time by Priority (Bar Chart)
     */
    function renderResponseTimeChart(canvasId, responseData) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        if (chartInstances[canvasId]) {
            chartInstances[canvasId].destroy();
        }

        const labels = responseData.map(d => d.label);
        // Convert to seconds or minutes for display
        const timesInSeconds = responseData.map(d => d.avg_response_sec);
        const bgColors = responseData.map(d => {
            if (d.priority === 1) return colors.p1;
            if (d.priority === 2) return colors.p2;
            if (d.priority === 3) return colors.p3;
            return colors.p4;
        });

        chartInstances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Avg Response Time (seconds)',
                    data: timesInSeconds,
                    backgroundColor: bgColors,
                    borderRadius: 6,
                    borderWidth: 1,
                    borderColor: 'rgba(0,0,0,0.05)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ` Response Time: ${ctx.raw}s (${(ctx.raw / 60).toFixed(1)} mins)`
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Seconds to Dispatch'
                        }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }

    /**
     * Refreshes all charts currently rendered on page
     */
    async function refreshAllCharts() {
        const hasFull = document.getElementById('typeChartFull');
        if (hasFull) {
            await initCharts({ previewOnly: false });
        } else {
            await initCharts({ previewOnly: true });
        }
    }

    return {
        initCharts,
        refreshAllCharts
    };
})();
