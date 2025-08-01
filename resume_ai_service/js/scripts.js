document.addEventListener("DOMContentLoaded", function () {

    // Form validation
    const contactForm = document.getElementById("contactForm");

    contactForm.addEventListener("submit", function (e) {
        e.preventDefault(); // Prevent form from submitting immediately

        // Get input values
        const name = document.getElementById("name").value.trim();
        const email = document.getElementById("email").value.trim();
        const message = document.getElementById("message").value.trim();

        // Validate fields
        if (name === "" || email === "" || message === "") {
            alert("Please fill in all fields.");
            return;
        }

        // Basic email format validation
        const emailPattern = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
        if (!emailPattern.test(email)) {
            alert("Please enter a valid email address.");
            return;
        }

        // Optionally, you can send the data to Flask via AJAX or just allow the form to submit
        contactForm.submit(); // Proceed to submit the form to Flask backend
    });

    // Optional: Add smooth scroll behavior for anchor links
    const anchorLinks = document.querySelectorAll("a[href^='#']");
    for (let anchor of anchorLinks) {
        anchor.addEventListener("click", function (e) {
            e.preventDefault();
            const targetId = anchor.getAttribute("href").slice(1);
            document.getElementById(targetId).scrollIntoView({
                behavior: "smooth",
                block: "start",
            });
        });
    }
});
