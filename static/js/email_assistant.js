document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('emailAssistantForm');
    const generateBtn = document.getElementById('generateEmailBtn');
    const spinner = document.getElementById('generateSpinner');
    const formStatus = document.getElementById('formStatus');

    // Multi-step loading state controller
    let loadingStagesTimer = null;
    const loadingStages = [
        'Step 1 of 3: Uploading resumes and job description...',
        'Step 2 of 3: Extracting text from resumes and JD...',
        'Step 3 of 3: Generating email draft with AI...'
    ];

    const subjectOutput = document.getElementById('subjectOutput');
    const bodyPreview = document.getElementById('bodyPreview');
    const tablePreview = document.getElementById('tablePreview');
    const bodyTextRaw = document.getElementById('bodyTextRaw');
    const tableHtmlRaw = document.getElementById('tableHtmlRaw');

    const copySubjectBtn = document.getElementById('copySubjectBtn');
    const copyBodyBtn = document.getElementById('copyBodyBtn');
    const copyTableBtn = document.getElementById('copyTableBtn');
    const copyTableHtmlBtn = document.getElementById('copyTableHtmlBtn');

    if (!form) {
        return;
    }

    const setLoading = (isLoading, message = '') => {
        if (isLoading) {
            generateBtn.disabled = true;
            spinner.classList.remove('d-none');

            // Reset any previous staged timer
            if (loadingStagesTimer) {
                clearInterval(loadingStagesTimer);
                loadingStagesTimer = null;
            }

            let stageIndex = 0;
            formStatus.textContent = message || loadingStages[stageIndex];

            // Progressively update the status text while the request is in flight
            loadingStagesTimer = setInterval(() => {
                if (stageIndex < loadingStages.length - 1) {
                    stageIndex += 1;
                    formStatus.textContent = loadingStages[stageIndex];
                }
            }, 3500);
        } else {
            generateBtn.disabled = false;
            spinner.classList.add('d-none');

            if (loadingStagesTimer) {
                clearInterval(loadingStagesTimer);
                loadingStagesTimer = null;
            }

            formStatus.textContent = message || '';
        }
    };

    const showError = (msg) => {
        if (window.customModal) {
            window.customModal.error(msg);
        } else {
            console.error(msg);
        }
    };

    const showSuccess = (msg) => {
        if (window.customModal) {
            window.customModal.success(msg);
        }
    };

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const clientName = document.getElementById('clientName').value.trim();
        const resumesInput = document.getElementById('resumeFiles');
        const jdText = document.getElementById('jobDescriptionText').value.trim();
        const jdFile = document.getElementById('jobDescriptionFile');
        const rateCard = document.getElementById('rateCard') ? document.getElementById('rateCard').value.trim() : '';
        const noticePeriod = document.getElementById('noticePeriod') ? document.getElementById('noticePeriod').value.trim() : '';
        const locationValue = document.getElementById('location') ? document.getElementById('location').value.trim() : '';
        const detailedSummaries = document.getElementById('detailedSummaries') ? document.getElementById('detailedSummaries').checked : false;
        const promptHintEl = document.getElementById('promptHint');
        const promptHint = promptHintEl ? promptHintEl.value.trim() : '';

        if (!clientName) {
            showError('Please enter the client name.');
            return;
        }

        if (!resumesInput.files || resumesInput.files.length === 0) {
            showError('Please upload at least one resume file.');
            return;
        }

        if (!jdText && (!jdFile.files || jdFile.files.length === 0)) {
            showError('Please provide the job description text or upload a JD file.');
            return;
        }

        const formData = new FormData();
        formData.append('client_name', clientName);
        formData.append('requirement_title', document.getElementById('requirementTitle').value.trim());
        formData.append('job_code', document.getElementById('jobCode').value.trim());
        formData.append('job_description_text', jdText);

        if (jdFile.files && jdFile.files[0]) {
            formData.append('job_description_file', jdFile.files[0]);
        }

        const includeTableSingle = document.getElementById('includeTableSingle').checked;
        if (includeTableSingle) {
            formData.append('include_table_for_single', 'true');
        }

        const signature = document.getElementById('signature').value;
        if (signature && signature.trim()) {
            formData.append('signature', signature);
        }

        if (rateCard) {
            formData.append('rate_card', rateCard);
        }

        if (noticePeriod) {
            formData.append('notice_period', noticePeriod);
        }

        if (locationValue) {
            formData.append('location', locationValue);
        }

        if (detailedSummaries) {
            formData.append('detailed_summaries', 'true');
        }

        if (promptHint) {
            formData.append('prompt_hint', promptHint);
        }

        // Append resume files
        Array.from(resumesInput.files).forEach((file) => {
            formData.append('files', file);
        });

        // Start staged loading messages while the backend processes the request
        setLoading(true);

        try {
            const response = await fetch('/api/v1/email-drafts/from-uploads', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                const message = (errorData && errorData.detail) ? errorData.detail : 'Failed to generate email draft.';
                showError(message);
                setLoading(false, '');
                return;
            }

            const data = await response.json();

            subjectOutput.value = data.subject || '';
            bodyPreview.innerHTML = data.body_html || '';
            tablePreview.innerHTML = data.candidates_table_html || '<span class="text-muted">No table generated for this request.</span>';

            bodyTextRaw.value = data.body_text || '';
            tableHtmlRaw.value = data.candidates_table_html || '';

            showSuccess('Email draft generated successfully.');
            setLoading(false, 'Ready.');
        } catch (err) {
            console.error('Error generating email draft', err);
            showError('An unexpected error occurred while generating the email draft.');
            setLoading(false, '');
        }
    });

    const copyToClipboard = async (value, emptyMessage) => {
        const text = (value || '').toString();
        if (!text.trim()) {
            if (emptyMessage) {
                showError(emptyMessage);
            }
            return;
        }
        try {
            await navigator.clipboard.writeText(text);
            showSuccess('Copied to clipboard.');
        } catch (err) {
            console.error('Clipboard error', err);
            showError('Unable to copy to clipboard.');
        }
    };

    const copyHtmlToClipboard = async (html, emptyMessage) => {
        const content = (html || '').toString().trim();
        if (!content) {
            if (emptyMessage) {
                showError(emptyMessage);
            }
            return;
        }

        // Prefer rich HTML copy when supported by the browser
        try {
            if (navigator.clipboard && navigator.clipboard.write && window.ClipboardItem) {
                const blob = new Blob([content], { type: 'text/html' });
                const item = new ClipboardItem({ 'text/html': blob });
                await navigator.clipboard.write([item]);
                showSuccess('Copied to clipboard.');
                return;
            }
        } catch (err) {
            console.error('Rich clipboard error', err);
            // Fall through to plain-text copy below
        }

        // Fallback: plain-text copy (previous behaviour)
        await copyToClipboard(content, emptyMessage);
    };

    copySubjectBtn.addEventListener('click', () => {
        copyToClipboard(subjectOutput.value, 'No subject to copy yet.');
    });

    copyBodyBtn.addEventListener('click', () => {
        copyToClipboard(bodyTextRaw.value || bodyPreview.innerText, 'No email body to copy yet.');
    });

    copyTableBtn.addEventListener('click', () => {
        const html = tableHtmlRaw.value || tablePreview.innerHTML;
        copyHtmlToClipboard(html, 'No candidate table to copy yet.');
    });

    if (copyTableHtmlBtn) {
        copyTableHtmlBtn.addEventListener('click', () => {
            // Old behaviour: copy raw HTML as plain text so it can be inspected or pasted as code
            const html = tableHtmlRaw.value || tablePreview.innerHTML;
            copyToClipboard(html, 'No candidate table HTML to copy yet.');
        });
    }
});
