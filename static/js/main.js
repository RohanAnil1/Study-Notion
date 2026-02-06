// Study-Notion Main JavaScript

document.addEventListener('DOMContentLoaded', function () {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add fade-in animation to cards
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.card, .feature-card').forEach(card => {
        observer.observe(card);
    });

    // Video progress tracking (if on video player page)
    const videoPlayer = document.querySelector('.video-container iframe');
    if (videoPlayer) {
        // Track video watch time
        let watchTime = 0;
        const interval = setInterval(() => {
            watchTime += 1;
            // Could send AJAX request to update progress
        }, 1000);

        // Clean up on page unload
        window.addEventListener('beforeunload', () => {
            clearInterval(interval);
        });
    }

    // Form validation enhancement
    const forms = document.querySelectorAll('form[method="POST"]');
    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Quiz timer (if on quiz page)
    const quizForm = document.querySelector('form[action*="submit_quiz"]');
    if (quizForm) {
        let startTime = Date.now();
        quizForm.addEventListener('submit', function () {
            const timeSpent = Math.floor((Date.now() - startTime) / 1000);
            console.log(`Quiz completed in ${timeSpent} seconds`);
        });
    }

    // Tooltip initialization (Bootstrap 5)
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Popover initialization (Bootstrap 5)
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// AJAX function for progress tracking
function updateLectureProgress(lectureId, completed) {
    fetch(`/api/update-progress/${lectureId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ completed: completed })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Progress updated successfully');
            }
        })
        .catch(error => {
            console.error('Error updating progress:', error);
        });
}

// Function to mark lecture as complete
function markLectureComplete(lectureId) {
    updateLectureProgress(lectureId, true);
}
