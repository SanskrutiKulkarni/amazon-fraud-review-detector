function submitReview() {
    const reviewText = document.getElementById("reviewText").value.trim();
    const captchaToken = grecaptcha.getResponse();

    const resultDiv = document.getElementById("result");
    resultDiv.innerHTML = "";
    resultDiv.style.color = "#333";

    if (!reviewText) {
        alert("Please enter your review");
        return;
    }

    if (!captchaToken) {
        resultDiv.innerHTML = "⚠️ Please complete the CAPTCHA.";
        resultDiv.style.color = "#e67e22";
        return;
    }

    resultDiv.innerHTML = "<p>Processing your review...</p>";

    fetch("/submit-review", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            text: reviewText,
            captcha: captchaToken
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'published') {
            resultDiv.innerHTML = `
                <p>✅ Published successfully!</p>
                <p class="status-badge badge-published">VERIFIED REVIEW</p>
            `;
            resultDiv.style.color = "#27ae60";
        } else {
            resultDiv.innerHTML = `
                <p>❌ ${data.reason || "Not published."}</p>
                <p>Confidence: ${(data.confidence * 100).toFixed(1)}%</p>
                <p>Status: ${data.status ? data.status.toUpperCase() : "UNKNOWN"}</p>
            `;
            resultDiv.style.color = data.status === "blocked" ? "#e74c3c" : "#f39c12";
        }
        document.getElementById("reviewText").value = "";
        grecaptcha.reset(); // Reset CAPTCHA
    })
    .catch(error => {
        console.error("Error:", error);
        resultDiv.innerHTML = "❌ Error submitting review. Please try again.";
        resultDiv.style.color = "#e74c3c";
        grecaptcha.reset(); // Also reset CAPTCHA in case of error
    });
}
