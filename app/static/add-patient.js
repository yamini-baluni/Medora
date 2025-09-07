// Global variables
let currentUser = null;
let currentToken = null;

// API base URL
const API_BASE = '/api';

// DOM elements
const loadingSpinner = document.getElementById('loadingSpinner');
const addPatientForm = document.getElementById('addPatientForm');
const submitBtn = document.getElementById('submitBtn');
const submitBtnText = document.getElementById('submitBtnText');
const successMessage = document.getElementById('successMessage');
const errorMessage = document.getElementById('errorMessage');
const errorText = document.getElementById('errorText');

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    console.log('Add Patient page loaded');
    initializePage();
    setupEventListeners();
    generatePatientId();
    updateFormProgress();
});

function initializePage() {
    // Check if user is logged in
    const token = localStorage.getItem('medora_token');
    if (token) {
        currentToken = token;
        fetchUserProfile();
    } else {
        // Redirect to login if not authenticated
        window.location.href = '/';
    }
}

function setupEventListeners() {
    // Form submission
    if (addPatientForm) {
        addPatientForm.addEventListener('submit', handleFormSubmission);
    }

    // Add progress tracking to all form fields
    const allFields = addPatientForm.querySelectorAll('input, select, textarea');
    allFields.forEach(field => {
        field.addEventListener('input', updateFormProgress);
        field.addEventListener('change', updateFormProgress);
    });

    // Update debug info
    updateDebugInfo();
}

// Generate patient ID
function generatePatientId() {
    const now = new Date();
    const dateStr = now.getFullYear().toString() + 
                   (now.getMonth() + 1).toString().padStart(2, '0') + 
                   now.getDate().toString().padStart(2, '0');
    const randomStr = Math.random().toString(36).substring(2, 8).toUpperCase();
    const patientId = `MED${dateStr}${randomStr}`;
    
    const patientIdField = document.getElementById('patientId');
    if (patientIdField) {
        patientIdField.value = patientId;
        console.log('Generated Patient ID:', patientId);
    }
}

// Calculate age from date of birth
function calculateAge() {
    const dobField = document.getElementById('dateOfBirth');
    const ageField = document.getElementById('age');
    
    if (dobField && ageField && dobField.value) {
        const dob = new Date(dobField.value);
        const today = new Date();
        const age = today.getFullYear() - dob.getFullYear();
        const monthDiff = today.getMonth() - dob.getMonth();
        
        if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dob.getDate())) {
            age--;
        }
        
        ageField.value = age;
        updateFormProgress();
    }
}

// Form progress tracking
function updateFormProgress() {
    const form = document.getElementById('addPatientForm');
    if (!form) return;
    
    const requiredFields = form.querySelectorAll('input[required], select[required], textarea[required]');
    const optionalFields = form.querySelectorAll('input:not([required]), select:not([required]), textarea:not([required])');
    const totalFields = requiredFields.length + optionalFields.length;
    
    let completedFields = 0;
    
    // Check required fields
    requiredFields.forEach(field => {
        if (field.value.trim() !== '') {
            completedFields++;
        }
    });
    
    // Check optional fields (give partial credit)
    optionalFields.forEach(field => {
        if (field.value.trim() !== '') {
            completedFields += 0.5;
        }
    });
    
    const progress = Math.min(100, Math.round((completedFields / totalFields) * 100));
    
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('formProgress');
    
    if (progressBar) {
        progressBar.style.width = progress + '%';
    }
    
    if (progressText) {
        progressText.textContent = progress + '% Complete';
    }
}

// Update debug information
function updateDebugInfo() {
    const form = document.getElementById('addPatientForm');
    const formStatus = document.getElementById('formStatus');
    const fieldsCount = document.getElementById('fieldsCount');
    
    if (form && formStatus && fieldsCount) {
        const allFields = form.querySelectorAll('input, select, textarea');
        fieldsCount.textContent = allFields.length;
        formStatus.textContent = 'Form loaded successfully';
    }
}

// Fill test data for testing
function fillTestData() {
    console.log('Filling test data...');
    
    const testData = {
        'firstName': 'John',
        'lastName': 'Doe',
        'dateOfBirth': '1990-01-01',
        'gender': 'Male',
        'phone': '123-456-7890',
        'email': 'john.doe@example.com',
        'address': '123 Main Street, City, State 12345',
        'medicalHistory': 'No significant medical history. Annual checkups only.',
        'currentMedications': 'None currently prescribed.',
        'allergies': 'No known allergies.',
        'emergencyName': 'Jane Doe',
        'emergencyPhone': '098-765-4321'
    };
    
    // Fill in the form
    Object.keys(testData).forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.value = testData[fieldId];
            console.log(`✓ Filled ${fieldId} with ${testData[fieldId]}`);
        } else {
            console.error(`✗ Field ${fieldId} not found`);
        }
    });
    
    // Calculate age
    calculateAge();
    
    // Update progress
    updateFormProgress();
    
    console.log('Form filled with test data');
    showToast('Form filled with test data!', 'info');
}

// Handle form submission
async function handleFormSubmission(e) {
    e.preventDefault();
    console.log('Form submission started');
    
    // Validate required fields
    const requiredFields = e.target.querySelectorAll('[required]');
    const missingFields = [];
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            missingFields.push(field.previousElementSibling?.textContent || field.name);
            field.classList.add('border-red-500', 'ring-2', 'ring-red-200');
        } else {
            field.classList.remove('border-red-500', 'ring-2', 'ring-red-200');
        }
    });
    
    if (missingFields.length > 0) {
        showError(`Please fill in required fields: ${missingFields.join(', ')}`);
        return;
    }
    
    // Show confirmation dialog
    const formData = new FormData(e.target);
    const firstName = formData.get('first_name');
    const lastName = formData.get('last_name');
    const dob = formData.get('date_of_birth');
    
    const confirmMessage = `Are you sure you want to create a patient record for:\n\nName: ${firstName} ${lastName}\nDate of Birth: ${dob}\n\nThis will save the patient to the database immediately.`;
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    // Show loading state
    showLoading();
    
    // Prepare data
    const data = {};
    for (let [key, value] of formData.entries()) {
        if (value) data[key] = value;
    }
    
    // Add calculated age
    const ageField = document.getElementById('age');
    if (ageField && ageField.value) {
        data.age = parseInt(ageField.value);
    }
    
    console.log('Submitting patient data:', data);
    
    try {
        const response = await fetch(`${API_BASE}/patients`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        console.log('API Response:', result);

        if (response.ok) {
            showSuccess('Patient created successfully!');
            e.target.reset();
            generatePatientId();
            updateFormProgress();
            
            // Auto-hide success message after 3 seconds
            setTimeout(() => {
                hideSuccess();
            }, 3000);
            
        } else {
            showError(result.error || 'Failed to create patient');
        }
    } catch (error) {
        console.error('Error creating patient:', error);
        showError('Network error occurred');
    } finally {
        hideLoading();
    }
}

// Fetch user profile
async function fetchUserProfile() {
    try {
        const response = await fetch(`${API_BASE}/auth/profile`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });

        if (response.ok) {
            const userData = await response.json();
            currentUser = userData.user;
            
            // Update user info in UI
            const userInfo = document.getElementById('userInfo');
            if (userInfo && currentUser) {
                userInfo.textContent = `Welcome, ${currentUser.first_name}`;
            }
        }
    } catch (error) {
        console.error('Error fetching user profile:', error);
    }
}

// Show loading spinner
function showLoading() {
    if (loadingSpinner) {
        loadingSpinner.classList.remove('hidden');
    }
    
    // Disable submit button
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.classList.add('opacity-75', 'cursor-not-allowed');
    }
    
    if (submitBtnText) {
        submitBtnText.textContent = 'Creating Patient...';
    }
}

// Hide loading spinner
function hideLoading() {
    if (loadingSpinner) {
        loadingSpinner.classList.add('hidden');
    }
    
    // Re-enable submit button
    if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.classList.remove('opacity-75', 'cursor-not-allowed');
    }
    
    if (submitBtnText) {
        submitBtnText.textContent = 'Create Patient Record';
    }
}

// Show success message
function showSuccess(message) {
    hideError();
    if (successMessage) {
        successMessage.classList.remove('hidden');
        const messageElement = successMessage.querySelector('p');
        if (messageElement) {
            messageElement.textContent = message;
        }
    }
}

// Hide success message
function hideSuccess() {
    if (successMessage) {
        successMessage.classList.add('hidden');
    }
}

// Show error message
function showError(message) {
    hideSuccess();
    if (errorMessage && errorText) {
        errorMessage.classList.remove('hidden');
        errorText.textContent = message;
    }
}

// Hide error message
function hideError() {
    if (errorMessage) {
        errorMessage.classList.add('hidden');
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full`;
    
    let bgColor, textColor, icon;
    
    switch (type) {
        case 'success':
            bgColor = 'bg-green-500';
            textColor = 'text-white';
            icon = 'fas fa-check-circle';
            break;
        case 'error':
            bgColor = 'bg-red-500';
            textColor = 'text-white';
            icon = 'fas fa-exclamation-circle';
            break;
        case 'warning':
            bgColor = 'bg-yellow-500';
            textColor = 'text-white';
            icon = 'fas fa-exclamation-triangle';
            break;
        default:
            bgColor = 'bg-blue-500';
            textColor = 'text-white';
            icon = 'fas fa-info-circle';
    }
    
    toast.className += ` ${bgColor} ${textColor}`;
    toast.innerHTML = `
        <div class="flex items-center">
            <i class="${icon} mr-2"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
        toast.classList.remove('translate-x-full');
    }, 100);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.classList.add('translate-x-full');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

// Make functions globally accessible
window.generatePatientId = generatePatientId;
window.calculateAge = calculateAge;
window.fillTestData = fillTestData;
