document.addEventListener('DOMContentLoaded', () => {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const uploadProgress = document.getElementById('upload-progress');

    uploadArea.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => uploadArea.classList.add('highlight'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => uploadArea.classList.remove('highlight'), false);
    });

    uploadArea.addEventListener('drop', (e) => {
        handleFiles(e.dataTransfer.files);
    });

    function handleFiles(files) {
        if (files.length === 0) return;

        if (files.length === 1) {
            uploadFile(files[0]);
        } else {
            uploadBatch(files);
        }
    }

    async function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/v1/resumes/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            if (response.ok) {
                displayProgress(result);
            } else {
                displayError(result.detail);
            }
        } catch (error) {
            displayError('An error occurred during upload.');
        }
    }

    async function uploadBatch(files) {
        const formData = new FormData();
        for (const file of files) {
            formData.append('files', file);
        }

        try {
            const response = await fetch('/api/v1/resumes/upload-batch', {
                method: 'POST',
                body: formData
            });

            const results = await response.json();
            if (response.ok) {
                results.forEach(result => displayProgress(result));
            } else {
                displayError(results.detail);
            }
        } catch (error) {
            displayError('An error occurred during batch upload.');
        }
    }

    function displayProgress(result) {
        const progressElement = document.createElement('div');
        progressElement.className = 'progress-item';
        progressElement.innerHTML = `<p>${result.file_name} - <span>${result.status}</span></p>`;
        uploadProgress.appendChild(progressElement);

        if (result.status === 'processing') {
            pollJobStatus(result.job_id, progressElement);
        }
    }

    function displayError(message) {
        const errorElement = document.createElement('div');
        errorElement.className = 'error-item';
        errorElement.textContent = message;
        uploadProgress.appendChild(errorElement);
    }

    async function pollJobStatus(jobId, element) {
        const interval = setInterval(async () => {
            try {
                const response = await fetch(`/api/v1/resumes/jobs/${jobId}`);
                const result = await response.json();

                if (response.ok) {
                    element.querySelector('span').textContent = result.status;
                    if (result.status === 'completed' || result.status === 'failed') {
                        clearInterval(interval);
                    }
                } else {
                    clearInterval(interval);
                }
            } catch (error) {
                clearInterval(interval);
            }
        }, 2000);
    }
});
