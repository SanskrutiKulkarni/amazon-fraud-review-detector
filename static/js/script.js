function submitReview() {
    const text = document.getElementById('reviewText').value.trim();
    if (!text) {
        alert('Please enter your review');
        return;
    }

    const resultDiv = document.getElementById('result');
    resultDiv.innerHTML = '<p>Processing your review...</p>';
    resultDiv.style.color = '#333';

    fetch('/submit-review', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: text })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'published') {
            resultDiv.innerHTML = `
                <p>✅ Published successfully!</p>
                <p class="status-badge badge-published">VERIFIED REVIEW</p>
            `;
            resultDiv.style.color = '#27ae60';
        } else {
            resultDiv.innerHTML = `
                <p>❌ ${data.reason}</p>
                <p>Confidence: ${(data.confidence * 100).toFixed(1)}%</p>
                <p>Status: ${data.status.toUpperCase()}</p>
            `;
            resultDiv.style.color = data.status === 'blocked' ? '#e74c3c' : '#f39c12';
        }
        document.getElementById('reviewText').value = '';
    })
    .catch(error => {
        resultDiv.innerHTML = 'Error submitting review. Please try again.';
        resultDiv.style.color = '#e74c3c';
        console.error('Error:', error);
    });
}