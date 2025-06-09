// Global state
let currentUser = null;
let subscriptions = [];
let analytics = {};
let categoryChart = null;

// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
    await checkAuth();
    setupEventListeners();
});

// Authentication
async function checkAuth() {
    try {
        const response = await fetch('/api/user', {
            credentials: 'include'
        });
        
        if (response.ok) {
            currentUser = await response.json();
            showDashboard();
            await loadDashboard();
        } else {
            showLanding();
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        showLanding();
    }
}

function showLanding() {
    document.getElementById('landingPage').style.display = 'block';
    document.getElementById('dashboard').style.display = 'none';
    updateNavAuth();
}

function showDashboard() {
    document.getElementById('landingPage').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
    updateNavAuth();
}

function updateNavAuth() {
    const navAuth = document.getElementById('navAuth');
    if (currentUser) {
        navAuth.innerHTML = `
            <span class="mr-4">Welcome, ${currentUser.name || currentUser.email}</span>
            ${currentUser.profile_pic ? `<img src="${currentUser.profile_pic}" class="w-8 h-8 rounded-full mr-4">` : ''}
            <button onclick="logout()" class="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600">
                <i class="fas fa-sign-out-alt mr-2"></i>Logout
            </button>
        `;
    } else {
        navAuth.innerHTML = `
            <button onclick="loginWithGoogle()" class="bg-primary text-white px-4 py-2 rounded-lg hover:opacity-90">
                <i class="fab fa-google mr-2"></i>Sign In
            </button>
        `;
    }
}

function loginWithGoogle() {
    window.location.href = '/api/auth/login';
}

function logout() {
    window.location.href = '/api/auth/logout';
}

// Dashboard
async function loadDashboard() {
    await Promise.all([
        loadSubscriptions(),
        loadAnalytics(),
        loadCatalog()
    ]);
}

async function loadSubscriptions() {
    try {
        const response = await fetch('/api/subscriptions', {
            credentials: 'include'
        });
        
        if (response.ok) {
            subscriptions = await response.json();
            renderSubscriptions();
        }
    } catch (error) {
        console.error('Failed to load subscriptions:', error);
        showToast('Failed to load subscriptions', 'error');
    }
}

async function loadAnalytics() {
    try {
        const response = await fetch('/api/analytics', {
            credentials: 'include'
        });
        
        if (response.ok) {
            analytics = await response.json();
            updateAnalytics();
        }
    } catch (error) {
        console.error('Failed to load analytics:', error);
    }
}

async function loadCatalog() {
    try {
        const response = await fetch('/api/catalog');
        if (response.ok) {
            const catalog = await response.json();
            renderCatalog(catalog);
        }
    } catch (error) {
        console.error('Failed to load catalog:', error);
    }
}

// Render functions
function renderSubscriptions() {
    const container = document.getElementById('subscriptionsList');
    
    if (subscriptions.length === 0) {
        container.innerHTML = `
            <div class="card p-8 text-center">
                <i class="fas fa-inbox text-6xl text-gray-300 mb-4"></i>
                <p class="text-gray-600 mb-4">No subscriptions yet</p>
                <button onclick="showUploadModal()" class="bg-primary text-white px-6 py-2 rounded-lg">
                    Upload Statement
                </button>
            </div>
        `;
        return;
    }
    
    container.innerHTML = subscriptions.map(sub => `
        <div class="card subscription-card p-6 flex items-center justify-between">
            <div class="flex items-center">
                <div class="text-3xl mr-4">${sub.logo_url || '💳'}</div>
                <div>
                    <h3 class="text-lg font-semibold">${sub.name}</h3>
                    <p class="text-gray-600">
                        ${sub.billing_cycle} • ${sub.category || 'Other'}
                        ${sub.detected_from === 'pdf' ? ' • <i class="fas fa-robot text-xs"></i> AI Detected' : ''}
                    </p>
                    ${sub.next_billing_date ? `<p class="text-sm text-gray-500">Next billing: ${formatDate(sub.next_billing_date)}</p>` : ''}
                </div>
            </div>
            <div class="flex items-center gap-4">
                <div class="text-right">
                    <p class="text-2xl font-bold text-primary">$${sub.amount.toFixed(2)}</p>
                    <p class="text-sm text-gray-600">/${sub.billing_cycle}</p>
                </div>
                <div class="flex gap-2">
                    <button onclick="editSubscription(${sub.id})" class="text-gray-600 hover:text-primary">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button onclick="deleteSubscription(${sub.id})" class="text-gray-600 hover:text-red-500">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

function updateAnalytics() {
    document.getElementById('monthlyTotal').textContent = `$${analytics.total_monthly || 0}`;
    document.getElementById('yearlyTotal').textContent = `$${analytics.total_yearly || 0}`;
    document.getElementById('subCount').textContent = analytics.subscription_count || 0;
    document.getElementById('avgCost').textContent = `$${analytics.average_subscription || 0}`;
    
    // Update category chart
    if (analytics.by_category) {
        updateCategoryChart(analytics.by_category);
        renderCategoryBreakdown(analytics.by_category);
    }
}

function updateCategoryChart(byCategory) {
    const ctx = document.getElementById('categoryChart').getContext('2d');
    
    if (categoryChart) {
        categoryChart.destroy();
    }
    
    const categories = Object.keys(byCategory);
    const values = Object.values(byCategory);
    
    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: categories,
            datasets: [{
                data: values,
                backgroundColor: [
                    '#FF5B04', // Orange
                    '#075056', // Midnight Green
                    '#F4D47C', // Sand Yellow
                    '#233038', // Gunmetal
                    '#D3DBDD', // Light Silver
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': $' + context.parsed.toFixed(2);
                        }
                    }
                }
            }
        }
    });
}

function renderCategoryBreakdown(byCategory) {
    const container = document.getElementById('categoryBreakdown');
    const total = Object.values(byCategory).reduce((sum, val) => sum + val, 0);
    
    container.innerHTML = Object.entries(byCategory).map(([category, amount]) => {
        const percentage = (amount / total * 100).toFixed(1);
        return `
            <div class="flex justify-between items-center">
                <span class="capitalize">${category}</span>
                <div class="flex items-center gap-2">
                    <span class="font-semibold">$${amount.toFixed(2)}</span>
                    <span class="text-sm text-gray-600">${percentage}%</span>
                </div>
            </div>
        `;
    }).join('');
}

function renderCatalog(catalog) {
    const container = document.getElementById('catalogList');
    
    container.innerHTML = catalog.map(service => `
        <button onclick="quickAddSubscription('${service.name}', ${service.suggested_price})" 
                class="card p-4 hover-lift text-left">
            <div class="text-2xl mb-2">${service.logo}</div>
            <h4 class="font-semibold">${service.name}</h4>
            <p class="text-sm text-gray-600">$${service.suggested_price}/mo</p>
        </button>
    `).join('');
}

// Event listeners
function setupEventListeners() {
    // File upload
    const fileInput = document.getElementById('fileInput');
    const uploadZone = document.getElementById('uploadZone');
    
    fileInput.addEventListener('change', handleFileSelect);
    
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });
    
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });
    
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });
    
    // Add subscription form
    document.getElementById('addSubForm').addEventListener('submit', handleAddSubscription);
}

// File handling
function handleFileSelect(e) {
    handleFiles(e.target.files);
}

async function handleFiles(files) {
    if (files.length === 0) return;
    
    const file = files[0];
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showToast('Please upload a PDF file', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    document.getElementById('uploadProgress').classList.remove('hidden');
    document.getElementById('uploadResults').classList.add('hidden');
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showUploadResults(result);
            await loadDashboard(); // Reload data
        } else {
            showToast(result.error || 'Upload failed', 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showToast('Upload failed', 'error');
    } finally {
        document.getElementById('uploadProgress').classList.add('hidden');
    }
}

function showUploadResults(result) {
    const container = document.getElementById('uploadResults');
    
    if (result.subscriptions && result.subscriptions.length > 0) {
        container.innerHTML = `
            <div class="bg-green-50 border border-green-200 p-4 rounded-lg">
                <h3 class="font-semibold text-green-800 mb-2">
                    Found ${result.subscriptions.length} subscriptions!
                </h3>
                <p class="text-sm text-gray-600 mb-3">Total monthly cost: $${result.total_monthly_cost}</p>
                <div class="space-y-2">
                    ${result.subscriptions.map(sub => `
                        <div class="flex justify-between text-sm">
                            <span>${sub.name}</span>
                            <span class="font-semibold">$${sub.amount}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        showToast(`Added ${result.subscriptions.length} subscriptions!`, 'success');
    } else {
        container.innerHTML = `
            <div class="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
                <p class="text-yellow-800">No subscriptions found in this statement</p>
            </div>
        `;
    }
    
    container.classList.remove('hidden');
}

// Subscription management
async function handleAddSubscription(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    try {
        const response = await fetch('/api/subscriptions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data),
            credentials: 'include'
        });
        
        if (response.ok) {
            showToast('Subscription added successfully!', 'success');
            closeModal('addModal');
            e.target.reset();
            await loadDashboard();
        } else {
            showToast('Failed to add subscription', 'error');
        }
    } catch (error) {
        console.error('Add subscription error:', error);
        showToast('Failed to add subscription', 'error');
    }
}

async function quickAddSubscription(name, amount) {
    const data = {
        name: name,
        amount: amount,
        billing_cycle: 'monthly',
        detected_from: 'catalog'
    };
    
    try {
        const response = await fetch('/api/subscriptions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data),
            credentials: 'include'
        });
        
        if (response.ok) {
            showToast(`${name} added successfully!`, 'success');
            closeModal('catalogModal');
            await loadDashboard();
        } else {
            showToast('Failed to add subscription', 'error');
        }
    } catch (error) {
        console.error('Quick add error:', error);
        showToast('Failed to add subscription', 'error');
    }
}

async function deleteSubscription(id) {
    if (!confirm('Are you sure you want to delete this subscription?')) return;
    
    try {
        const response = await fetch(`/api/subscriptions/${id}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (response.ok) {
            showToast('Subscription deleted', 'success');
            await loadDashboard();
        } else {
            showToast('Failed to delete subscription', 'error');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showToast('Failed to delete subscription', 'error');
    }
}

// Modals
function showUploadModal() {
    document.getElementById('uploadModal').style.display = 'block';
}

function showAddModal() {
    document.getElementById('addModal').style.display = 'block';
}

function showCatalogModal() {
    document.getElementById('catalogModal').style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Utility functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Close modals when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}