// Global chart references
let statsChart, rejectionChart, dailyChart, botChart;

// Load all data on page load
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    document.getElementById('refreshBtn').addEventListener('click', loadDashboardData);
});

// Load all dashboard data
async function loadDashboardData() {
    try {
        const response = await fetch('/dashboard-data');
        const data = await response.json();
        
        // Update stat cards
        document.getElementById('totalReviews').textContent = 
            data.stats.status_distribution.approved + 
            data.stats.status_distribution.quarantined + 
            data.stats.status_distribution.blocked;
        
        document.getElementById('approvedReviews').textContent = data.stats.status_distribution.approved;
        document.getElementById('quarantinedReviews').textContent = data.stats.status_distribution.quarantined;
        document.getElementById('blockedReviews').textContent = data.stats.status_distribution.blocked;
        
        // Render charts
        renderStatsChart(data);
        renderRejectionChart(data);
        renderDailyChart(data);
        renderBotChart(data);
        
        // Load quarantined reviews
        renderQuarantinedReviews(data.quarantined);
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        alert('Failed to load dashboard data. Please try again.');
    }
}

// Render stats chart
function renderStatsChart(data) {
    const ctx = document.getElementById('statsChart').getContext('2d');
    
    if (statsChart) statsChart.destroy();
    
    statsChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Approved', 'Quarantined', 'Blocked'],
            datasets: [{
                data: [
                    data.stats.status_distribution.approved,
                    data.stats.status_distribution.quarantined,
                    data.stats.status_distribution.blocked
                ],
                backgroundColor: [
                    '#2ecc71', // green
                    '#f39c12', // orange
                    '#e74c3c'  // red
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            cutout: '70%'
        }
    });
}

// Render rejection reasons chart
function renderRejectionChart(data) {
    const ctx = document.getElementById('rejectionChart').getContext('2d');
    
    if (rejectionChart) rejectionChart.destroy();
    
    rejectionChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: [
                'AI Content', 
                'Paid Review', 
                'Bot Detected', 
                'CAPTCHA Failed',
                'Suspicious Activity'
            ],
            datasets: [{
                data: [
                    data.stats.rejection_reasons.ai_rejections,
                    data.stats.rejection_reasons.paid_rejections,
                    data.stats.rejection_reasons.bot_rejections,
                    data.stats.rejection_reasons.captcha_rejections,
                    data.stats.rejection_reasons.activity_rejections
                ],
                backgroundColor: [
                    '#3498db',
                    '#9b59b6',
                    '#1abc9c',
                    '#e67e22',
                    '#95a5a6'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Render daily activity chart
function renderDailyChart(data) {
    const ctx = document.getElementById('dailyChart').getContext('2d');
    
    if (dailyChart) dailyChart.destroy();
    
    dailyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.stats.daily_activity.map(d => d.day),
            datasets: [
                {
                    label: 'Approved',
                    data: data.stats.daily_activity.map(d => d.approved),
                    borderColor: '#2ecc71',
                    backgroundColor: 'rgba(46, 204, 113, 0.1)',
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Quarantined',
                    data: data.stats.daily_activity.map(d => d.quarantined),
                    borderColor: '#f39c12',
                    backgroundColor: 'rgba(243, 156, 18, 0.1)',
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Blocked',
                    data: data.stats.daily_activity.map(d => d.blocked),
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    tension: 0.3,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Render bot chart
function renderBotChart(data) {
    const ctx = document.getElementById('botChart').getContext('2d');
    
    if (botChart) botChart.destroy();
    
    botChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(data.bot_stats.detection_types),
            datasets: [{
                label: 'Bot Detections',
                data: Object.values(data.bot_stats.detection_types),
                backgroundColor: '#3498db'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Render quarantined reviews
function renderQuarantinedReviews(reviews) {
    const tableBody = document.querySelector('#quarantineTable tbody');
    tableBody.innerHTML = '';
    
    reviews.forEach(review => {
        const row = document.createElement('tr');
        row.dataset.reason = review.reason.toLowerCase();
        
        // Format date
        const date = new Date(review.timestamp);
        const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        
        row.innerHTML = `
            <td>${review.id}</td>
            <td title="${review.text}">
                ${review.text.length > 50 ? review.text.substring(0, 50) + '...' : review.text}
            </td>
            <td>${review.reason}</td>
            <td>${(review.confidence * 100).toFixed(1)}%</td>
            <td>${formattedDate}</td>
            <td class="actions">
                <button class="approve-btn" onclick="approveReview(${review.id})">Approve</button>
                <button class="reject-btn" onclick="rejectReview(${review.id})">Reject</button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Filter reviews
function filterReviews(type) {
    // Update active filter button
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.textContent.toLowerCase().includes(type) || (type === 'all' && btn.textContent === 'All')) {
            btn.classList.add('active');
        }
    });
    
    // Filter rows
    const rows = document.querySelectorAll('#quarantineTable tbody tr');
    rows.forEach(row => {
        const show = type === 'all' || 
                    (type === 'ai' && row.dataset.reason.includes('ai')) ||
                    (type === 'paid' && (row.dataset.reason.includes('paid') || row.dataset.reason.includes('incentivized'))) ||
                    (type === 'bot' && row.dataset.reason.includes('bot'));
        row.style.display = show ? '' : 'none';
    });
}

// Approve review
async function approveReview(id) {
    if (confirm(`Approve review #${id}? This will make it publicly visible.`)) {
        try {
            const response = await fetch(`/approve-review/${id}`, {
                method: 'POST'
            });
            
            if (response.ok) {
                alert('Review approved successfully!');
                loadDashboardData();
            } else {
                throw new Error('Failed to approve review');
            }
        } catch (error) {
            console.error('Error approving review:', error);
            alert('Failed to approve review. Please try again.');
        }
    }
}

// Reject review
async function rejectReview(id) {
    if (confirm(`Permanently reject review #${id}? This cannot be undone.`)) {
        try {
            const response = await fetch(`/reject-review/${id}`, {
                method: 'POST'
            });
            
            if (response.ok) {
                alert('Review rejected successfully!');
                loadDashboardData();
            } else {
                throw new Error('Failed to reject review');
            }
        } catch (error) {
            console.error('Error rejecting review:', error);
            alert('Failed to reject review. Please try again.');
        }
    }
}