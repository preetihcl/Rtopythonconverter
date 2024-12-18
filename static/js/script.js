// Function to toggle password visibility
function togglePassword() {
    const passwordField = document.getElementById('openai-key');
    const passwordToggle = document.querySelector('.toggle-password');

    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        passwordToggle.textContent = '🙈'; // Change icon to hide
    } else {
        passwordField.type = 'password';
        passwordToggle.textContent = '👁️'; // Change icon to show
    }
}

// Function to set API key in sessionStorage and hidden fields before form submission
function setApiKeyInHiddenFields() {
    const passwordInput = document.getElementById('openai-key');
    const enteredKey = passwordInput.value.trim();

    if (!enteredKey) {
        alert("Please provide your OpenAI API key.");
        return false; // Prevent form submission if key is not entered
    }

    // Save the entered API key in sessionStorage
    sessionStorage.setItem('openai_api_key', enteredKey);

    // Set the hidden input fields for the forms
    document.getElementById('openai-key-hidden').value = enteredKey;
    document.getElementById('openai-key-hidden-right').value = enteredKey;

    return true; // Allow form submission
}

// Event listener for form submissions
document.getElementById('converter-form').onsubmit = function (event) {
    if (!setApiKeyInHiddenFields()) {
        event.preventDefault(); // Prevent submission if no key is set
    }
};

document.getElementById('file-upload-form').onsubmit = function (event) {
    if (!setApiKeyInHiddenFields()) {
        event.preventDefault(); // Prevent submission if no key is set
    }
};

// Reload stored API key into the password field on page load
window.onload = function () {
    const passwordField = document.getElementById('openai-key');
    const storedApiKey = sessionStorage.getItem('openai_api_key');

    if (storedApiKey) {
        passwordField.value = storedApiKey; // Restore key for re-use in current session
    }
};