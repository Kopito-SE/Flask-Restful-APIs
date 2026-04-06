// API Configuration
const API = '/api/auth';

// Helper Functions
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function showMessage(msg, isError = true) {
    const messageDiv = document.getElementById('message');
    if (!messageDiv) return;
    
    messageDiv.textContent = msg;
    messageDiv.style.display = 'block';
    messageDiv.style.padding = '12px';
    messageDiv.style.marginBottom = '20px';
    messageDiv.style.borderRadius = '8px';
    messageDiv.style.backgroundColor = isError ? '#fee2e2' : '#dcfce7';
    messageDiv.style.color = isError ? '#991b1b' : '#166534';
    messageDiv.style.border = isError ? '1px solid #fecaca' : '1px solid #bbf7d0';
    
    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 5000);
}

function updateAvatar(name) {
    const avatarElement = document.getElementById('userAvatar');
    if (avatarElement && name) {
        const initial = name.charAt(0).toUpperCase();
        avatarElement.textContent = initial;
    }
}

// Main function to load profile
async function loadProfile() {
    console.log('🟢 Loading profile...');
    
    const token = localStorage.getItem('token');
    console.log('Token exists?', !!token);
    
    if (!token) {
        console.log('No token, redirecting to login');
        window.location.href = '/login';
        return;
    }
    
    try {
        console.log('Fetching from:', `${API}/profile`);
        
        const response = await fetch(`${API}/profile`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log('Response status:', response.status);
        
        if (response.status === 401) {
            console.log('Token expired/invalid');
            localStorage.removeItem('token');
            window.location.href = '/login';
            return;
        }
        
        const data = await response.json();
        console.log('Received data:', data);
        
        // Check if we have user data
        if (data && data.user) {
            const user = data.user;
            console.log('User object:', user);
            
            // Display profile information
            const profileDiv = document.getElementById('profile');
            if (profileDiv) {
                profileDiv.innerHTML = `
                    <div class="info-row">
                        <div class="info-label">🆔 User ID:</div>
                        <div class="info-value">${escapeHtml(user.id)}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">👤 Username:</div>
                        <div class="info-value">${escapeHtml(user.username)}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">📧 Email:</div>
                        <div class="info-value">${escapeHtml(user.email)}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">✅ Verified:</div>
                        <div class="info-value">${user.verified ? '✅ Yes' : '❌ No'}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">🔐 Account Type:</div>
                        <div class="info-value">${user.auth_provider === 'google' ? 'Google Account' : 'Email Account'}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">📅 Joined:</div>
                        <div class="info-value">${user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}</div>
                    </div>
                `;
            }
            
            // Update avatar
            updateAvatar(user.username);
            
            // Show success message
            showMessage('Profile loaded successfully!', false);
            
        } else {
            console.error('No user data in response:', data);
            showMessage('Failed to load profile data', true);
        }
        
    } catch (error) {
        console.error('Error loading profile:', error);
        showMessage('Error loading profile: ' + error.message, true);
    }
}

// Update profile function
async function updateProfile() {
    const token = localStorage.getItem('token');
    const username = document.getElementById('new_username')?.value.trim();
    const email = document.getElementById('new_email')?.value.trim();
    const button = document.getElementById('updateProfileBtn');
    
    if (!username && !email) {
        showMessage('Please enter at least one field to update', true);
        return;
    }
    
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        showMessage('Please enter a valid email address', true);
        return;
    }
    
    if (button) {
        button.disabled = true;
        button.textContent = 'Saving...';
    }
    
    try {
        const response = await fetch(`${API}/profile`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ username, email })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage(data.message || 'Profile updated successfully!', false);
            document.getElementById('new_username').value = '';
            document.getElementById('new_email').value = '';
            setTimeout(() => loadProfile(), 1000);
        } else {
            showMessage(data.error || 'Failed to update profile', true);
        }
    } catch (error) {
        console.error('Update error:', error);
        showMessage('Network error. Please try again.', true);
    } finally {
        if (button) {
            button.disabled = false;
            button.textContent = 'Save Changes';
        }
    }
}

// Change password function
async function changePassword() {
    const token = localStorage.getItem('token');
    const currentPassword = document.getElementById('current_password')?.value;
    const newPassword = document.getElementById('new_password2')?.value;
    const button = document.getElementById('changePasswordBtn');
    
    if (!currentPassword || !newPassword) {
        showMessage('Please fill in all password fields', true);
        return;
    }
    
    if (newPassword.length < 6) {
        showMessage('New password must be at least 6 characters', true);
        return;
    }
    
    if (button) {
        button.disabled = true;
        button.textContent = 'Updating...';
    }
    
    try {
        const response = await fetch(`${API}/change-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage(data.message || 'Password changed successfully!', false);
            document.getElementById('current_password').value = '';
            document.getElementById('new_password2').value = '';
        } else {
            showMessage(data.error || 'Failed to change password', true);
        }
    } catch (error) {
        console.error('Password change error:', error);
        showMessage('Network error. Please try again.', true);
    } finally {
        if (button) {
            button.disabled = false;
            button.textContent = 'Update Password';
        }
    }
}

// Logout function
async function logout() {
    const token = localStorage.getItem('token');
    
    try {
        if (token) {
            await fetch(`${API}/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
        }
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        localStorage.removeItem('token');
        window.location.href = '/login';
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard page loaded');
    
    const token = localStorage.getItem('token');
    console.log('Token in storage:', token ? 'Present' : 'Missing');
    
    if (!token) {
        console.log('No token found, redirecting to login');
        window.location.href = '/login';
        return;
    }
    
    // Load profile data
    loadProfile();
    
    // Attach event listeners
    const updateBtn = document.getElementById('updateProfileBtn');
    const changeBtn = document.getElementById('changePasswordBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    
    if (updateBtn) updateBtn.addEventListener('click', updateProfile);
    if (changeBtn) changeBtn.addEventListener('click', changePassword);
    if (logoutBtn) logoutBtn.addEventListener('click', logout);
});
// ============ SIDEBAR NAVIGATION ============

// Function to switch between pages/sections
function showPage(pageName) {
    // Get all sections
    const profileSection = document.querySelector('.profile-card');
    const updateSection = document.querySelectorAll('.settings-section');
    
    // Hide all sections first
    if (profileSection) profileSection.style.display = 'none';
    updateSection.forEach(section => section.style.display = 'none');
    
    // Show selected page
    switch(pageName) {
        case 'dashboard':
            if (profileSection) profileSection.style.display = 'block';
            updateSection.forEach(section => section.style.display = 'block');
            document.querySelector('.page-title').textContent = 'Dashboard';
            break;
            
        case 'profile':
            if (profileSection) profileSection.style.display = 'block';
            updateSection.forEach(section => section.style.display = 'none');
            document.querySelector('.page-title').textContent = 'Profile';
            break;
            
        case 'settings':
            if (profileSection) profileSection.style.display = 'none';
            updateSection.forEach(section => section.style.display = 'block');
            document.querySelector('.page-title').textContent = 'Settings';
            break;
    }
    
    // Update active class on nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('data-page') === pageName) {
            item.classList.add('active');
        }
    });
}

// Add click handlers to sidebar buttons
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const page = item.getAttribute('data-page');
        if (page) {
            showPage(page);
        }
    });
});