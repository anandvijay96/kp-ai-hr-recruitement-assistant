#!/usr/bin/env python3
"""
Build the comprehensive vetting page HTML
"""

VETTING_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resume Vetting - AI HR Assistant</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <style>
        :root {
            --primary: #366092;
            --success: #28a745;
            --warning: #ffc107;
            --danger: #dc3545;
        }
        body { background: #f5f7fa; font-family: 'Segoe UI', Tahoma, sans-serif; }
        .navbar { background: linear-gradient(135deg, var(--primary) 0%, #4a90e2 100%); box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .card { border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border: none; margin-bottom: 20px; }
        .upload-zone { border: 3px dashed #dee2e6; border-radius: 12px; padding: 50px 30px; text-align: center; transition: all 0.3s; cursor: pointer; background: white; }
        .upload-zone:hover, .upload-zone.dragover { border-color: var(--primary); background: #f0f7ff; }
        .score-badge { font-size: 1.5em; font-weight: bold; padding: 8px 16px; border-radius: 8px; }
        .score-high { background: var(--success); color: white; }
        .score-medium { background: var(--warning); color: #000; }
        .score-low { background: var(--danger); color: white; }
        .resume-row { cursor: pointer; transition: all 0.2s; }
        .resume-row:hover { background: #f8f9fa; }
        .component-score { margin-bottom: 10px; }
        .progress { height: 8px; border-radius: 4px; }
        .flag-badge { font-size: 0.85em; padding: 4px 8px; margin: 2px; }
        .stats-card { text-align: center; padding: 15px; border-radius: 8px; margin: 5px; }
        .stats-total { background: #e3f2fd; color: #1976d2; }
        .stats-approved { background: #e8f5e9; color: #388e3c; }
        .stats-rejected { background: #ffebee; color: #d32f2f; }
        .stats-pending { background: #fff3e0; color: #f57c00; }
        .bulk-actions { background: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .details-panel { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-top: 10px; }
        .hidden { display: none; }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-dark mb-4">
        <div class="container-fluid">
            <a class="navbar-brand" href="/"><i class="bi bi-shield-check me-2"></i>AI HR Assistant - Resume Vetting</a>
            <div>
                <a href="/" class="btn btn-light btn-sm me-2"><i class="bi bi-house"></i> Home</a>
                <a href="/upload" class="btn btn-light btn-sm me-2"><i class="bi bi-upload"></i> Direct Upload</a>
                <a href="/candidates" class="btn btn-light btn-sm"><i class="bi bi-people"></i> Candidates</a>
            </div>
        </div>
    </nav>

    <div class="container">
        <!-- Header -->
        <div class="row mb-4">
            <div class="col-12">
                <h2><i class="bi bi-shield-shaded me-2"></i>Resume Authenticity Vetting</h2>
                <p class="text-muted">Scan resumes for authenticity before adding to database. Only approved resumes will be saved.</p>
            </div>
        </div>

        <!-- Upload Section -->
        <div class="card" id="uploadSection">
            <div class="card-body">
                <h5 class="card-title"><i class="bi bi-cloud-upload me-2"></i>Upload Resumes for Vetting</h5>
                <form id="vetForm">
                    <div class="upload-zone" id="uploadZone">
                        <input type="file" id="fileInput" multiple accept=".pdf,.doc,.docx" class="d-none">
                        <i class="bi bi-cloud-arrow-up" style="font-size: 48px; color: var(--primary);"></i>
                        <h5 class="mt-3">Drag & Drop Resumes Here</h5>
                        <p class="text-muted">or click to browse (Max 50 files, PDF/DOC/DOCX)</p>
                        <div id="fileList" class="mt-3 text-start"></div>
                    </div>
                    <div class="mt-3">
                        <label class="form-label">Job Description (Optional - for matching analysis)</label>
                        <textarea class="form-control" id="jobDescription" rows="3" placeholder="Paste job description here..."></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary btn-lg mt-3" id="scanBtn">
                        <i class="bi bi-search me-2"></i>Scan Resumes for Authenticity
                    </button>
                </form>
            </div>
        </div>

        <!-- Scanning Progress -->
        <div class="card hidden" id="scanningSection">
            <div class="card-body">
                <h5><i class="bi bi-hourglass-split me-2"></i>Scanning in Progress...</h5>
                <div class="progress mt-3">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" id="scanProgress" style="width: 0%"></div>
                </div>
                <p class="text-center mt-2" id="scanStatus">Scanning file 1 of 10...</p>
            </div>
        </div>

        <!-- Statistics -->
        <div class="row hidden" id="statsSection">
            <div class="col-md-3"><div class="stats-card stats-total"><h4 id="statTotal">0</h4><small>Total Scanned</small></div></div>
            <div class="col-md-3"><div class="stats-card stats-approved"><h4 id="statApproved">0</h4><small>Approved</small></div></div>
            <div class="col-md-3"><div class="stats-card stats-rejected"><h4 id="statRejected">0</h4><small>Rejected</small></div></div>
            <div class="col-md-3"><div class="stats-card stats-pending"><h4 id="statPending">0</h4><small>Pending Review</small></div></div>
        </div>

        <!-- Bulk Actions -->
        <div class="bulk-actions hidden" id="bulkActions">
            <div class="row align-items-center">
                <div class="col-md-6">
                    <button class="btn btn-sm btn-outline-secondary me-2" onclick="selectAll()"><i class="bi bi-check-square"></i> Select All</button>
                    <button class="btn btn-sm btn-outline-secondary me-2" onclick="deselectAll()"><i class="bi bi-square"></i> Deselect All</button>
                    <button class="btn btn-sm btn-success me-2" onclick="approveSelected()"><i class="bi bi-check-lg"></i> Approve Selected</button>
                    <button class="btn btn-sm btn-danger me-2" onclick="rejectSelected()"><i class="bi bi-x-lg"></i> Reject Selected</button>
                </div>
                <div class="col-md-6 text-end">
                    <input type="number" id="scoreThreshold" class="form-control d-inline-block" style="width: 80px;" value="70" min="0" max="100">
                    <button class="btn btn-sm btn-info me-2" onclick="approveByScore()"><i class="bi bi-filter"></i> Approve Score ≥</button>
                    <button class="btn btn-primary btn-lg" onclick="uploadApproved()"><i class="bi bi-database-add"></i> Upload Approved to Database</button>
                </div>
            </div>
        </div>

        <!-- Results Table -->
        <div class="card hidden" id="resultsSection">
            <div class="card-body">
                <h5><i class="bi bi-list-check me-2"></i>Vetting Results</h5>
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th width="50"><input type="checkbox" id="selectAllCheck" onclick="toggleSelectAll()"></th>
                                <th>Resume</th>
                                <th>Authenticity</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="resultsTableBody"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let sessionId = null;
        let scannedResumes = [];
        let selectedHashes = new Set();

        // File upload handling
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('fileInput');

        uploadZone.addEventListener('click', () => fileInput.click());
        uploadZone.addEventListener('dragover', (e) => { e.preventDefault(); uploadZone.classList.add('dragover'); });
        uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragover'));
        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            fileInput.files = e.dataTransfer.files;
            displayFileList();
        });

        fileInput.addEventListener('change', displayFileList);

        function displayFileList() {
            const files = fileInput.files;
            const fileList = document.getElementById('fileList');
            if (files.length > 0) {
                fileList.innerHTML = `<strong>${files.length} file(s) selected:</strong><br>` +
                    Array.from(files).slice(0, 5).map(f => `<small>• ${f.name}</small>`).join('<br>') +
                    (files.length > 5 ? `<br><small>... and ${files.length - 5} more</small>` : '');
            }
        }

        // Scan form submission
        document.getElementById('vetForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const files = fileInput.files;
            if (files.length === 0) { alert('Please select files'); return; }
            if (files.length > 50) { alert('Maximum 50 files allowed'); return; }

            sessionId = generateSessionId();
            await scanResumes(files);
        });

        async function scanResumes(files) {
            document.getElementById('uploadSection').classList.add('hidden');
            document.getElementById('scanningSection').classList.remove('hidden');

            const jobDesc = document.getElementById('jobDescription').value;
            let scanned = 0;

            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                const formData = new FormData();
                formData.append('file', file);
                formData.append('session_id', sessionId);
                if (jobDesc) formData.append('job_description', jobDesc);

                try {
                    document.getElementById('scanStatus').textContent = `Scanning ${file.name} (${i + 1} of ${files.length})...`;
                    const response = await fetch('/api/v1/vetting/scan', { method: 'POST', body: formData });
                    const result = await response.json();
                    scannedResumes.push(result);
                    scanned++;
                } catch (error) {
                    console.error(`Error scanning ${file.name}:`, error);
                }

                const progress = ((i + 1) / files.length) * 100;
                document.getElementById('scanProgress').style.width = progress + '%';
            }

            document.getElementById('scanningSection').classList.add('hidden');
            displayResults();
        }

        function displayResults() {
            document.getElementById('statsSection').classList.remove('hidden');
            document.getElementById('bulkActions').classList.remove('hidden');
            document.getElementById('resultsSection').classList.remove('hidden');

            const tbody = document.getElementById('resultsTableBody');
            tbody.innerHTML = '';

            scannedResumes.forEach((resume, index) => {
                const scan = resume.scan_result;
                const authScore = scan.authenticity_score.overall_score || 0;
                const scoreClass = authScore >= 80 ? 'high' : authScore >= 60 ? 'medium' : 'low';

                const row = `
                    <tr class="resume-row" data-hash="${resume.file_hash}">
                        <td><input type="checkbox" class="resume-check" data-hash="${resume.file_hash}" onchange="updateSelection('${resume.file_hash}', this.checked)"></td>
                        <td>
                            <strong>${scan.filename}</strong><br>
                            <small class="text-muted">${formatFileSize(scan.file_size)}</small>
                        </td>
                        <td>
                            <span class="score-badge score-${scoreClass}">${Math.round(authScore)}%</span><br>
                            <small>
                                Font: ${Math.round(scan.authenticity_score.font_consistency || 0)}% |
                                Grammar: ${Math.round(scan.authenticity_score.grammar_score || 0)}% |
                                LinkedIn: ${Math.round(scan.authenticity_score.linkedin_profile_score || 0)}%
                            </small><br>
                            ${scan.authenticity_score.flags && scan.authenticity_score.flags.length > 0 ?
                                `<span class="badge bg-danger flag-badge">🚩 ${scan.authenticity_score.flags.length} flags</span>` : ''}
                        </td>
                        <td id="status-${resume.file_hash}"><span class="badge bg-secondary">Pending</span></td>
                        <td>
                            <button class="btn btn-sm btn-success" onclick="approveResume('${resume.file_hash}')"><i class="bi bi-check"></i></button>
                            <button class="btn btn-sm btn-danger" onclick="rejectResume('${resume.file_hash}')"><i class="bi bi-x"></i></button>
                            <button class="btn btn-sm btn-info" onclick="toggleDetails('${resume.file_hash}')"><i class="bi bi-info-circle"></i></button>
                        </td>
                    </tr>
                    <tr class="hidden" id="details-${resume.file_hash}">
                        <td colspan="5">
                            <div class="details-panel">${generateDetailsHTML(scan)}</div>
                        </td>
                    </tr>
                `;
                tbody.innerHTML += row;
            });

            updateStats();
        }

        function generateDetailsHTML(scan) {
            const auth = scan.authenticity_score;
            return `
                <h6><i class="bi bi-clipboard-data"></i> Detailed Authenticity Analysis</h6>
                <div class="row mt-3">
                    <div class="col-md-6">
                        <div class="component-score">
                            <strong>Font Consistency:</strong> ${Math.round(auth.font_consistency || 0)}%
                            <div class="progress"><div class="progress-bar bg-success" style="width: ${auth.font_consistency || 0}%"></div></div>
                        </div>
                        <div class="component-score">
                            <strong>Grammar Quality:</strong> ${Math.round(auth.grammar_score || 0)}%
                            <div class="progress"><div class="progress-bar bg-success" style="width: ${auth.grammar_score || 0}%"></div></div>
                        </div>
                        <div class="component-score">
                            <strong>Formatting:</strong> ${Math.round(auth.formatting_score || 0)}%
                            <div class="progress"><div class="progress-bar bg-success" style="width: ${auth.formatting_score || 0}%"></div></div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="component-score">
                            <strong>LinkedIn Profile:</strong> ${Math.round(auth.linkedin_profile_score || 0)}%
                            <div class="progress"><div class="progress-bar bg-success" style="width: ${auth.linkedin_profile_score || 0}%"></div></div>
                        </div>
                        <div class="component-score">
                            <strong>Capitalization:</strong> ${Math.round(auth.capitalization_score || 0)}%
                            <div class="progress"><div class="progress-bar bg-success" style="width: ${auth.capitalization_score || 0}%"></div></div>
                        </div>
                        <div class="component-score">
                            <strong>Visual Consistency:</strong> ${Math.round(auth.visual_consistency || 0)}%
                            <div class="progress"><div class="progress-bar bg-success" style="width: ${auth.visual_consistency || 0}%"></div></div>
                        </div>
                    </div>
                </div>
                ${auth.flags && auth.flags.length > 0 ? `
                    <div class="mt-3">
                        <h6><i class="bi bi-flag"></i> Flags Detected:</h6>
                        ${auth.flags.map(flag => `
                            <span class="badge bg-${flag.severity === 'high' ? 'danger' : flag.severity === 'medium' ? 'warning' : 'info'} flag-badge">
                                ${flag.severity === 'high' ? '🔴' : flag.severity === 'medium' ? '🟡' : 'ℹ️'} ${flag.message}
                            </span>
                        `).join('')}
                    </div>
                ` : ''}
                ${scan.matching_score ? `
                    <div class="mt-3">
                        <h6><i class="bi bi-bullseye"></i> Job Match: ${Math.round(scan.matching_score.overall_match || 0)}%</h6>
                        <small>
                            Skills: ${Math.round(scan.matching_score.skills_match || 0)}% |
                            Experience: ${Math.round(scan.matching_score.experience_match || 0)}% |
                            Education: ${Math.round(scan.matching_score.education_match || 0)}%
                        </small>
                    </div>
                ` : ''}
            `;
        }

        function toggleDetails(hash) {
            const row = document.getElementById(`details-${hash}`);
            row.classList.toggle('hidden');
        }

        async function approveResume(hash) {
            await fetch(`/api/v1/vetting/session/${sessionId}/approve/${hash}`, { method: 'POST' });
            document.getElementById(`status-${hash}`).innerHTML = '<span class="badge bg-success">Approved</span>';
            updateStats();
        }

        async function rejectResume(hash) {
            await fetch(`/api/v1/vetting/session/${sessionId}/reject/${hash}`, { method: 'POST' });
            document.getElementById(`status-${hash}`).innerHTML = '<span class="badge bg-danger">Rejected</span>';
            updateStats();
        }

        function updateSelection(hash, checked) {
            if (checked) selectedHashes.add(hash); else selectedHashes.delete(hash);
        }

        function selectAll() { document.querySelectorAll('.resume-check').forEach(cb => { cb.checked = true; selectedHashes.add(cb.dataset.hash); }); }
        function deselectAll() { document.querySelectorAll('.resume-check').forEach(cb => { cb.checked = false; selectedHashes.clear(); }); }

        async function approveSelected() {
            for (const hash of selectedHashes) await approveResume(hash);
        }

        async function rejectSelected() {
            for (const hash of selectedHashes) await rejectResume(hash);
        }

        async function approveByScore() {
            const threshold = document.getElementById('scoreThreshold').value;
            await fetch(`/api/v1/vetting/session/${sessionId}/bulk-approve?min_score=${threshold}`, { method: 'POST' });
            location.reload();
        }

        async function uploadApproved() {
            if (!confirm('Upload all approved resumes to database?')) return;
            const response = await fetch(`/api/v1/vetting/session/${sessionId}/approved`);
            const data = await response.json();
            if (data.total_approved === 0) { alert('No approved resumes to upload'); return; }
            sessionStorage.setItem('approved_resumes', JSON.stringify(data.approved_resumes));
            sessionStorage.setItem('vetting_session_id', sessionId);
            window.location.href = '/upload?source=vetting';
        }

        async function updateStats() {
            const response = await fetch(`/api/v1/vetting/session/${sessionId}`);
            const session = await response.json();
            document.getElementById('statTotal').textContent = Object.keys(session.scanned_resumes).length;
            document.getElementById('statApproved').textContent = session.approved.length;
            document.getElementById('statRejected').textContent = session.rejected.length;
            document.getElementById('statPending').textContent = Object.keys(session.scanned_resumes).length - session.approved.length - session.rejected.length;
        }

        function generateSessionId() { return 'vet_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9); }
        function formatFileSize(bytes) { const sizes = ['Bytes', 'KB', 'MB']; if (bytes === 0) return '0 Bytes'; const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024))); return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i]; }
        function toggleSelectAll() { const checked = document.getElementById('selectAllCheck').checked; if (checked) selectAll(); else deselectAll(); }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    with open("templates/vet_resumes.html", "w", encoding="utf-8") as f:
        f.write(VETTING_PAGE)
    print("✅ Vetting page created successfully!")
    print("📋 Features included:")
    print("  - Drag & drop file upload")
    print("  - Real-time scanning progress")
    print("  - Complete authenticity score display (all 6 components)")
    print("  - Flags and warnings with severity levels")
    print("  - Detailed diagnostics per resume")
    print("  - Approve/Reject individual resumes")
    print("  - Bulk actions (select all, approve by score)")
    print("  - Statistics dashboard")
    print("  - Integration with vetting API")
    print("  - Upload approved to database workflow")
