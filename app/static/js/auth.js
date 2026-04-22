const API = "/api/auth"

function message(msg, isError = true) {
    const msgDiv = document.getElementById("message")
    if (!msgDiv) {
        // Avoid blowing up on pages without a message container
        console.warn("Message element not found on this page")
        return
    }
    msgDiv.innerText = msg
    msgDiv.style.color = isError ? "#dc3545" : "#28a745"
    setTimeout(() => msgDiv.innerText = "", 3000)
}

function authHeaders() {
    const token = localStorage.getItem("token")
    return token ? { "Authorization": `Bearer ${token}` } : {}
}

// REGISTER
async function register() {
    let email = document.getElementById("reg_email").value
    let username = document.getElementById("reg_username").value
    let password = document.getElementById("reg_password").value
    
    let res = await fetch(`${API}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, username, password })
    })
    
    let data = await res.json()
    
    if (res.ok) {
        message("Registration successful! Please verify your email.", false)
        setTimeout(() => {
            window.location.href = `/verify?email=${encodeURIComponent(email)}`
        }, 1500)
    } else {
        message(data.error || data.message)
    }
}

// VERIFY EMAIL
async function verifyEmail() {
    let email = document.getElementById("verify_email").value
    let code = document.getElementById("verify_code").value
    
    let res = await fetch(`${API}/verify-email`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, code })
    })
    
    let data = await res.json()
    
    if (res.ok) {
        message("Email verified! You can now login.", false)
        setTimeout(() => {
            window.location.href = "/login"
        }, 1500)
    } else {
        message(data.error || data.message)
    }
}

// RESEND CODE
async function resendCode() {
    let email = document.getElementById("verify_email").value
    
    let res = await fetch(`${API}/resend-code`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email })
    })
    
    let data = await res.json()
    
    if (res.ok) {
        message("New code sent! Check your email.", false)
    } else {
        message(data.error || data.message)
    }
}

// LOGIN
async function login() {
    const emailInput = document.getElementById("login_email") || document.getElementById("login_username")
    if (!emailInput) {
        message("Login form failed to load. Please refresh the page.")
        return
    }

    let email = emailInput.value.trim().toLowerCase()
    let password = document.getElementById("login_password").value
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/

    if (!emailPattern.test(email)) {
        message("Enter a valid email address")
        return
    }
    
    let res = await fetch(`${API}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    })
    
    let data = await res.json()
    
    if (data.token) {
        localStorage.setItem("token", data.token)
        message("Login successful! Redirecting...", false)
        setTimeout(() => {
            window.location.href = "/dashboard"
        }, 1000)
    } else {
        message(data.error || data.message)
    }
}

// REQUEST RESET
async function requestReset() {
    let email = document.getElementById("reset_email").value
    
    let res = await fetch(`${API}/request-reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email })
    })
    
    let data = await res.json()
    
    if (res.ok) {
        message("Reset code sent! Check your email.", false)
        // Store email for next page
        sessionStorage.setItem("reset_email", email)
        setTimeout(() => {
            window.location.href = "/reset-password"
        }, 1500)
    } else {
        message(data.error || data.message)
    }
}

// RESET PASSWORD
async function resetPassword() {
    let email = document.getElementById("reset_email2").value
    let code = document.getElementById("reset_code").value
    let new_password = document.getElementById("new_password").value
    
    let res = await fetch(`${API}/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, code, new_password })
    })
    
    let data = await res.json()
    
    if (res.ok) {
        message("Password reset successful! Please login.", false)
        setTimeout(() => {
            window.location.href = "/login"
        }, 1500)
    } else {
        message(data.error || data.message)
    }
}

// Auto-fill email on reset password page
if (window.location.pathname === "/reset-password") {
    const savedEmail = sessionStorage.getItem("reset_email")
    if (savedEmail) {
        document.getElementById("reset_email2").value = savedEmail
        sessionStorage.removeItem("reset_email")
    }
}

// LOGOUT
function logout() {
    localStorage.removeItem("token")
    window.location.href = "/login"
}

// Check if logged in (protect dashboard)
if (window.location.pathname === "/dashboard" && !localStorage.getItem("token")) {
    window.location.href = "/login"
}

// PROFILE HELPERS FOR DASHBOARD
async function loadProfile() {
    const token = localStorage.getItem("token")
    if (!token) return

    try {
        const res = await fetch(`${API}/profile`, {
            headers: authHeaders()
        })
        const data = await res.json()

        if (res.ok && data.user) {
            const profileDiv = document.getElementById("profile")
            if (profileDiv) {
                const { username, email, verified } = data.user
                profileDiv.innerHTML = `
                    <p><strong>Username:</strong> ${username}</p>
                    <p><strong>Email:</strong> ${email}</p>
                    <p><strong>Verified:</strong> ${verified ? "Yes" : "No"}</p>
                `
            }
        } else {
            message(data.error || "Unable to load profile")
        }
    } catch (err) {
        console.error(err)
        message("Unable to load profile right now")
    }
}

async function updateProfile() {
    const username = document.getElementById("new_username").value.trim()
    const email = document.getElementById("new_email").value.trim()

    if (!username && !email) {
        message("Enter a new username or email to update")
        return
    }

    try {
        const res = await fetch(`${API}/profile`, {
            method: "PUT",
            headers: { "Content-Type": "application/json", ...authHeaders() },
            body: JSON.stringify({ username, email })
        })
        const data = await res.json()

        if (res.ok) {
            message("Profile updated", false)
            document.getElementById("new_username").value = ""
            document.getElementById("new_email").value = ""
            loadProfile()
        } else {
            message(data.error || data.message || "Failed to update profile")
        }
    } catch (err) {
        console.error(err)
        message("Unable to update profile right now")
    }
}

async function changePassword() {
    const current_password = document.getElementById("current_password").value
    const new_password = document.getElementById("new_password2").value

    if (!current_password || !new_password) {
        message("Enter current and new password")
        return
    }

    try {
        const res = await fetch(`${API}/change-password`, {
            method: "POST",
            headers: { "Content-Type": "application/json", ...authHeaders() },
            body: JSON.stringify({ current_password, new_password })
        })
        const data = await res.json()

        if (res.ok) {
            message("Password changed successfully", false)
            document.getElementById("current_password").value = ""
            document.getElementById("new_password2").value = ""
        } else {
            message(data.error || data.message || "Failed to change password")
        }
    } catch (err) {
        console.error(err)
        message("Unable to change password right now")
    }
}

// Auto-load profile when viewing the dashboard with a token
if (window.location.pathname === "/dashboard" && localStorage.getItem("token")) {
    loadProfile()
}
