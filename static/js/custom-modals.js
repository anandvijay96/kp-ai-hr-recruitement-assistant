/**
 * Custom Modal System - Replaces alert(), confirm(), and prompt()
 * Professional, modern UI with Bootstrap 5 styling
 */

class CustomModal {
    constructor() {
        this.modalContainer = null;
        this.createModalContainer();
    }

    createModalContainer() {
        // Create modal container if it doesn't exist
        if (!document.getElementById('customModalContainer')) {
            const container = document.createElement('div');
            container.id = 'customModalContainer';
            document.body.appendChild(container);
            this.modalContainer = container;
        } else {
            this.modalContainer = document.getElementById('customModalContainer');
        }
    }

    /**
     * Show alert modal (replaces alert())
     */
    alert(message, title = 'Notice', type = 'info') {
        return new Promise((resolve) => {
            const modalId = 'alertModal_' + Date.now();
            const iconClass = this.getIconClass(type);
            const iconColor = this.getIconColor(type);
            
            const modalHTML = `
                <div class="modal fade" id="${modalId}" tabindex="-1" data-bs-backdrop="static" data-bs-keyboard="false">
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content">
                            <div class="modal-header border-0 pb-0">
                                <h5 class="modal-title d-flex align-items-center">
                                    <i class="bi ${iconClass} me-2" style="color: ${iconColor}; font-size: 24px;"></i>
                                    ${title}
                                </h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body pt-2">
                                <p class="mb-0" style="white-space: pre-line;">${message}</p>
                            </div>
                            <div class="modal-footer border-0">
                                <button type="button" class="btn btn-primary" data-bs-dismiss="modal">OK</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            this.modalContainer.innerHTML = modalHTML;
            const modalElement = document.getElementById(modalId);
            const modal = new bootstrap.Modal(modalElement);
            
            modalElement.addEventListener('hidden.bs.modal', () => {
                modalElement.remove();
                resolve(true);
            });
            
            modal.show();
        });
    }

    /**
     * Show confirm modal (replaces confirm())
     */
    confirm(message, title = 'Confirm Action', options = {}) {
        return new Promise((resolve) => {
            const modalId = 'confirmModal_' + Date.now();
            const {
                confirmText = 'OK',
                cancelText = 'Cancel',
                confirmClass = 'btn-primary',
                type = 'warning'
            } = options;
            
            const iconClass = this.getIconClass(type);
            const iconColor = this.getIconColor(type);
            
            const modalHTML = `
                <div class="modal fade" id="${modalId}" tabindex="-1" data-bs-backdrop="static" data-bs-keyboard="false">
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content">
                            <div class="modal-header border-0 pb-0">
                                <h5 class="modal-title d-flex align-items-center">
                                    <i class="bi ${iconClass} me-2" style="color: ${iconColor}; font-size: 24px;"></i>
                                    ${title}
                                </h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body pt-2">
                                <p class="mb-0" style="white-space: pre-line;">${message}</p>
                            </div>
                            <div class="modal-footer border-0">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" id="cancelBtn_${modalId}">${cancelText}</button>
                                <button type="button" class="btn ${confirmClass}" id="confirmBtn_${modalId}">${confirmText}</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            this.modalContainer.innerHTML = modalHTML;
            const modalElement = document.getElementById(modalId);
            const modal = new bootstrap.Modal(modalElement);
            
            // Confirm button
            document.getElementById(`confirmBtn_${modalId}`).addEventListener('click', () => {
                modal.hide();
                resolve(true);
            });
            
            // Cancel button and close
            modalElement.addEventListener('hidden.bs.modal', () => {
                modalElement.remove();
                if (!modalElement.dataset.confirmed) {
                    resolve(false);
                }
            });
            
            document.getElementById(`confirmBtn_${modalId}`).addEventListener('click', () => {
                modalElement.dataset.confirmed = 'true';
            });
            
            modal.show();
        });
    }

    /**
     * Show prompt modal (replaces prompt())
     */
    prompt(message, title = 'Input Required', defaultValue = '', options = {}) {
        return new Promise((resolve) => {
            const modalId = 'promptModal_' + Date.now();
            const {
                confirmText = 'OK',
                cancelText = 'Cancel',
                placeholder = '',
                inputType = 'text',
                required = false
            } = options;
            
            const modalHTML = `
                <div class="modal fade" id="${modalId}" tabindex="-1" data-bs-backdrop="static" data-bs-keyboard="false">
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content">
                            <div class="modal-header border-0 pb-0">
                                <h5 class="modal-title d-flex align-items-center">
                                    <i class="bi bi-pencil-square me-2" style="color: #0d6efd; font-size: 24px;"></i>
                                    ${title}
                                </h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body pt-2">
                                <p class="mb-2" style="white-space: pre-line;">${message}</p>
                                <input type="${inputType}" class="form-control" id="promptInput_${modalId}" 
                                       value="${defaultValue}" placeholder="${placeholder}" ${required ? 'required' : ''}>
                            </div>
                            <div class="modal-footer border-0">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" id="cancelBtn_${modalId}">${cancelText}</button>
                                <button type="button" class="btn btn-primary" id="confirmBtn_${modalId}">${confirmText}</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            this.modalContainer.innerHTML = modalHTML;
            const modalElement = document.getElementById(modalId);
            const modal = new bootstrap.Modal(modalElement);
            const inputElement = document.getElementById(`promptInput_${modalId}`);
            
            // Focus input when modal is shown
            modalElement.addEventListener('shown.bs.modal', () => {
                inputElement.focus();
                inputElement.select();
            });
            
            // Enter key to confirm
            inputElement.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    document.getElementById(`confirmBtn_${modalId}`).click();
                }
            });
            
            // Confirm button
            document.getElementById(`confirmBtn_${modalId}`).addEventListener('click', () => {
                const value = inputElement.value;
                if (required && !value.trim()) {
                    inputElement.classList.add('is-invalid');
                    return;
                }
                modalElement.dataset.confirmed = 'true';
                modalElement.dataset.value = value;
                modal.hide();
            });
            
            // Cancel button and close
            modalElement.addEventListener('hidden.bs.modal', () => {
                const confirmed = modalElement.dataset.confirmed === 'true';
                const value = modalElement.dataset.value;
                modalElement.remove();
                resolve(confirmed ? value : null);
            });
            
            modal.show();
        });
    }

    /**
     * Show success toast notification
     */
    success(message, duration = 3000) {
        this.showToast(message, 'success', duration);
    }

    /**
     * Show error toast notification
     */
    error(message, duration = 5000) {
        this.showToast(message, 'danger', duration);
    }

    /**
     * Show info toast notification
     */
    info(message, duration = 3000) {
        this.showToast(message, 'info', duration);
    }

    /**
     * Show warning toast notification
     */
    warning(message, duration = 4000) {
        this.showToast(message, 'warning', duration);
    }

    /**
     * Generic toast notification
     */
    showToast(message, type = 'info', duration = 3000) {
        const toastId = 'toast_' + Date.now();
        const iconClass = this.getIconClass(type);
        const bgClass = this.getToastBgClass(type);
        
        const toastHTML = `
            <div class="toast align-items-center text-white ${bgClass} border-0" id="${toastId}" role="alert" 
                 style="position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px;">
                <div class="d-flex">
                    <div class="toast-body d-flex align-items-center">
                        <i class="bi ${iconClass} me-2" style="font-size: 20px;"></i>
                        <span>${message}</span>
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        // Create toast container if it doesn't exist
        let toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.style.position = 'fixed';
            toastContainer.style.top = '20px';
            toastContainer.style.right = '20px';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }
        
        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { autohide: true, delay: duration });
        
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
        
        toast.show();
    }

    getIconClass(type) {
        const icons = {
            'success': 'bi-check-circle-fill',
            'error': 'bi-x-circle-fill',
            'danger': 'bi-x-circle-fill',
            'warning': 'bi-exclamation-triangle-fill',
            'info': 'bi-info-circle-fill'
        };
        return icons[type] || icons['info'];
    }

    getIconColor(type) {
        const colors = {
            'success': '#28a745',
            'error': '#dc3545',
            'danger': '#dc3545',
            'warning': '#ffc107',
            'info': '#0d6efd'
        };
        return colors[type] || colors['info'];
    }

    getToastBgClass(type) {
        const classes = {
            'success': 'bg-success',
            'error': 'bg-danger',
            'danger': 'bg-danger',
            'warning': 'bg-warning',
            'info': 'bg-info'
        };
        return classes[type] || classes['info'];
    }
}

// Create global instance
window.customModal = new CustomModal();

// Convenience functions (optional - for easier migration)
window.showAlert = (message, title, type) => window.customModal.alert(message, title, type);
window.showConfirm = (message, title, options) => window.customModal.confirm(message, title, options);
window.showPrompt = (message, title, defaultValue, options) => window.customModal.prompt(message, title, defaultValue, options);
window.showSuccess = (message, duration) => window.customModal.success(message, duration);
window.showError = (message, duration) => window.customModal.error(message, duration);
window.showInfo = (message, duration) => window.customModal.info(message, duration);
window.showWarning = (message, duration) => window.customModal.warning(message, duration);
