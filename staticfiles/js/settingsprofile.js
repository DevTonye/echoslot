// client_profile_form.js

function triggerFileInput() {
    const realFileInput = document.querySelector('input[name="profile_image"]');
    if (realFileInput) {
        realFileInput.click();
    }
}

function previewImage(event) {
    const fileInput = event.target;
    const file = fileInput.files && fileInput.files[0];

    const imagePreview = document.getElementById("imagePreview");
    const imagePlaceholder = document.getElementById("imagePlaceholder");

    if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
            imagePreview.src = e.target.result;
            imagePreview.style.display = "block";
            if (imagePlaceholder) {
                imagePlaceholder.style.display = "none";
            }
        };
        reader.readAsDataURL(file);
    }
}

// Register the event listener after the DOM loads
document.addEventListener('DOMContentLoaded', function () {
    const fileInput = document.querySelector('input[name="profile_image"]');
    if (fileInput) {
        fileInput.addEventListener('change', previewImage);
    }
});
