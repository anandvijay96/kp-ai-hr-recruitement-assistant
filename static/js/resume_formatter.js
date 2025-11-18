document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('resumeFormatterForm');
    const submitBtn = document.getElementById('rfSubmitBtn');
    const spinner = document.getElementById('rfSpinner');
    const statusEl = document.getElementById('rfFormStatus');
    const resultsEl = document.getElementById('rfResults');
    const templateSelect = document.getElementById('rfTemplateId');
    const templateDescription = document.getElementById('rfTemplateDescription');

    if (!form) {
        return;
    }

    const setLoading = (isLoading, message = '') => {
        if (isLoading) {
            submitBtn.disabled = true;
            spinner.classList.remove('d-none');
            statusEl.textContent = message || 'Processing resumes...';
        } else {
            submitBtn.disabled = false;
            spinner.classList.add('d-none');
            statusEl.textContent = message || '';
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

    const renderTemplates = (templates) => {
        // Reset options (keep placeholder)
        while (templateSelect.options.length > 1) {
            templateSelect.remove(1);
        }

        templates.forEach((t) => {
            const opt = document.createElement('option');
            opt.value = t.id;
            opt.textContent = t.name;
            opt.dataset.description = t.description || '';
            templateSelect.appendChild(opt);
        });

        // Auto-select the first real template (index 1) as default
        if (templates.length > 0 && templateSelect.options.length > 1) {
            templateSelect.selectedIndex = 1;
            const first = templateSelect.options[1];
            templateDescription.textContent = first && first.dataset.description
                ? first.dataset.description
                : '';
        }
    };

    const loadTemplates = async () => {
        try {
            setLoading(true, 'Loading templates...');
            const resp = await fetch('/api/v1/resume-formatter/templates');
            if (resp.status === 401) {
                window.location.href = '/login';
                return;
            }
            if (!resp.ok) {
                showError('Failed to load templates for Resume Formatter.');
                setLoading(false, '');
                return;
            }
            const data = await resp.json();
            renderTemplates(data.templates || []);
            setLoading(false, '');
        } catch (err) {
            console.error('Error loading templates', err);
            showError('Unexpected error while loading templates.');
            setLoading(false, '');
        }
    };

    templateSelect.addEventListener('change', () => {
        const selected = templateSelect.options[templateSelect.selectedIndex];
        const desc = selected && selected.dataset.description ? selected.dataset.description : '';
        templateDescription.textContent = desc;
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const clientName = document.getElementById('rfClientName').value.trim();
        const templateId = templateSelect.value;
        const filesInput = document.getElementById('rfResumeFiles');

        if (!clientName) {
            showError('Please enter the client name.');
            return;
        }
        if (!templateId) {
            showError('Please select a template.');
            return;
        }
        if (!filesInput.files || filesInput.files.length === 0) {
            showError('Please upload at least one resume file.');
            return;
        }

        const formData = new FormData();
        formData.append('client_name', clientName);
        formData.append('template_id', templateId);

        // Optional fields (ignored by current stub API but sent for future compatibility)
        const jdText = document.getElementById('rfJdText').value.trim();
        const jdFile = document.getElementById('rfJdFile');
        const instructions = document.getElementById('rfInstructions').value;

        if (jdText) {
            formData.append('jd_text', jdText);
        }
        if (jdFile.files && jdFile.files[0]) {
            formData.append('jd_file', jdFile.files[0]);
        }
        if (instructions && instructions.trim()) {
            formData.append('instructions', instructions);
        }

        Array.from(filesInput.files).forEach((file) => {
            formData.append('files', file);
        });

        setLoading(true, 'Submitting resumes to formatter...');

        try {
            const resp = await fetch('/api/v1/resume-formatter/from-uploads', {
                method: 'POST',
                body: formData,
            });

            if (resp.status === 401) {
                window.location.href = '/login';
                return;
            }

            const data = await resp.json().catch(() => null);

            if (!resp.ok) {
                const msg = (data && data.detail) ? data.detail : 'Failed to format resumes.';
                showError(msg);
                setLoading(false, '');
                return;
            }

            const resumes = (data && Array.isArray(data.resumes)) ? data.resumes : [];

            resultsEl.classList.remove('text-muted');

            if (!resumes.length) {
                resultsEl.innerHTML = `
                    <div>
                        <p class="mb-0">No formatted resumes were returned by the formatter.</p>
                    </div>
                `;
            } else {
                const itemsHtml = resumes.map((r, index) => {
                    const safeName = r.candidate_name || r.original_filename || `Resume ${index + 1}`;
                    const docxLink = r.docx_url
                        ? `<a href="${r.docx_url}" class="btn btn-sm btn-outline-primary" target="_blank" rel="noopener">Download DOCX</a>`
                        : '<span class="text-muted small">DOCX link unavailable</span>';
                    const pdfLink = r.pdf_url
                        ? `<a href="${r.pdf_url}" class="btn btn-sm btn-outline-secondary ms-2" target="_blank" rel="noopener">Download PDF</a>`
                        : '';

                    return `
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <div><strong>${safeName}</strong></div>
                                <div class="small text-muted">${r.original_filename || ''}</div>
                            </div>
                            <div>
                                ${docxLink}
                                ${pdfLink}
                            </div>
                        </li>
                    `;
                }).join('');

                resultsEl.innerHTML = `
                    <div>
                        <p class="mb-2"><strong>Formatted resumes</strong> for client <strong>${clientName}</strong> (${resumes.length} file${resumes.length > 1 ? 's' : ''}).</p>
                        <ul class="list-group list-group-flush">
                            ${itemsHtml}
                        </ul>
                    </div>
                `;
            }

            showSuccess('Formatted resumes generated successfully.');
            setLoading(false, 'Ready.');
        } catch (err) {
            console.error('Error calling Resume Formatter API', err);
            showError('Unexpected error while calling Resume Formatter API.');
            setLoading(false, '');
        }
    });

    // Initial load
    loadTemplates();
});
