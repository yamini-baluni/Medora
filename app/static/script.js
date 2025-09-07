// Global variables
let currentUser = null;
let currentToken = null;
let patients = [];
let editingPatientId = null;

// DOM elements
const authForms = document.getElementById('authForms');
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const navMenu = document.getElementById('navMenu');
const navToggle = document.getElementById('navToggle');
const logoutBtn = document.getElementById('logoutBtn');
const userName = document.getElementById('userName');
const loadingSpinner = document.getElementById('loadingSpinner');
const toastContainer = document.getElementById('toastContainer');

// API base URL
const API_BASE = '/api';

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    checkAuthStatus();
});

function initializeApp() {
    // Check if user is already logged in
    const token = localStorage.getItem('medora_token');
    if (token) {
        currentToken = token;
        fetchUserProfile();
    }
}

function setupEventListeners() {
    // Authentication form tabs
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.addEventListener('click', (e) => {
            console.log('Auth tab clicked:', e.target);
            const formType = e.target.dataset.form;
            console.log('Form type from dataset:', formType);
            switchAuthForm(formType);
        });
    });

        // Top-right authentication buttons
    document.getElementById('signInBtn').addEventListener('click', () => {
        // Navigate to sign in page
        window.location.href = '/signin';
    });
    
    document.getElementById('createAccountBtn').addEventListener('click', () => {
        // Navigate to registration page
        window.location.href = '/register';
    });

    // Login form
    loginForm.addEventListener('submit', handleLogin);

    // Register form
    registerForm.addEventListener('submit', handleRegister);

    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = e.target.closest('.nav-link').dataset.page;
            console.log('Navigation clicked:', page);
            navigateToPage(page);
        });
    });

    // Mobile navigation toggle
    navToggle.addEventListener('click', toggleMobileNav);

    // Logout
    logoutBtn.addEventListener('click', handleLogout);

    // Patient management
    document.getElementById('addPatientBtn').addEventListener('click', showAddPatientModal);
    document.getElementById('addPatientBtn2').addEventListener('click', showAddPatientModal);
    document.getElementById('closePatientModal').addEventListener('click', hidePatientModal);
    document.getElementById('cancelPatientBtn').addEventListener('click', hidePatientModal);
    document.getElementById('patientForm').addEventListener('submit', handlePatientSubmit);
    document.getElementById('patientSearch').addEventListener('input', handlePatientSearch);

    // Search button
    document.getElementById('searchBtn').addEventListener('click', () => {
        const searchTerm = document.getElementById('patientSearch').value;
        searchPatients(searchTerm);
    });

    // Profile form
    document.getElementById('profileForm').addEventListener('submit', handleProfileUpdate);

    // User management
    setupUserManagement();
    
    // Dashboard doctor action buttons
    const dashboardAddPatientBtn = document.getElementById('dashboardAddPatientBtn');
    const dashboardSearchPatientBtn = document.getElementById('dashboardSearchPatientBtn');
    
    if (dashboardAddPatientBtn) {
        dashboardAddPatientBtn.addEventListener('click', () => {
            console.log('Dashboard Add Patient button clicked');
            navigateToPage('addPatient');
        });
    }
    
    if (dashboardSearchPatientBtn) {
        dashboardSearchPatientBtn.addEventListener('click', () => navigateToPage('patients'));
    }
}

// Navigation function
function navigateToPage(page) {
    console.log('navigateToPage called with:', page);
    
    // Check if user has permission to access this page
    if (!currentUser) {
        showToast('Please log in to access this page', 'error');
        return;
    }
    
    // Role-based access control
    if (page === 'patients' && currentUser.role !== 'admin' && currentUser.role !== 'doctor') {
        showToast('Only doctors and administrators can access the Patients page', 'error');
        return;
    }
    
    if (page === 'users' && currentUser.role !== 'admin') {
        showToast('Only administrators can access the Users page', 'error');
        return;
    }

    // Hide all pages
    document.querySelectorAll('.page-content').forEach(p => {
        p.classList.add('hidden');
    });

    // Remove active class from all nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });

    // Show selected page and activate nav link
    document.getElementById(`${page}Page`).classList.remove('hidden');
    document.querySelector(`[data-page="${page}"]`).classList.add('active');

    // Load page-specific content
    switch (page) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'patients':
            loadPatients();
            break;
        case 'users':
            loadUsers();
            break;
        case 'patientView':
            loadPatientView();
            break;
        case 'appointments':
            loadAppointments();
            break;
        case 'addPatient':
            showAddPatientPage();
            break;
        case 'profile':
            loadProfile();
            break;
    }
}

// Authentication functions
function switchAuthForm(formType) {
    console.log('Switching to form:', formType);
    
    // Remove active class from all tabs
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.classList.remove('active');
        tab.classList.remove('bg-white', 'text-medora-600', 'shadow-sm');
        tab.classList.add('text-gray-600');
    });
    
    // Hide all forms first
    document.querySelectorAll('.auth-form').forEach(form => {
        form.classList.add('hidden');
        form.classList.remove('active');
    });

    // Add active class to selected tab
    const selectedTab = document.querySelector(`[data-form="${formType}"]`);
    if (selectedTab) {
        selectedTab.classList.add('active', 'bg-white', 'text-medora-600', 'shadow-sm');
        selectedTab.classList.remove('text-gray-600');
        console.log('Selected tab:', selectedTab);
    } else {
        console.error('Tab not found for form type:', formType);
    }
    
    // Show selected form
    const selectedForm = document.getElementById(`${formType}Form`);
    if (selectedForm) {
        selectedForm.classList.remove('hidden');
        selectedForm.classList.add('active');
        console.log('Selected form:', selectedForm);
    } else {
        console.error('Form not found for form type:', formType);
    }
}

async function handleLogin(e) {
    e.preventDefault();
    showLoading();

    const formData = new FormData(loginForm);
    const data = {
        username: formData.get('username'),
        password: formData.get('password')
    };

    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            currentToken = result.access_token;
            currentUser = result.user;
            
            localStorage.setItem('medora_token', currentToken);
            localStorage.setItem('medora_user', JSON.stringify(currentUser));
            
            // Show success message with user details
            showToast(`🎉 Welcome back, ${currentUser.first_name}! Login successful!`, 'success');
            
            // Clear form
            loginForm.reset();
            
            // Show authenticated UI
            showAuthenticatedUI();
            loadDashboard();
            
            // Show welcome message
            setTimeout(() => {
                showToast(`👋 Welcome to Medora, ${currentUser.first_name} ${currentUser.last_name}!`, 'success');
            }, 1000);
            
        } else {
            showToast(result.error || 'Login failed. Please check your credentials.', 'error');
        }
    } catch (error) {
        showToast('Network error. Please check your connection and try again.', 'error');
    } finally {
        hideLoading();
    }
}

async function handleRegister(e) {
    e.preventDefault();
    showLoading();

    const formData = new FormData(registerForm);
    const data = {
        username: formData.get('username'),
        email: formData.get('email'),
        password: formData.get('password'),
        first_name: formData.get('first_name'),
        last_name: formData.get('last_name'),
        phone: formData.get('phone')
    };

    try {
        const response = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            currentToken = result.access_token;
            currentUser = result.user;
            
            localStorage.setItem('medora_token', currentToken);
            localStorage.setItem('medora_user', JSON.stringify(currentUser));
            
            // Show comprehensive success message
            showToast(`🎉 Registration successful! Welcome to Medora, ${currentUser.first_name}!`, 'success');
            
            // Clear form
            registerForm.reset();
            
            // Show verification details if available
            if (result.verification) {
                setTimeout(() => {
                    showToast(`✅ Account verified! User ID: ${result.verification.database_id}`, 'success');
                }, 1500);
            }
            
            // Create patient record for new users (if they're not admin/doctor)
            if (currentUser.role === 'user' || currentUser.role === 'patient') {
                await createPatientRecord();
            }
            
            // Show authenticated UI
            showAuthenticatedUI();
            loadDashboard();
            
            // Show welcome message
            setTimeout(() => {
                showToast(`🚀 Your account has been created and saved to the database successfully!`, 'success');
            }, 2000);
            
        } else {
            showToast(result.error || 'Registration failed. Please try again.', 'error');
        }
    } catch (error) {
        showToast('Network error. Please check your connection and try again.', 'error');
    } finally {
        hideLoading();
    }
}

async function createPatientRecord() {
    try {
        const patientData = {
            first_name: currentUser.first_name,
            last_name: currentUser.last_name,
            phone: currentUser.phone,
            date_of_birth: '1990-01-01', // Default date, can be updated later
            gender: 'Not specified'
        };
        
        const response = await fetch(`${API_BASE}/patients`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify(patientData)
        });
        
        if (response.ok) {
            showToast('✅ Patient record created successfully! You can now view your health data.', 'success');
        } else {
            const errorData = await response.json();
            console.log('Patient record creation failed:', errorData.error);
        }
    } catch (error) {
        console.log('Error creating patient record:', error);
    }
}

async function fetchUserProfile() {
    try {
        const response = await fetch(`${API_BASE}/profile`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });

        if (response.ok) {
            const result = await response.json();
            currentUser = result.user;
            localStorage.setItem('medora_user', JSON.stringify(currentUser));
            showAuthenticatedUI();
            loadDashboard();
        } else {
            // Token expired or invalid
            handleLogout();
        }
    } catch (error) {
        handleLogout();
    }
}

function handleLogout() {
    currentToken = null;
    currentUser = null;
    localStorage.removeItem('medora_token');
    localStorage.removeItem('medora_user');
    
    showAuthUI();
    showToast('Logged out successfully', 'success');
}

function checkAuthStatus() {
    if (currentToken && currentUser) {
        showAuthenticatedUI();
        loadDashboard();
    } else {
        showAuthUI();
    }
}

// UI functions
function showAuthUI() {
    // Show authentication forms
    authForms.classList.remove('hidden');
    
    // Hide all pages
    document.querySelectorAll('.page-content').forEach(page => {
        page.classList.add('hidden');
    });
    
    // Remove active class from all nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Show auth buttons, hide user info
    document.getElementById('authButtons').classList.remove('hidden');
    document.getElementById('userInfo').classList.add('hidden');
    
    // Reset user name
    document.getElementById('userName').textContent = 'Guest';
}

function showAuthenticatedUI() {
    // Hide authentication forms
    authForms.classList.add('hidden');
    
    // Show dashboard page
    document.getElementById('dashboardPage').classList.remove('hidden');
    document.querySelector('[data-page="dashboard"]').classList.add('active');
    
    // Hide auth buttons, show user info
    document.getElementById('authButtons').classList.add('hidden');
    document.getElementById('userInfo').classList.remove('hidden');
    
    // Update user name
    document.getElementById('userName').textContent = `${currentUser.first_name} ${currentUser.last_name}`;
    
    // Update navigation visibility based on user role
    updateNavigationVisibility();
}

function updateNavigationVisibility() {
    if (!currentUser) return;
    
    // Show/hide navigation links based on role
    const patientsLink = document.querySelector('[data-page="patients"]');
    const addPatientLink = document.querySelector('[data-page="addPatient"]');
    const usersLink = document.querySelector('[data-page="users"]');
    const patientViewLink = document.querySelector('[data-page="patientView"]');
    
    if (patientsLink) {
        if (currentUser.role === 'admin' || currentUser.role === 'doctor') {
            patientsLink.classList.remove('hidden');
        } else {
            patientsLink.classList.add('hidden');
        }
    }
    
    if (addPatientLink) {
        if (currentUser.role === 'admin' || currentUser.role === 'doctor') {
            addPatientLink.classList.remove('hidden');
        } else {
            addPatientLink.classList.add('hidden');
        }
    }
    
    if (usersLink) {
        if (currentUser.role === 'admin') {
            usersLink.classList.remove('hidden');
        } else {
            usersLink.classList.add('hidden');
        }
    }
    
    if (patientViewLink) {
        if (currentUser.role === 'patient' || currentUser.role === 'user') {
            patientViewLink.classList.remove('hidden');
        } else {
            patientViewLink.classList.add('hidden');
        }
    }
}

// Dashboard functions
async function loadDashboard() {
    showLoading();
    try {
        const response = await fetch(`${API_BASE}/dashboard`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            updateDashboard(data);
        } else {
            showToast('Failed to load dashboard', 'error');
        }
    } catch (error) {
        showToast('Network error', 'error');
    } finally {
        hideLoading();
    }
}

function updateDashboard(data) {
    // Update stats
    document.getElementById('totalPatients').textContent = data.statistics.total_patients;
    document.getElementById('totalAppointments').textContent = data.statistics.total_appointments;
    document.getElementById('todayAppointments').textContent = data.statistics.today_appointments || 0;
    document.getElementById('newPatientsMonth').textContent = data.statistics.new_patients_month || 0;
    
    // Update user name
    document.getElementById('dashboardUserName').textContent = data.user.first_name;

    // Update recent patients
    const recentPatientsContainer = document.getElementById('recentPatients');
    if (data.recent_patients && data.recent_patients.length > 0) {
        recentPatientsContainer.innerHTML = data.recent_patients.map(patient => `
            <div class="patient-item">
                <strong>${patient.first_name} ${patient.last_name}</strong>
                <span class="patient-id">${patient.patient_id}</span>
            </div>
        `).join('');
    } else {
        recentPatientsContainer.innerHTML = '<p class="empty-state">No patients yet</p>';
    }

    // Update upcoming appointments
    const upcomingAppointmentsContainer = document.getElementById('upcomingAppointments');
    if (data.upcoming_appointments && data.upcoming_appointments.length > 0) {
        upcomingAppointmentsContainer.innerHTML = data.upcoming_appointments.map(appointment => `
            <div class="appointment-item">
                <strong>${appointment.doctor_name}</strong>
                <span>${new Date(appointment.appointment_date).toLocaleDateString()}</span>
            </div>
        `).join('');
    } else {
        upcomingAppointmentsContainer.innerHTML = '<p class="empty-state">No upcoming appointments</p>';
    }
    
    // Show doctor actions section for doctors and admins
    const doctorActionsSection = document.getElementById('doctorActions');
    if (doctorActionsSection) {
        if (currentUser && (currentUser.role === 'doctor' || currentUser.role === 'admin')) {
            doctorActionsSection.classList.remove('hidden');
        } else {
            doctorActionsSection.classList.add('hidden');
        }
    }
}

// Patient management functions
async function loadPatients() {
    showLoading();
    try {
        const response = await fetch(`${API_BASE}/patients`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            patients = data.patients;
            displayPatients(patients);
        } else {
            showToast('Failed to load patients', 'error');
        }
    } catch (error) {
        showToast('Network error', 'error');
    } finally {
        hideLoading();
    }
}

function displayPatients(patientsToShow) {
    const tbody = document.getElementById('patientsTableBody');
    
    if (!patientsToShow || patientsToShow.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="px-6 py-8 text-center text-gray-500">
                    <div class="flex flex-col items-center">
                        <i class="fas fa-user-injured text-4xl text-gray-300 mb-4"></i>
                        <p class="text-lg font-medium text-gray-700 mb-2">No patients found</p>
                        <p class="text-gray-500">Start building your patient database by adding new patients</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = patientsToShow.map(patient => {
        // Calculate age from date of birth
        const age = patient.date_of_birth ? 
            Math.floor((new Date() - new Date(patient.date_of_birth)) / (365.25 * 24 * 60 * 60 * 1000)) : 'N/A';
        
        return `
            <tr class="hover:bg-gray-50 transition-colors duration-200">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    #${patient.patient_id || patient.id}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${patient.first_name} ${patient.last_name}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${age !== 'N/A' ? age + ' years' : 'N/A'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${patient.gender || 'N/A'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${patient.blood_type || 'N/A'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${patient.phone || 'N/A'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                        Active
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div class="flex space-x-2">
                        <button onclick="editPatient(${patient.id})" 
                                class="text-medora-600 hover:text-medora-900 transition-colors duration-200">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="deletePatient(${patient.id})" 
                                class="text-red-600 hover:text-red-900 transition-colors duration-200">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function showAddPatientModal() {
    editingPatientId = null;
    document.getElementById('patientModalTitle').textContent = 'Add New Patient';
    document.getElementById('patientForm').reset();
    document.getElementById('patientModal').classList.remove('hidden');
}

function showEditPatientModal(patientId) {
    const patient = patients.find(p => p.id === patientId);
    if (!patient) return;

    editingPatientId = patientId;
    document.getElementById('patientModalTitle').textContent = 'Edit Patient';
    
    // Fill form with patient data
    document.getElementById('patientFirstName').value = patient.first_name;
    document.getElementById('patientLastName').value = patient.last_name;
    document.getElementById('patientDOB').value = patient.date_of_birth;
    document.getElementById('patientGender').value = patient.gender;
    document.getElementById('patientBloodType').value = patient.blood_type || '';
    document.getElementById('patientHeight').value = patient.height || '';
    document.getElementById('patientWeight').value = patient.weight || '';
    document.getElementById('patientPhone').value = patient.phone || '';
    document.getElementById('patientAddress').value = patient.address || '';
    document.getElementById('patientAllergies').value = patient.allergies || '';
    document.getElementById('patientMedicalHistory').value = patient.medical_history || '';
    document.getElementById('patientCurrentMeds').value = patient.current_medications || '';
    document.getElementById('patientInsuranceProvider').value = patient.insurance_provider || '';
    document.getElementById('patientInsuranceNumber').value = patient.insurance_number || '';
    document.getElementById('patientEmergencyContact').value = patient.emergency_contact_name || '';
    document.getElementById('patientEmergencyPhone').value = patient.emergency_contact_phone || '';
    document.getElementById('patientEmergencyRelationship').value = patient.emergency_contact_relationship || '';
    
    document.getElementById('patientModal').classList.remove('hidden');
}

function hidePatientModal() {
    document.getElementById('patientModal').classList.add('hidden');
    editingPatientId = null;
}

async function handlePatientSubmit(e) {
    e.preventDefault();
    showLoading();

    const formData = new FormData(e.target);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        if (value) data[key] = value;
    }

    try {
        const url = editingPatientId ? 
            `${API_BASE}/patients/${editingPatientId}` : 
            `${API_BASE}/patients`;
        
        const method = editingPatientId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            showToast(result.message, 'success');
            hidePatientModal();
            loadPatients();
            loadDashboard(); // Refresh dashboard stats
        } else {
            showToast(result.error || 'Operation failed', 'error');
        }
    } catch (error) {
        showToast('Network error', 'error');
    } finally {
        hideLoading();
    }
}

async function deletePatient(patientId) {
    if (!confirm('Are you sure you want to delete this patient?')) return;

    showLoading();
    try {
        const response = await fetch(`${API_BASE}/patients/${patientId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });

        if (response.ok) {
            showToast('Patient deleted successfully', 'success');
            loadPatients();
            loadDashboard(); // Refresh dashboard stats
        } else {
            const result = await response.json();
            showToast(result.error || 'Delete failed', 'error');
        }
    } catch (error) {
        showToast('Network error', 'error');
    } finally {
        hideLoading();
    }
}

function handlePatientSearch(e) {
    const searchTerm = e.target.value.toLowerCase();
    if (searchTerm.length === 0) {
        displayPatients(patients);
        return;
    }

    const filteredPatients = patients.filter(patient => 
        patient.first_name.toLowerCase().includes(searchTerm) ||
        patient.last_name.toLowerCase().includes(searchTerm) ||
        patient.patient_id.toLowerCase().includes(searchTerm)
    );

    displayPatients(filteredPatients);
}

async function searchPatients(searchTerm) {
    if (!searchTerm.trim()) return;

    showLoading();
    try {
        const response = await fetch(`${API_BASE}/patients/search?q=${encodeURIComponent(searchTerm)}`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            displayPatients(data.patients);
        } else {
            showToast('Search failed', 'error');
        }
    } catch (error) {
        showToast('Network error', 'error');
    } finally {
        hideLoading();
    }
}

// Profile functions
function loadProfile() {
    if (!currentUser) return;

    document.getElementById('profileName').textContent = `${currentUser.first_name} ${currentUser.last_name}`;
    document.getElementById('profileEmail').textContent = currentUser.email;
    document.getElementById('profileRole').textContent = `Role: ${currentUser.role}`;
    
    document.getElementById('profileFirstName').value = currentUser.first_name;
    document.getElementById('profileLastName').value = currentUser.last_name;
    document.getElementById('profilePhone').value = currentUser.phone || '';
}

// Patient View functions
async function loadPatientView() {
    if (!currentUser) return;
    
    showLoading();
    try {
        // Fetch the current user's patient data
        const response = await fetch(`${API_BASE}/patients/my-patient`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });
        
        if (response.ok) {
            const patientData = await response.json();
            displayPatientView(patientData);
        } else if (response.status === 404) {
            // No patient record found, show message
            showToast('No patient record found. Please contact an administrator to create your patient record.', 'warning');
            document.getElementById('patientViewPage').innerHTML = `
                <div class="max-w-4xl mx-auto text-center py-12">
                    <div class="text-gray-500">
                        <i class="fas fa-user-injured text-6xl mb-6 block"></i>
                        <h2 class="text-2xl font-bold text-gray-900 mb-4">No Patient Record Found</h2>
                        <p class="text-lg text-gray-600 mb-6">We couldn't find your patient record in our system.</p>
                        <p class="text-gray-500">Please contact an administrator or doctor to create your patient record.</p>
                    </div>
                </div>
            `;
        } else {
            showToast('Failed to load health data', 'error');
        }
        
    } catch (error) {
        showToast('Network error loading health data', 'error');
    } finally {
        hideLoading();
    }
}

function displayPatientView(patientData) {
    // Populate patient view page with data
    document.getElementById('patientViewId').textContent = patientData.patient_id || '-';
    document.getElementById('patientViewName').textContent = `${patientData.first_name} ${patientData.last_name}` || '-';
    document.getElementById('patientViewDOB').textContent = patientData.date_of_birth ? new Date(patientData.date_of_birth).toLocaleDateString() : '-';
    document.getElementById('patientViewGender').textContent = patientData.gender || '-';
    document.getElementById('patientViewBloodType').textContent = patientData.blood_type || '-';
    document.getElementById('patientViewPhone').textContent = patientData.phone || '-';
    document.getElementById('patientViewAddress').textContent = patientData.address || '-';
    
    // Medical information
    if (patientData.allergies) {
        document.getElementById('patientViewAllergies').innerHTML = `<p class="text-red-600 font-medium">${patientData.allergies}</p>`;
    }
    
    if (patientData.current_medications) {
        document.getElementById('patientViewMedications').innerHTML = `<p class="text-blue-600 font-medium">${patientData.current_medications}</p>`;
    }
    
    if (patientData.medical_history) {
        document.getElementById('patientViewMedicalHistory').innerHTML = `<p class="text-gray-700">${patientData.medical_history}</p>`;
    }
    
    // Insurance information
    document.getElementById('patientViewInsuranceProvider').textContent = patientData.insurance_provider || '-';
    document.getElementById('patientViewInsuranceNumber').textContent = patientData.insurance_number || '-';
    
    // Emergency contact
    document.getElementById('patientViewEmergencyName').textContent = patientData.emergency_contact_name || '-';
    document.getElementById('patientViewEmergencyPhone').textContent = patientData.emergency_contact_phone || '-';
    document.getElementById('patientViewEmergencyRelationship').textContent = patientData.emergency_contact_relationship || '-';
}

async function handleProfileUpdate(e) {
    e.preventDefault();
    showLoading();

    const formData = new FormData(e.target);
    const data = {
        first_name: formData.get('first_name'),
        last_name: formData.get('last_name'),
        phone: formData.get('phone')
    };

    try {
        const response = await fetch(`${API_BASE}/profile`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            currentUser = result.user;
            localStorage.setItem('medora_user', JSON.stringify(currentUser));
            userName.textContent = `${currentUser.first_name} ${currentUser.last_name}`;
            showToast('Profile updated successfully', 'success');
            loadProfile();
        } else {
            showToast(result.error || 'Update failed', 'error');
        }
    } catch (error) {
        showToast('Network error', 'error');
    } finally {
        hideLoading();
    }
}

// User Management Functions
async function loadUsers() {
    showLoading();
    try {
        const response = await fetch(`${API_BASE}/users`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            displayUsers(data.users);
            updateUserStats(data.users);
            setupPagination(data.pagination);
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to load users', 'error');
        }
    } catch (error) {
        showToast('Network error loading users', 'error');
    } finally {
        hideLoading();
    }
}

function displayUsers(users) {
    const tbody = document.getElementById('usersTableBody');
    
    if (users.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="11" class="px-6 py-12 text-center">
                    <div class="text-gray-500">
                        <i class="fas fa-users text-4xl mb-4 block"></i>
                        <p class="text-lg font-medium">No users found</p>
                        <p class="text-sm">Start by registering new users to see them here</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = users.map(user => `
        <tr class="user-row hover:bg-gray-50 transition-colors duration-200" data-user-id="${user.id}">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${user.id}</td>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                    <div class="w-8 h-8 bg-gradient-to-r from-medora-500 to-blue-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
                        ${user.username.charAt(0).toUpperCase()}
                    </div>
                    <div class="ml-3">
                        <div class="text-sm font-medium text-gray-900">${user.username}</div>
                    </div>
                </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${user.email}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${user.first_name}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${user.last_name}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${user.phone || '-'}</td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    user.role === 'admin' ? 'bg-red-100 text-red-800' :
                    user.role === 'doctor' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                }">
                    ${user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    user.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                }">
                    ${user.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${formatDate(user.created_at)}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-medora-100 text-medora-800">
                    ${user.total_patients}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <div class="flex space-x-2">
                    <button onclick="editUser(${user.id})" title="Edit User" 
                            class="text-medora-600 hover:text-medora-900 transition-colors duration-200">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button onclick="deleteUser(${user.id})" title="Delete User" 
                            class="text-red-600 hover:text-red-900 transition-colors duration-200 ${user.id === currentUser?.id ? 'opacity-50 cursor-not-allowed' : ''}" 
                            ${user.id === currentUser?.id ? 'disabled' : ''}>
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function updateUserStats(users) {
    const totalUsers = users.length;
    const activeUsers = users.filter(u => u.is_active).length;
    const adminUsers = users.filter(u => u.role === 'admin').length;
    const regularUsers = users.filter(u => u.role === 'user').length;

    document.getElementById('totalUsers').textContent = totalUsers;
    document.getElementById('activeUsers').textContent = activeUsers;
    document.getElementById('adminUsers').textContent = adminUsers;
    document.getElementById('regularUsers').textContent = regularUsers;
}

function setupPagination(pagination) {
    const paginationDiv = document.getElementById('usersPagination');
    
    if (pagination.pages <= 1) {
        paginationDiv.innerHTML = '';
        return;
    }

    let paginationHTML = '<div class="flex items-center justify-center space-x-2">';
    
    // Previous button
    if (pagination.has_prev) {
        paginationHTML += `
            <button onclick="loadUsersPage(${pagination.page - 1})" 
                    class="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 hover:text-gray-700 transition-colors duration-200">
                <i class="fas fa-chevron-left mr-1"></i>Previous
            </button>`;
    }
    
    // Page numbers
    for (let i = 1; i <= pagination.pages; i++) {
        if (i === pagination.page) {
            paginationHTML += `
                <span class="px-3 py-2 text-sm font-medium text-white bg-medora-600 border border-medora-600 rounded-md">
                    ${i}
                </span>`;
        } else {
            paginationHTML += `
                <button onclick="loadUsersPage(${i})" 
                        class="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 hover:text-gray-700 transition-colors duration-200">
                    ${i}
                </button>`;
        }
    }
    
    // Next button
    if (pagination.has_next) {
        paginationHTML += `
            <button onclick="loadUsersPage(${pagination.page + 1})" 
                    class="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 hover:text-gray-700 transition-colors duration-200">
                Next<i class="fas fa-chevron-right ml-1"></i>
            </button>`;
    }
    
    paginationHTML += '</div>';
    paginationDiv.innerHTML = paginationHTML;
}

async function loadUsersPage(page) {
    showLoading();
    try {
        const response = await fetch(`${API_BASE}/users?page=${page}`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            displayUsers(data.users);
            updateUserStats(data.users);
            setupPagination(data.pagination);
        } else {
            showToast('Failed to load users page', 'error');
        }
    } catch (error) {
        showToast('Network error', 'error');
    } finally {
        hideLoading();
    }
}

async function editUser(userId) {
    // For now, just show a message - you can expand this later
    showToast('Edit user functionality coming soon!', 'info');
}

async function deleteUser(userId) {
    if (!confirm('Are you sure you want to deactivate this user? This action cannot be undone.')) {
        return;
    }

    showLoading();
    try {
        const response = await fetch(`${API_BASE}/users/${userId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });

        if (response.ok) {
            showToast('User deactivated successfully', 'success');
            loadUsers(); // Refresh the user list
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to deactivate user', 'error');
        }
    } catch (error) {
        showToast('Network error', 'error');
    } finally {
        hideLoading();
    }
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

// Add event listeners for user management
function setupUserManagement() {
    const refreshUsersBtn = document.getElementById('refreshUsersBtn');
    const exportUsersBtn = document.getElementById('exportUsersBtn');
    
    if (refreshUsersBtn) {
        refreshUsersBtn.addEventListener('click', loadUsers);
    }
    
    if (exportUsersBtn) {
        exportUsersBtn.addEventListener('click', exportUsers);
    }
}

function exportUsers() {
    // Simple export functionality - you can enhance this later
    showToast('Export functionality coming soon!', 'info');
}

// Utility functions
// Toast notification system
function showToast(message, type = 'info', duration = 5000) {
    // Remove existing toasts
    const existingToasts = document.querySelectorAll('.toast');
    existingToasts.forEach(toast => toast.remove());
    
    const toast = document.createElement('div');
    
    // Set colors based on type
    let bgColor = 'bg-blue-500';
    let iconColor = 'text-blue-500';
    let icon = 'fas fa-info-circle';
    
    if (type === 'success') {
        bgColor = 'bg-green-500';
        iconColor = 'text-green-500';
        icon = 'fas fa-check-circle';
    } else if (type === 'error') {
        bgColor = 'bg-red-500';
        iconColor = 'text-red-500';
        icon = 'fas fa-exclamation-circle';
    } else if (type === 'warning') {
        bgColor = 'bg-yellow-500';
        iconColor = 'text-yellow-500';
        icon = 'fas fa-exclamation-triangle';
    }
    
    toast.className = `toast transform transition-all duration-300 ease-in-out translate-x-full`;
    toast.innerHTML = `
        <div class="max-w-sm w-full bg-white shadow-lg rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden">
            <div class="p-4">
                <div class="flex items-start">
                    <div class="flex-shrink-0">
                        <i class="${icon} ${iconColor} text-xl"></i>
                    </div>
                    <div class="ml-3 w-0 flex-1 pt-0.5">
                        <p class="text-sm font-medium text-gray-900">${message}</p>
                    </div>
                    <div class="ml-4 flex-shrink-0 flex">
                        <button onclick="this.closest('.toast').remove()" 
                                class="bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-medora-500">
                            <span class="sr-only">Close</span>
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
            <div class="bg-gray-50 px-4 py-3">
                <div class="text-xs text-gray-500">
                    <div class="flex items-center justify-between">
                        <span>${type.charAt(0).toUpperCase() + type.slice(1)}</span>
                        <div class="w-full bg-gray-200 rounded-full h-1 ml-2">
                            <div class="bg-${type === 'success' ? 'green' : type === 'error' ? 'red' : type === 'warning' ? 'yellow' : 'blue'}-500 h-1 rounded-full transition-all duration-200" style="width: 100%"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
        toast.classList.remove('translate-x-full');
        toast.classList.add('translate-x-0');
    }, 100);
    
    // Auto remove
    setTimeout(() => {
        if (toast.parentElement) {
            toast.classList.add('translate-x-full');
            setTimeout(() => toast.remove(), 300);
        }
    }, duration);
}

function showLoading() {
    loadingSpinner.classList.remove('hidden');
    // Disable forms during loading
    document.querySelectorAll('button[type="submit"]').forEach(btn => {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Processing...';
    });
}

function hideLoading() {
    loadingSpinner.classList.add('hidden');
    // Re-enable forms after loading
    document.querySelectorAll('button[type="submit"]').forEach(btn => {
        btn.disabled = false;
        if (btn.closest('#loginForm')) {
            btn.innerHTML = '<i class="fas fa-sign-in-alt mr-2"></i>Sign In';
        } else if (btn.closest('#registerForm')) {
            btn.innerHTML = '<i class="fas fa-user-plus mr-2"></i>Create Account';
        } else {
            btn.innerHTML = 'Submit';
        }
    });
}

// Global functions for onclick handlers
window.editPatient = function(patientId) {
    showEditPatientModal(patientId);
};

window.deletePatient = function(patientId) {
    deletePatient(patientId);
};

window.testFormSubmission = function() {
    testFormSubmission();
}; 

// Mobile navigation toggle
function toggleMobileNav() {
    const navMenu = document.getElementById('navMenu');
    navMenu.classList.toggle('hidden');
} 

// Appointment functions
async function loadAppointments() {
    try {
        showLoading();
        const response = await fetch(`${API_BASE}/appointments`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            displayAppointments(data.appointments);
        } else {
            const errorData = await response.json();
            showToast(errorData.error || 'Failed to load appointments', 'error');
        }
    } catch (error) {
        console.error('Error loading appointments:', error);
        showToast('Failed to load appointments', 'error');
    } finally {
        hideLoading();
    }
}

function displayAppointments(appointments) {
    const tbody = document.getElementById('appointmentsTableBody');
    
    if (!appointments || appointments.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="px-6 py-8 text-center text-gray-500">
                    <div class="flex flex-col items-center">
                        <i class="fas fa-calendar-times text-4xl text-gray-300 mb-4"></i>
                        <p class="text-lg font-medium text-gray-700 mb-2">No appointments found</p>
                        <p class="text-gray-500">Start scheduling appointments for your patients</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = appointments.map(appointment => `
        <tr class="hover:bg-gray-50 transition-colors duration-200">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                #${appointment.id}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${appointment.patient_name || 'N/A'}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${formatDate(appointment.appointment_date)}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${formatTime(appointment.appointment_time)}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${appointment.reason || 'N/A'}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    appointment.status === 'Scheduled' ? 'bg-blue-100 text-blue-800' :
                    appointment.status === 'Completed' ? 'bg-green-100 text-green-800' :
                    'bg-red-100 text-red-800'
                }">
                    ${appointment.status}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${appointment.doctor_name || 'N/A'}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <div class="flex space-x-2">
                    <button onclick="editAppointment(${appointment.id})" 
                            class="text-medora-600 hover:text-medora-900 transition-colors duration-200">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button onclick="deleteAppointment(${appointment.id})" 
                            class="text-red-600 hover:text-red-900 transition-colors duration-200">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

function formatTime(timeString) {
    if (!timeString) return 'N/A';
    return timeString;
}

function editAppointment(appointmentId) {
    // TODO: Implement edit appointment functionality
    showToast('Edit appointment functionality coming soon!', 'info');
}

function deleteAppointment(appointmentId) {
    if (confirm('Are you sure you want to delete this appointment?')) {
        // TODO: Implement delete appointment functionality
        showToast('Delete appointment functionality coming soon!', 'info');
    }
}

// Add event listeners for appointment buttons
document.addEventListener('DOMContentLoaded', function() {
    const addAppointmentBtn = document.getElementById('addAppointmentBtn');
    const searchAppointmentsBtn = document.getElementById('searchAppointmentsBtn');
    
    if (addAppointmentBtn) {
        addAppointmentBtn.addEventListener('click', function() {
            showToast('Add appointment functionality coming soon!', 'info');
        });
    }
    
    if (searchAppointmentsBtn) {
        searchAppointmentsBtn.addEventListener('click', function() {
            // TODO: Implement appointment search
            showToast('Appointment search functionality coming soon!', 'info');
        });
    }
    
    // Add event listeners for patient page form
    const addPatientPageForm = document.getElementById('addPatientPageForm');
    const cancelAddPatientBtn = document.getElementById('cancelAddPatientBtn');
    
    if (addPatientPageForm) {
        addPatientPageForm.addEventListener('submit', handleAddPatientPageSubmit);
    }
    
    if (cancelAddPatientBtn) {
        cancelAddPatientBtn.addEventListener('click', function() {
            navigateToPage('patients');
        });
    }
});

// Function to show the Add Patient page
function showAddPatientPage() {
    console.log('showAddPatientPage called');
    
    // Hide all pages
    document.querySelectorAll('.page-content').forEach(page => {
        page.classList.add('hidden');
    });
    
    // Show add patient page
    const addPatientPage = document.getElementById('addPatientPage');
    if (addPatientPage) {
        addPatientPage.classList.remove('hidden');
        console.log('Add Patient page shown');
    } else {
        console.error('Add Patient page not found!');
        return;
    }
    
    // Update navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    const navLink = document.querySelector('[data-page="addPatient"]');
    if (navLink) {
        navLink.classList.add('active');
        console.log('Navigation updated');
    }
    
    // Reset form
    const form = document.getElementById('addPatientPageForm');
    if (form) {
        form.reset();
        console.log('Form reset');
        
        // Add progress tracking to all form fields
        const allFields = form.querySelectorAll('input, select, textarea');
        console.log('Found', allFields.length, 'form fields');
        
        allFields.forEach(field => {
            field.addEventListener('input', updateFormProgress);
            field.addEventListener('change', updateFormProgress);
        });
        
        // Initialize progress
        updateFormProgress();
        
        // Generate and display a preview patient ID
        generatePatientIdPreview();
        
        // Test form elements
        const testFields = [
            'addPatientFirstName',
            'addPatientLastName', 
            'addPatientDOB',
            'addPatientGender'
        ];
        
        testFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                console.log(`✓ Field ${fieldId} found`);
            } else {
                console.error(`✗ Field ${fieldId} NOT found`);
            }
        });
        
        console.log('Add Patient page setup complete');
        
        // Update debug info
        updateDebugInfo();
    } else {
        console.error('Add Patient form not found!');
    }
}

// Test form submission function
function testFormSubmission() {
    console.log('Testing form submission...');
    
    const form = document.getElementById('addPatientPageForm');
    if (!form) {
        console.error('Form not found for testing');
        return;
    }
    
    // Fill in some test data
    const testData = {
        'addPatientFirstName': 'John',
        'addPatientLastName': 'Doe',
        'addPatientDOB': '1990-01-01',
        'addPatientGender': 'Male',
        'addPatientPhone': '123-456-7890',
        'addPatientAddress': '123 Test Street',
        'addPatientBloodType': 'A+',
        'addPatientHeight': '175',
        'addPatientWeight': '70',
        'addPatientAllergies': 'None',
        'addPatientMedicalHistory': 'No significant history',
        'addPatientCurrentMedications': 'None',
        'addPatientInsuranceProvider': 'Test Insurance',
        'addPatientInsuranceNumber': 'INS123456',
        'addPatientEmergencyName': 'Jane Doe',
        'addPatientEmergencyPhone': '098-765-4321',
        'addPatientEmergencyRelationship': 'Spouse'
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
    
    // Update progress
    updateFormProgress();
    
    console.log('Form filled with test data');
    showToast('Form filled with test data!', 'info');
}

// Update debug information
function updateDebugInfo() {
    const form = document.getElementById('addPatientPageForm');
    const formStatus = document.getElementById('formStatus');
    const fieldsCount = document.getElementById('fieldsCount');
    
    if (form && formStatus && fieldsCount) {
        const allFields = form.querySelectorAll('input, select, textarea');
        fieldsCount.textContent = allFields.length;
        formStatus.textContent = 'Form loaded successfully';
    }
}

// Generate patient ID preview
function generatePatientIdPreview() {
    const now = new Date();
    const dateStr = now.getFullYear().toString() + 
                   (now.getMonth() + 1).toString().padStart(2, '0') + 
                   now.getDate().toString().padStart(2, '0');
    const randomStr = Math.random().toString(36).substring(2, 8).toUpperCase();
    const patientId = `MED${dateStr}${randomStr}`;
    
    // Add a preview section to show the generated ID
    const formHeader = document.querySelector('#addPatientPage .bg-gradient-to-r');
    if (formHeader) {
        const existingPreview = document.getElementById('patientIdPreview');
        if (existingPreview) {
            existingPreview.remove();
        }
        
        const previewDiv = document.createElement('div');
        previewDiv.id = 'patientIdPreview';
        previewDiv.className = 'mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg';
        previewDiv.innerHTML = `
            <div class="flex items-center justify-center">
                <i class="fas fa-id-card text-blue-500 mr-3"></i>
                <div class="text-center">
                    <p class="text-sm text-blue-600 font-medium">Generated Patient ID</p>
                    <p class="text-lg font-bold text-blue-800 font-mono">${patientId}</p>
                    <p class="text-xs text-blue-500">This ID will be assigned when the patient is created</p>
                </div>
            </div>
        `;
        
        formHeader.appendChild(previewDiv);
    }
}

// Function to handle form submission from the Add Patient page
async function handleAddPatientPageSubmit(e) {
    e.preventDefault();
    
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
        showToast(`Please fill in required fields: ${missingFields.join(', ')}`, 'error');
        return;
    }
    
    // Show confirmation dialog
    const confirmFormData = new FormData(e.target);
    const firstName = confirmFormData.get('first_name');
    const lastName = confirmFormData.get('last_name');
    const dob = confirmFormData.get('date_of_birth');
    
    const confirmMessage = `Are you sure you want to create a patient record for:\n\nName: ${firstName} ${lastName}\nDate of Birth: ${dob}\n\nThis will save the patient to the database immediately.`;
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    // Show loading state on submit button
    const submitBtn = document.getElementById('submitPatientBtn');
    const submitBtnText = document.getElementById('submitBtnText');
    if (submitBtn && submitBtnText) {
        submitBtn.disabled = true;
        submitBtnText.textContent = 'Creating Patient...';
        submitBtn.classList.add('opacity-75', 'cursor-not-allowed');
    }
    
    showLoading();

    const formData = new FormData(e.target);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        if (value) data[key] = value;
    }

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

        if (response.ok) {
            // Show success message
            const successMessage = document.getElementById('patientSuccessMessage');
            if (successMessage) {
                successMessage.classList.remove('hidden');
            }
            
            showToast('Patient created successfully!', 'success');
            
            // Reset form
            e.target.reset();
            
            // Auto-hide success message after 3 seconds
            setTimeout(() => {
                if (successMessage) {
                    successMessage.classList.add('hidden');
                }
            }, 3000);
            
            // Optionally navigate back to patients page after a delay
            setTimeout(() => {
                navigateToPage('patients');
            }, 2000);
            
        } else {
            showToast(result.error || 'Failed to create patient', 'error');
        }
    } catch (error) {
        console.error('Error creating patient:', error);
        showToast('Network error occurred', 'error');
    } finally {
        hideLoading();
    }
}

// BMI calculation function
function calculateBMI() {
    const height = document.getElementById('addPatientHeight').value;
    const weight = document.getElementById('addPatientWeight').value;
    const bmiValue = document.getElementById('bmiValue');
    const bmiCategory = document.getElementById('bmiCategory');
    
    if (height && weight && height > 0 && weight > 0) {
        const heightInMeters = height / 100;
        const bmi = (weight / (heightInMeters * heightInMeters)).toFixed(1);
        bmiValue.textContent = bmi;
        
        let category = '';
        let categoryColor = '';
        
        if (bmi < 18.5) {
            category = 'Underweight';
            categoryColor = 'text-blue-600';
        } else if (bmi < 25) {
            category = 'Normal weight';
            categoryColor = 'text-green-600';
        } else if (bmi < 30) {
            category = 'Overweight';
            categoryColor = 'text-yellow-600';
        } else {
            category = 'Obese';
            categoryColor = 'text-red-600';
        }
        
        bmiCategory.textContent = category;
        bmiCategory.className = `ml-2 text-sm ${categoryColor}`;
    } else {
        bmiValue.textContent = '-';
        bmiCategory.textContent = '-';
        bmiCategory.className = 'ml-2 text-sm text-gray-500';
    }
    
    // Update form progress
    updateFormProgress();
}

// Form progress tracking function
function updateFormProgress() {
    const form = document.getElementById('addPatientPageForm');
    if (!form) return;
    
    const requiredFields = form.querySelectorAll('input[required], select[required]');
    const optionalFields = form.querySelectorAll('input:not([required]), select:not([required]), textarea');
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