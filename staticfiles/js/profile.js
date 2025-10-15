 function previewFile() {
    const preview = document.getElementById('previewImage');
    const initials = document.querySelector('.initials');
    const file = document.getElementById('profileImage').files[0];
    const reader = new FileReader();

    reader.onloadend = function() {
        preview.src = reader.result;
        preview.style.display = 'block';
        initials.style.display = 'none';
    }

    if (file) {
        reader.readAsDataURL(file);
    } else {
        preview.src = '';
        preview.style.display = 'none';
        initials.style.display = 'block';
    }
}