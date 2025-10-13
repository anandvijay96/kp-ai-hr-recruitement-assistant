# Rating System UI Implementation Guide

## ✅ **PHASE 1 & 2 COMPLETE**
- Database model created
- API endpoints implemented
- Routes registered

## 🎯 **PHASE 3: UI IMPLEMENTATION**

### **Step 1: Add Star Rating CSS**

Add to `<style>` section in `candidate_detail.html`:

```css
/* Star Rating Styles */
.rating-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 24px;
}

.rating-summary {
    text-align: center;
    padding: 20px 0;
}

.rating-score {
    font-size: 48px;
    font-weight: bold;
    margin-bottom: 8px;
}

.rating-stars-large {
    font-size: 24px;
    color: #ffd700;
    margin-bottom: 8px;
}

.rating-count {
    font-size: 14px;
    opacity: 0.9;
}

.star-rating {
    display: inline-flex;
    gap: 4px;
    cursor: pointer;
}

.star-rating.readonly {
    cursor: default;
}

.star-rating i {
    font-size: 20px;
    color: #ddd;
    transition: color 0.2s;
}

.star-rating i.filled {
    color: #ffd700;
}

.star-rating i.half {
    background: linear-gradient(90deg, #ffd700 50%, #ddd 50%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.star-rating:not(.readonly) i:hover,
.star-rating:not(.readonly) i:hover ~ i {
    color: #ffed4e;
}

.rating-category {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #f0f0f0;
}

.rating-category:last-child {
    border-bottom: none;
}

.rating-category-label {
    font-weight: 500;
    color: #495057;
}

.rating-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
}

.rating-badge.highly-recommended {
    background: #d4edda;
    color: #155724;
}

.rating-badge.recommended {
    background: #d1ecf1;
    color: #0c5460;
}

.rating-badge.maybe {
    background: #fff3cd;
    color: #856404;
}

.rating-badge.not-recommended {
    background: #f8d7da;
    color: #721c24;
}

.rating-history-item {
    padding: 16px;
    background: #f8f9fa;
    border-radius: 8px;
    margin-bottom: 12px;
}

.rating-history-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.rating-history-user {
    font-weight: 600;
    color: #495057;
}

.rating-history-date {
    font-size: 12px;
    color: #6c757d;
}
```

### **Step 2: Add Rating Section HTML**

Insert after Assessment Scores section:

```html
<!-- Candidate Rating -->
<div class="detail-card">
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="section-title mb-0">
            <i class="bi bi-star me-2"></i>
            Recruiter Rating
        </h5>
        <button class="btn btn-primary btn-sm" id="addRatingBtn">
            <i class="bi bi-plus-circle me-1"></i>Add Rating
        </button>
    </div>
    
    <!-- Rating Summary -->
    <div id="ratingSummary" style="display: none;">
        <div class="rating-section">
            <div class="rating-summary">
                <div class="rating-score" id="avgOverallRating">-</div>
                <div class="rating-stars-large" id="avgOverallStars"></div>
                <div class="rating-count" id="ratingCount">No ratings yet</div>
            </div>
        </div>
        
        <!-- Category Breakdown -->
        <div id="categoryBreakdown">
            <div class="rating-category">
                <span class="rating-category-label">Technical Skills</span>
                <div class="star-rating readonly" id="avgTechnicalStars"></div>
            </div>
            <div class="rating-category">
                <span class="rating-category-label">Communication</span>
                <div class="star-rating readonly" id="avgCommunicationStars"></div>
            </div>
            <div class="rating-category">
                <span class="rating-category-label">Culture Fit</span>
                <div class="star-rating readonly" id="avgCultureFitStars"></div>
            </div>
            <div class="rating-category">
                <span class="rating-category-label">Experience Level</span>
                <div class="star-rating readonly" id="avgExperienceStars"></div>
            </div>
        </div>
    </div>
    
    <!-- No Ratings Message -->
    <div id="noRatingsMessage" class="text-center text-muted py-4">
        <i class="bi bi-star" style="font-size: 48px; opacity: 0.3;"></i>
        <p class="mt-2">No ratings yet. Be the first to rate this candidate!</p>
    </div>
    
    <!-- Rating History -->
    <div id="ratingHistory" style="display: none; margin-top: 20px;">
        <h6 class="mb-3">Rating History</h6>
        <div id="ratingHistoryList"></div>
    </div>
</div>
```

### **Step 3: Add Rating Modal**

Insert before closing `</body>` tag:

```html
<!-- Rating Modal -->
<div class="modal fade" id="ratingModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">
                    <i class="bi bi-star me-2"></i>
                    Rate Candidate
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form id="ratingForm">
                    <!-- Technical Skills -->
                    <div class="mb-4">
                        <label class="form-label">Technical Skills</label>
                        <div class="star-rating" id="technicalSkillsRating" data-category="technical_skills">
                            <i class="bi bi-star" data-value="1"></i>
                            <i class="bi bi-star" data-value="2"></i>
                            <i class="bi bi-star" data-value="3"></i>
                            <i class="bi bi-star" data-value="4"></i>
                            <i class="bi bi-star" data-value="5"></i>
                        </div>
                    </div>
                    
                    <!-- Communication -->
                    <div class="mb-4">
                        <label class="form-label">Communication</label>
                        <div class="star-rating" id="communicationRating" data-category="communication">
                            <i class="bi bi-star" data-value="1"></i>
                            <i class="bi bi-star" data-value="2"></i>
                            <i class="bi bi-star" data-value="3"></i>
                            <i class="bi bi-star" data-value="4"></i>
                            <i class="bi bi-star" data-value="5"></i>
                        </div>
                    </div>
                    
                    <!-- Culture Fit -->
                    <div class="mb-4">
                        <label class="form-label">Culture Fit</label>
                        <div class="star-rating" id="cultureFitRating" data-category="culture_fit">
                            <i class="bi bi-star" data-value="1"></i>
                            <i class="bi bi-star" data-value="2"></i>
                            <i class="bi bi-star" data-value="3"></i>
                            <i class="bi bi-star" data-value="4"></i>
                            <i class="bi bi-star" data-value="5"></i>
                        </div>
                    </div>
                    
                    <!-- Experience Level -->
                    <div class="mb-4">
                        <label class="form-label">Experience Level</label>
                        <div class="star-rating" id="experienceLevelRating" data-category="experience_level">
                            <i class="bi bi-star" data-value="1"></i>
                            <i class="bi bi-star" data-value="2"></i>
                            <i class="bi bi-star" data-value="3"></i>
                            <i class="bi bi-star" data-value="4"></i>
                            <i class="bi bi-star" data-value="5"></i>
                        </div>
                    </div>
                    
                    <!-- Recommendation -->
                    <div class="mb-4">
                        <label class="form-label">Recommendation</label>
                        <select class="form-select" id="recommendation">
                            <option value="">Select recommendation</option>
                            <option value="highly_recommended">Highly Recommended</option>
                            <option value="recommended">Recommended</option>
                            <option value="maybe">Maybe</option>
                            <option value="not_recommended">Not Recommended</option>
                        </select>
                    </div>
                    
                    <!-- Comments -->
                    <div class="mb-4">
                        <label class="form-label">Comments</label>
                        <textarea class="form-control" id="comments" rows="3" placeholder="General feedback..."></textarea>
                    </div>
                    
                    <!-- Strengths -->
                    <div class="mb-4">
                        <label class="form-label">Strengths</label>
                        <textarea class="form-control" id="strengths" rows="2" placeholder="What did you like?"></textarea>
                    </div>
                    
                    <!-- Concerns -->
                    <div class="mb-4">
                        <label class="form-label">Concerns</label>
                        <textarea class="form-control" id="concerns" rows="2" placeholder="Any concerns?"></textarea>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary" id="saveRatingBtn">
                    <i class="bi bi-check-circle me-1"></i>Save Rating
                </button>
            </div>
        </div>
    </div>
</div>
```

### **Step 4: Add JavaScript Functions**

Add before closing `</script>` tag:

```javascript
// Star Rating System
let ratingData = {
    technical_skills: 0,
    communication: 0,
    culture_fit: 0,
    experience_level: 0
};

// Initialize star ratings
function initStarRatings() {
    $('.star-rating:not(.readonly)').each(function() {
        const $rating = $(this);
        const category = $rating.data('category');
        
        $rating.find('i').on('click', function() {
            const value = parseInt($(this).data('value'));
            ratingData[category] = value;
            updateStars($rating, value);
        });
        
        $rating.find('i').on('mouseenter', function() {
            const value = parseInt($(this).data('value'));
            highlightStars($rating, value);
        });
        
        $rating.on('mouseleave', function() {
            updateStars($rating, ratingData[category]);
        });
    });
}

function highlightStars($rating, value) {
    $rating.find('i').each(function(index) {
        if (index < value) {
            $(this).removeClass('bi-star').addClass('bi-star-fill filled');
        } else {
            $(this).removeClass('bi-star-fill filled').addClass('bi-star');
        }
    });
}

function updateStars($rating, value) {
    highlightStars($rating, value);
}

function renderStars(rating, readonly = true) {
    let html = `<div class="star-rating ${readonly ? 'readonly' : ''}">`;
    for (let i = 1; i <= 5; i++) {
        if (i <= rating) {
            html += `<i class="bi bi-star-fill filled"></i>`;
        } else {
            html += `<i class="bi bi-star"></i>`;
        }
    }
    html += '</div>';
    return html;
}

// Load rating summary
async function loadRatingSummary(candidateId) {
    try {
        const response = await fetch(`/api/v1/candidates/${candidateId}/rating-summary`);
        const summary = await response.json();
        
        if (summary.total_ratings > 0) {
            $('#ratingSummary').show();
            $('#noRatingsMessage').hide();
            
            // Overall rating
            $('#avgOverallRating').text(summary.average_overall.toFixed(1));
            $('#avgOverallStars').html(renderStars(Math.round(summary.average_overall)));
            $('#ratingCount').text(`Based on ${summary.total_ratings} rating${summary.total_ratings > 1 ? 's' : ''}`);
            
            // Category breakdown
            if (summary.average_technical) {
                $('#avgTechnicalStars').html(renderStars(Math.round(summary.average_technical)).replace('star-rating', ''));
            }
            if (summary.average_communication) {
                $('#avgCommunicationStars').html(renderStars(Math.round(summary.average_communication)).replace('star-rating', ''));
            }
            if (summary.average_culture_fit) {
                $('#avgCultureFitStars').html(renderStars(Math.round(summary.average_culture_fit)).replace('star-rating', ''));
            }
            if (summary.average_experience) {
                $('#avgExperienceStars').html(renderStars(Math.round(summary.average_experience)).replace('star-rating', ''));
            }
        } else {
            $('#ratingSummary').hide();
            $('#noRatingsMessage').show();
        }
        
        // Load rating history
        await loadRatingHistory(candidateId);
        
    } catch (error) {
        console.error('Error loading rating summary:', error);
    }
}

// Load rating history
async function loadRatingHistory(candidateId) {
    try {
        const response = await fetch(`/api/v1/candidates/${candidateId}/ratings`);
        const ratings = await response.json();
        
        if (ratings.length > 0) {
            $('#ratingHistory').show();
            const historyHtml = ratings.map(rating => `
                <div class="rating-history-item">
                    <div class="rating-history-header">
                        <div>
                            <span class="rating-history-user">${rating.user_name}</span>
                            ${rating.recommendation ? `<span class="rating-badge ${rating.recommendation}">${rating.recommendation.replace('_', ' ')}</span>` : ''}
                        </div>
                        <span class="rating-history-date">${new Date(rating.created_at).toLocaleDateString()}</span>
                    </div>
                    <div class="mb-2">
                        ${renderStars(rating.overall_rating || 0)}
                    </div>
                    ${rating.comments ? `<p class="mb-0 small">${rating.comments}</p>` : ''}
                </div>
            `).join('');
            $('#ratingHistoryList').html(historyHtml);
        } else {
            $('#ratingHistory').hide();
        }
    } catch (error) {
        console.error('Error loading rating history:', error);
    }
}

// Show rating modal
$('#addRatingBtn').on('click', function() {
    // Reset form
    ratingData = {
        technical_skills: 0,
        communication: 0,
        culture_fit: 0,
        experience_level: 0
    };
    $('.star-rating:not(.readonly) i').removeClass('bi-star-fill filled').addClass('bi-star');
    $('#ratingForm')[0].reset();
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('ratingModal'));
    modal.show();
    
    // Initialize star ratings
    initStarRatings();
});

// Save rating
$('#saveRatingBtn').on('click', async function() {
    const candidateId = window.currentCandidateId;
    
    const ratingPayload = {
        candidate_id: candidateId,
        technical_skills: ratingData.technical_skills || null,
        communication: ratingData.communication || null,
        culture_fit: ratingData.culture_fit || null,
        experience_level: ratingData.experience_level || null,
        recommendation: $('#recommendation').val() || null,
        comments: $('#comments').val() || null,
        strengths: $('#strengths').val() || null,
        concerns: $('#concerns').val() || null
    };
    
    try {
        const response = await fetch(`/api/v1/candidates/${candidateId}/rate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(ratingPayload)
        });
        
        if (response.ok) {
            // Close modal
            bootstrap.Modal.getInstance(document.getElementById('ratingModal')).hide();
            
            // Reload ratings
            await loadRatingSummary(candidateId);
            
            // Show success message
            alert('Rating saved successfully!');
        } else {
            const error = await response.json();
            alert('Error saving rating: ' + (error.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error saving rating:', error);
        alert('Error saving rating. Please try again.');
    }
});

// Call loadRatingSummary when candidate is loaded
// Add to displayCandidateDetails function:
// await loadRatingSummary(candidate.id);
```

---

## 🎯 **NEXT STEPS**

1. Add CSS to style section ✅
2. Add rating section HTML after Assessment Scores ✅
3. Add rating modal before `</body>` ✅
4. Add JavaScript functions ✅
5. Call `loadRatingSummary()` in `displayCandidateDetails()` function
6. Test create/view rating flow
7. Add rating filters to search page
8. Add rating analytics to dashboard

---

**Status:** Implementation guide complete  
**Next:** Apply changes to candidate_detail.html
