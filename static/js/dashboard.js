// Global chart references
let statsChart, botChart;

// Load all data on page load
document.addEventListener('DOMContentLoaded', function() {
    loadQuarantinedReviews();
    loadStats();
    loadBotAnalytics();
});

// Load quarantined reviews
async function loadQuarantinedReviews() {
    try {
        const response = await fetch('/get-quarantined');
        const reviews = await response.json();
        
        const tableBody = document.querySelector('#quarantineTable tbody');
        tableBody.innerHTML = '';
        
        reviews.forEach(review => {
            const row = document.createElement('tr');
            row.dataset.reason = review.reason.toLowerCase();
            
            row.innerHTML = `
                <td>${review.id}</td>
                <td>${review.text.length > 50 ? review.text.substring(0, 50) + '...' : review.text}</td>
                <td>${review.reason}</td>
                <td>${(review.confidence * 100).toFixed(1)}%</td>
                <td>
                    <button onclick="approveReview(${review.id})">Approve</button>
                    <button class="reject-btn" onclick="rejectReview(${review.id})">Reject</button>
                </td>
            `;
            
            tableBody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading quarantined reviews:', error);
    }
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch('/stats');
        const data = await response.json();
        
        const ctx = document.getElementById('statsChart').getContext('2d');
        
        if (statsChart) statsChart.destroy();
        
        statsChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(data.status_distribution),
                datasets: [{
                    data: Object.values(data.status_distribution),
                    backgroundColor: [
                        '#2ecc71', '#e74c3c', '#f39c12'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Review Status Distribution'
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load bot analytics
async function loadBotAnalytics() {
    try {
        const response = await fetch('/bot-analytics');
        const data = await response.json();
        
        const ctx = document.getElementById('botChart').getContext('2d');
        
        if (botChart) botChart.destroy();
        
        botChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(data.detection_types),
                datasets: [{
                    label: 'Bot Detections',
                    data: Object.values(data.detection_types),
                    backgroundColor: '#3498db'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Bot Detection Types'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading bot analytics:', error);
    }
}

// Filter reviews
function filterReviews(type) {
    const rows = document.querySelectorAll('#quarantineTable tbody tr');
    rows.forEach(row => {
        const show = type === 'all' || 
                    (type === 'ai' && row.dataset.reason.includes('ai')) ||
                    (type === 'paid' && (row.dataset.reason.includes('paid') || row.dataset.reason.includes('incentivized'))) ||
                    (type === 'bot' && row.dataset.reason.includes('bot'));
        row.style.display = show ? '' : 'none';
    });
}

// Approve review (mock implementation)
async function approveReview(id) {
    if (confirm(`Approve review #${id}?`)) {
        alert(`Review #${id} approved (in real system, this would call your backend)`);
        await loadQuarantinedReviews();
    }
}

// Reject review (mock implementation)
async function rejectReview(id) {
    if (confirm(`Permanently reject review #${id}?`)) {
        alert(`Review #${id} rejected (in real system, this would call your backend)`);
        await loadQuarantinedReviews();
    }
}