document.addEventListener('DOMContentLoaded', () => {
    const skillsFilter = document.getElementById('skills-filter');
    const experienceFilter = document.getElementById('experience-filter');
    const educationFilter = document.getElementById('education-filter');
    const locationFilter = document.getElementById('location-filter');
    const resultsList = document.getElementById('results-list');
    const paginationContainer = document.getElementById('pagination');
    const applyFiltersButton = document.getElementById('apply-filters');
    const clearFiltersButton = document.getElementById('clear-filters');

    async function fetchFilterOptions() {
        try {
            const response = await fetch('/api/v1/candidates/filter-options');
            const options = await response.json();
            renderFilterOptions(options);
        } catch (error) {
            console.error('Failed to fetch filter options:', error);
        }
    }

    function renderFilterOptions(options) {
        // Render skills
        skillsFilter.innerHTML = options.skills.map(skill => `
            <div class="filter-checkbox">
                <input type="checkbox" id="skill-${skill}" name="skill" value="${skill}">
                <label for="skill-${skill}">${skill}</label>
            </div>
        `).join('');

        // Render experience filter
        experienceFilter.innerHTML = `
            <div class="filter-range">
                <label>Min: <input type="number" id="min-experience" min="0" max="30" value="0"> years</label>
                <label>Max: <input type="number" id="max-experience" min="0" max="30" value="30"> years</label>
            </div>
        `;

        // Render education filter
        educationFilter.innerHTML = options.education_levels.map(level => `
            <div class="filter-checkbox">
                <input type="checkbox" id="edu-${level}" name="education" value="${level}">
                <label for="edu-${level}">${level}</label>
            </div>
        `).join('');

        // Render location filter
        locationFilter.innerHTML = `
            <select id="location-select" class="filter-select">
                <option value="">All Locations</option>
                ${options.locations.map(loc => `<option value="${loc}">${loc}</option>`).join('')}
            </select>
        `;
    }

    function getAppliedFilters() {
        const filters = {};
        const keywords = document.getElementById('search-keywords').value;
        if (keywords) {
            filters.search_query = keywords;
        }

        const selectedSkills = Array.from(skillsFilter.querySelectorAll('input:checked')).map(input => input.value);
        if (selectedSkills.length > 0) {
            filters.skills = selectedSkills;
        }

        const minExp = document.getElementById('min-experience')?.value;
        const maxExp = document.getElementById('max-experience')?.value;
        if (minExp) filters.min_experience = parseInt(minExp);
        if (maxExp) filters.max_experience = parseInt(maxExp);

        const selectedEducation = Array.from(educationFilter.querySelectorAll('input:checked')).map(input => input.value);
        if (selectedEducation.length > 0) {
            filters.education = selectedEducation;
        }

        const location = document.getElementById('location-select')?.value;
        if (location) {
            filters.location = location;
        }

        return filters;
    }

    async function applyFilters(page = 1) {
        const filters = getAppliedFilters();

        try {
            const response = await fetch(`/api/v1/candidates/search?page=${page}`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(filters)
            });
            const data = await response.json();
            renderResults(data.results);
            renderPagination(data.pagination);
        } catch (error) {
            console.error('Failed to apply filters:', error);
        }
    }

    function renderResults(results) {
        resultsList.innerHTML = '';
        
        // Update result count
        const resultCount = document.getElementById('result-count');
        if (resultCount) {
            resultCount.textContent = `${results.length} candidate${results.length !== 1 ? 's' : ''} found`;
        }
        
        if (results.length === 0) {
            resultsList.innerHTML = `
                <div class="alert alert-info">
                    <h5 class="alert-heading">No candidates found</h5>
                    <p class="mb-0">Try adjusting your filters to see more results.</p>
                </div>
            `;
            return;
        }

        results.forEach(candidate => {
            const statusBadge = getStatusBadge(candidate.status || 'New');
            const candidateCard = document.createElement('div');
            candidateCard.className = 'card candidate-card mb-3';
            candidateCard.innerHTML = `
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h5 class="card-title mb-0">${candidate.name || 'N/A'}</h5>
                        <span class="badge ${statusBadge.class}">${statusBadge.text}</span>
                    </div>
                    <p class="text-muted small mb-2">
                        <i class="bi bi-envelope"></i> ${candidate.email || 'N/A'}
                    </p>
                    <div class="row mb-2">
                        <div class="col-md-6">
                            <small><strong>Skills:</strong></small><br>
                            <small>${candidate.skills ? candidate.skills.map(s => `<span class="badge bg-light text-dark me-1">${s}</span>`).join('') : 'N/A'}</small>
                        </div>
                        <div class="col-md-3">
                            <small><strong>Experience:</strong></small><br>
                            <small>${candidate.experience_years || 0} years</small>
                        </div>
                        <div class="col-md-3">
                            <small><strong>Education:</strong></small><br>
                            <small>${candidate.education || 'N/A'}</small>
                        </div>
                    </div>
                    <div class="d-flex gap-2 mt-3">
                        <button class="btn btn-sm btn-primary" onclick="viewCandidate(${candidate.id})">View Profile</button>
                        <button class="btn btn-sm btn-success" onclick="shortlistCandidate(${candidate.id})">Shortlist</button>
                    </div>
                </div>
            `;
            resultsList.appendChild(candidateCard);
        });
    }
    
    function getStatusBadge(status) {
        const statusMap = {
            'New': { class: 'bg-info', text: 'New' },
            'Screened': { class: 'bg-warning', text: 'Screened' },
            'Interviewed': { class: 'bg-primary', text: 'Interviewed' },
            'Offered': { class: 'bg-success', text: 'Offered' },
            'Hired': { class: 'bg-success', text: 'Hired' },
            'Rejected': { class: 'bg-danger', text: 'Rejected' }
        };
        return statusMap[status] || { class: 'bg-secondary', text: status };
    }

    function renderPagination(pagination) {
        paginationContainer.innerHTML = '';
        if (pagination.total_pages <= 1) return;

        const nav = document.createElement('nav');
        nav.innerHTML = `
            <ul class="pagination justify-content-center">
                <li class="page-item ${pagination.page === 1 ? 'disabled' : ''}">
                    <a class="page-link" href="#" data-page="${pagination.page - 1}">Previous</a>
                </li>
                ${Array.from({length: pagination.total_pages}, (_, i) => i + 1).map(i => `
                    <li class="page-item ${i === pagination.page ? 'active' : ''}">
                        <a class="page-link" href="#" data-page="${i}">${i}</a>
                    </li>
                `).join('')}
                <li class="page-item ${pagination.page === pagination.total_pages ? 'disabled' : ''}">
                    <a class="page-link" href="#" data-page="${pagination.page + 1}">Next</a>
                </li>
            </ul>
        `;
        
        nav.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(e.target.dataset.page);
                if (page >= 1 && page <= pagination.total_pages) {
                    applyFilters(page);
                }
            });
        });
        
        paginationContainer.appendChild(nav);
    }

    function clearFilters() {
        document.getElementById('search-keywords').value = '';
        skillsFilter.querySelectorAll('input:checked').forEach(input => input.checked = false);
        educationFilter.querySelectorAll('input:checked').forEach(input => input.checked = false);
        if (document.getElementById('min-experience')) document.getElementById('min-experience').value = 0;
        if (document.getElementById('max-experience')) document.getElementById('max-experience').value = 30;
        if (document.getElementById('location-select')) document.getElementById('location-select').value = '';
        applyFilters();
    }

    applyFiltersButton.addEventListener('click', () => applyFilters());
    clearFiltersButton.addEventListener('click', clearFilters);

    // Initial load
    fetchFilterOptions();
    applyFilters();
});

// Placeholder functions for candidate actions
function viewCandidate(id) {
    alert(`View Profile for Candidate ID: ${id}\n\nThis feature will be implemented in the next phase.`);
}

function shortlistCandidate(id) {
    alert(`Shortlist Candidate ID: ${id}\n\nThis feature will be implemented in the next phase.`);
}
