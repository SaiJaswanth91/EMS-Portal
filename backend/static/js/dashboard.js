/**
 * EELMS Dashboard Chart.js Integration
 * Handles responsive chart rendering & empty state fallbacks
 */

document.addEventListener('DOMContentLoaded', function () {
    // Helper function to check if array has non-zero data
    function hasData(arr) {
        return Array.isArray(arr) && arr.length > 0 && arr.some(function(v) { return Number(v) > 0; });
    }

    // 1. Attendance Breakdown Chart
    const attEl = document.getElementById('attendance-breakdown-data');
    if (attEl) {
        try {
            const attData = JSON.parse(attEl.textContent);
            const canvas = document.getElementById('attendanceBreakdownChart');
            if (canvas && hasData(attData.data)) {
                new Chart(canvas, {
                    type: 'doughnut',
                    data: {
                        labels: attData.labels,
                        datasets: [{
                            data: attData.data,
                            backgroundColor: ['#22c55e', '#f59e0b', '#06b6d4', '#3b82f6', '#ef4444'],
                            borderWidth: 2,
                            borderColor: '#ffffff'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'bottom' }
                        }
                    }
                });
            } else if (canvas) {
                const container = canvas.parentElement;
                container.innerHTML = '<div class="text-center text-muted py-5"><i class="bi bi-pie-chart fs-1 opacity-50 d-block mb-2"></i>No attendance data recorded today.</div>';
            }
        } catch (e) {
            console.error("Error parsing attendance breakdown chart data:", e);
        }
    }

    // 2. Department Distribution Chart
    const deptEl = document.getElementById('dept-distribution-data');
    if (deptEl) {
        try {
            const deptData = JSON.parse(deptEl.textContent);
            const canvas = document.getElementById('deptDistributionChart');
            if (canvas && hasData(deptData.data)) {
                new Chart(canvas, {
                    type: 'bar',
                    data: {
                        labels: deptData.labels,
                        datasets: [{
                            label: 'Active Employees',
                            data: deptData.data,
                            backgroundColor: '#3b82f6',
                            borderRadius: 6
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: { beginAtZero: true, ticks: { precision: 0 } }
                        },
                        plugins: {
                            legend: { display: false }
                        }
                    }
                });
            } else if (canvas) {
                const container = canvas.parentElement;
                container.innerHTML = '<div class="text-center text-muted py-5"><i class="bi bi-bar-chart fs-1 opacity-50 d-block mb-2"></i>No department distribution data available.</div>';
            }
        } catch (e) {
            console.error("Error parsing department chart data:", e);
        }
    }

    // 3. Attendance / Hours Trend Chart
    const trendEl = document.getElementById('attendance-trend-data');
    if (trendEl) {
        try {
            const trendData = JSON.parse(trendEl.textContent);
            const canvas = document.getElementById('attendanceTrendChart');
            if (canvas && trendData.data) {
                new Chart(canvas, {
                    type: 'line',
                    data: {
                        labels: trendData.labels,
                        datasets: [{
                            label: 'Count / Working Hours',
                            data: trendData.data,
                            borderColor: '#2563eb',
                            backgroundColor: 'rgba(37, 99, 235, 0.1)',
                            fill: true,
                            tension: 0.3,
                            pointRadius: 4,
                            pointHoverRadius: 6
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: { beginAtZero: true }
                        },
                        plugins: {
                            legend: { display: false }
                        }
                    }
                });
            }
        } catch (e) {
            console.error("Error parsing attendance trend chart data:", e);
        }
    }
});
