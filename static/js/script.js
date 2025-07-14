// Global variable to store the last deployed agent resource name
let lastDeployedResourceName = null;

// Global variables to store agent lists
let deployedAgents = [];
let agentspaceAgents = [];

// Global variable to control polling
let isPollingProgress = false;

// Show loading indicator
function showLoading() {
    document.getElementById('loading').style.display = 'flex';
}

// Hide loading indicator
function hideLoading() {
    const loading = document.getElementById('loading');
    loading.style.display = 'none';
    // Stop any ongoing polling
    stopPollingProgress();
    // Reset to default loading content
    loading.innerHTML = `
        <div class="spinner"></div>
        <p>Processing...</p>
    `;
}

// Show a specific section and hide others
function showSection(sectionId) {
    // Stop any ongoing polling when changing sections
    stopPollingProgress();
    
    // Hide menu
    document.querySelector('.menu-container').style.display = 'none';
    
    // Hide all sections
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => section.style.display = 'none');
    
    // Show selected section
    document.getElementById(sectionId).style.display = 'block';
    
    // If showing deploy section, load current config
    if (sectionId === 'deploy') {
        loadCurrentConfig();
    }
    
    // If showing configure section, clear any previous results
    if (sectionId === 'configure') {
        clearConfigureResult();
    }
    
    // If showing register section, load config and update agentspace ID display
    if (sectionId === 'register') {
        loadCurrentConfig().then(() => {
            updateRegisterAgentspaceDisplay();
        });
    }
}

// Store current configuration
let currentConfig = {
    project_id: '',
    location: '',
    model: '',
    storage_bucket: '',
    agentspace_id: ''
};

// Load current configuration from backend
async function loadCurrentConfig() {
    try {
        const response = await fetch('/config');
        const data = await response.json();
        
        if (data.success) {
            currentConfig = data.config;
            updateConfigDisplay();
        }
    } catch (error) {
        console.error('Failed to load config:', error);
        updateConfigDisplay();
    }
}

// Update configuration display
function updateConfigDisplay() {
    document.getElementById('displayProjectId').textContent = currentConfig.project_id || 'Using default from .env';
    document.getElementById('displayLocation').textContent = currentConfig.location || 'Using default from .env';
    document.getElementById('displayModel').textContent = currentConfig.model || 'Using default from .env';
    document.getElementById('displayStorageBucket').textContent = currentConfig.storage_bucket || 'Using default from .env';
    document.getElementById('displayAgentspaceId').textContent = currentConfig.agentspace_id || 'Not configured';
}

// Update register agentspace display
function updateRegisterAgentspaceDisplay() {
    const agentspaceId = currentConfig.agentspace_id || 'Not configured';
    document.getElementById('registerAgentspaceId').textContent = agentspaceId;
    
    // Auto-populate resource name if we have a last deployed agent
    if (lastDeployedResourceName && !document.getElementById('registerResourceName').value) {
        document.getElementById('registerResourceName').value = lastDeployedResourceName;
    }
}

// Show menu and hide all sections
function showMenu() {
    // Stop any ongoing polling when returning to menu
    stopPollingProgress();
    
    document.querySelector('.menu-container').style.display = 'grid';
    
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => section.style.display = 'none');
}

// Quit application
function quitApp() {
    showConfirmDialog(
        'Quit Application',
        'Are you sure you want to quit the Agent Manager?',
        () => {
            // Try to close the window (works in some browsers)
            try {
                window.close();
            } catch (e) {
                // If window.close() fails, show instructions
            }
            
            // Show a message overlay with instructions
            showQuitMessage();
        }
    );
}

// Show quit message overlay
function showQuitMessage() {
    const overlay = document.createElement('div');
    overlay.className = 'quit-overlay';
    overlay.innerHTML = `
        <div class="quit-dialog">
            <h3>Application Quit</h3>
            <p>The Agent Manager has been terminated.</p>
            <p>You can now:</p>
            <ul>
                <li>Close this browser tab/window</li>
                <li>Or press <strong>Ctrl+W</strong> (Windows/Linux) or <strong>Cmd+W</strong> (Mac) to close the tab</li>
                <li>Or navigate to another page</li>
            </ul>
            <div class="quit-buttons">
                <button onclick="window.location.href='about:blank'">Close Tab</button>
                <button onclick="location.reload()">Restart App</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(overlay);
    
    // Hide all other content
    document.querySelector('.container').style.display = 'none';
}

// Show result message
function showResult(elementId, message, isSuccess = true) {
    const resultDiv = document.getElementById(elementId);
    resultDiv.className = isSuccess ? 'result success' : 'result error';
    resultDiv.innerHTML = message;
    resultDiv.style.display = 'block';
}

// Show deployment progress
function showDeploymentProgress() {
    const loading = document.getElementById('loading');
    loading.innerHTML = `
        <div class="deployment-progress">
            <h3>Deploying Agent...</h3>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div class="progress-text" id="progressText">Initializing...</div>
            <div class="progress-details" id="progressDetails"></div>
        </div>
    `;
    loading.style.display = 'flex';
}

// Update deployment progress
async function updateDeploymentProgress() {
    try {
        const response = await fetch('/deploy/progress');
        const progress = await response.json();
        
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const progressDetails = document.getElementById('progressDetails');
        
        if (progressFill && progressText && progressDetails) {
            const percentage = (progress.step / progress.total_steps) * 100;
            progressFill.style.width = `${percentage}%`;
            progressText.textContent = `Step ${progress.step} of ${progress.total_steps}`;
            progressDetails.innerHTML = progress.message;
            
            if (progress.status === 'completed' || progress.status === 'failed') {
                isPollingProgress = false;
                return false; // Stop polling
            }
        }
        
        return isPollingProgress; // Continue polling only if still active
    } catch (error) {
        console.error('Error fetching progress:', error);
        isPollingProgress = false;
        return false;
    }
}

// Poll deployment progress
async function pollDeploymentProgress() {
    const pollInterval = 1000; // Poll every second
    isPollingProgress = true;
    
    while (isPollingProgress && await updateDeploymentProgress()) {
        await new Promise(resolve => setTimeout(resolve, pollInterval));
    }
    isPollingProgress = false;
}

// Stop polling progress
function stopPollingProgress() {
    isPollingProgress = false;
}

// Show error state in a container
function showErrorState(containerId, title, message, retryCallback) {
    const container = document.getElementById(containerId);
    container.innerHTML = `
        <div class="error-state">
            <h4>${title}</h4>
            <p>${message}</p>
            <button class="retry-btn" onclick="(${retryCallback.toString()})()">Try Again</button>
        </div>
    `;
}

// Show confirmation dialog
function showConfirmDialog(title, message, onConfirm) {
    const overlay = document.createElement('div');
    overlay.className = 'confirm-overlay';
    overlay.innerHTML = `
        <div class="confirm-dialog">
            <h3>${title}</h3>
            <p>${message}</p>
            <div class="confirm-buttons">
                <button class="confirm-btn" onclick="confirmAction()">Confirm</button>
                <button class="cancel-btn" onclick="cancelAction()">Cancel</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(overlay);
    
    // Add global functions for buttons
    window.confirmAction = () => {
        document.body.removeChild(overlay);
        onConfirm();
        delete window.confirmAction;
        delete window.cancelAction;
    };
    
    window.cancelAction = () => {
        document.body.removeChild(overlay);
        delete window.confirmAction;
        delete window.cancelAction;
    };
}


// Select delete agent from dropdown
function selectDeleteAgent(agentId) {
    if (agentId) {
        document.getElementById('agentId').value = agentId;
    }
}


// Load deployed agents for testing dropdown
async function loadTestAgents() {
    const button = document.querySelector('button[onclick="loadTestAgents()"]');
    const buttonText = button.querySelector('.button-text');
    const buttonLoading = button.querySelector('.button-loading');
    const dropdown = document.getElementById('testAgentSelect');
    
    // Show loading state
    buttonText.style.display = 'none';
    buttonLoading.style.display = 'flex';
    button.disabled = true;
    
    // Show loading in dropdown
    dropdown.className = 'loading';
    dropdown.innerHTML = '<option value="">Loading deployed agents...</option>';
    
    try {
        const response = await fetch('/list_deployed_agents');
        const data = await response.json();
        
        if (data.success) {
            dropdown.className = '';
            
            if (data.agents.length === 0) {
                dropdown.className = 'empty';
                dropdown.innerHTML = '<option value="">No deployed agents found</option>';
            } else {
                // Store agents data globally
                window.currentTestAgents = data.agents;
                
                // Populate dropdown
                let optionsHtml = '<option value="">Select a deployed agent...</option>';
                data.agents.forEach(agent => {
                    const shortName = agent.resource_name.split('/').pop();
                    optionsHtml += `<option value="${agent.resource_name}" data-display-name="${agent.display_name || 'Unnamed Agent'}">
                        ${agent.display_name || 'Unnamed Agent'} (${shortName})
                    </option>`;
                });
                dropdown.innerHTML = optionsHtml;
            }
        } else {
            dropdown.className = 'empty';
            dropdown.innerHTML = '<option value="">Failed to load agents - Try again</option>';
        }
    } catch (error) {
        dropdown.className = 'empty';
        dropdown.innerHTML = '<option value="">Connection error - Try again</option>';
    } finally {
        // Hide loading state
        buttonText.style.display = 'inline';
        buttonLoading.style.display = 'none';
        button.disabled = false;
    }
}


// Select test agent from dropdown
function selectTestAgent(resourceName) {
    if (resourceName) {
        document.getElementById('resourceName').value = resourceName;
    }
}


// Load deployed agents for registration dropdown
async function loadRegisterAgents() {
    const button = document.querySelector('button[onclick="loadRegisterAgents()"]');
    const buttonText = button.querySelector('.button-text');
    const buttonLoading = button.querySelector('.button-loading');
    const dropdown = document.getElementById('registerAgentSelect');
    
    // Show loading state
    buttonText.style.display = 'none';
    buttonLoading.style.display = 'flex';
    button.disabled = true;
    
    // Show loading in dropdown
    dropdown.className = 'loading';
    dropdown.innerHTML = '<option value="">Loading deployed agents...</option>';
    
    try {
        const response = await fetch('/list_deployed_agents');
        const data = await response.json();
        
        if (data.success) {
            dropdown.className = '';
            
            if (data.agents.length === 0) {
                dropdown.className = 'empty';
                dropdown.innerHTML = '<option value="">No deployed agents found</option>';
            } else {
                // Store agents data globally
                window.currentRegisterAgents = data.agents;
                
                // Populate dropdown
                let optionsHtml = '<option value="">Select a deployed agent...</option>';
                data.agents.forEach(agent => {
                    const shortName = agent.resource_name.split('/').pop();
                    optionsHtml += `<option value="${agent.resource_name}" data-display-name="${agent.display_name || 'Unnamed Agent'}" data-description="${agent.description || 'Agent for querying databases'}">
                        ${agent.display_name || 'Unnamed Agent'} (${shortName})
                    </option>`;
                });
                dropdown.innerHTML = optionsHtml;
            }
        } else {
            dropdown.className = 'empty';
            dropdown.innerHTML = '<option value="">Failed to load agents - Try again</option>';
        }
    } catch (error) {
        dropdown.className = 'empty';
        dropdown.innerHTML = '<option value="">Connection error - Try again</option>';
    } finally {
        // Hide loading state
        buttonText.style.display = 'inline';
        buttonLoading.style.display = 'none';
        button.disabled = false;
    }
}


// Select register agent from dropdown
function selectRegisterAgent(resourceName) {
    if (resourceName) {
        const dropdown = document.getElementById('registerAgentSelect');
        const selectedOption = dropdown.querySelector(`option[value="${resourceName}"]`);
        
        if (selectedOption) {
            document.getElementById('registerResourceName').value = resourceName;
            document.getElementById('displayName').value = selectedOption.getAttribute('data-display-name') || 'Query Agent';
            document.getElementById('description').value = selectedOption.getAttribute('data-description') || 'Agent for querying databases';
        }
    }
}


// Initialize page - stop any ongoing polling and reset deployment state
document.addEventListener('DOMContentLoaded', function() {
    stopPollingProgress();
    
    // Reset deployment progress on page load
    fetch('/deploy/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    }).catch(error => {
        console.log('Note: Could not reset deployment progress on page load');
    });
});

// Also stop polling when page is hidden or refreshed
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        stopPollingProgress();
    }
});

// Stop polling before page unload
window.addEventListener('beforeunload', function() {
    stopPollingProgress();
});

// Deploy agent
document.getElementById('deployForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    showDeploymentProgress();
    
    const formData = {
        agent_name: document.getElementById('agentName').value,
        project_id: currentConfig.project_id || null,
        location: currentConfig.location || null,
        model_name: currentConfig.model || null,
        storage_bucket: currentConfig.storage_bucket || null
    };
    
    try {
        // Start polling progress
        pollDeploymentProgress();
        
        const response = await fetch('/deploy', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData),
        });
        
        const data = await response.json();
        
        if (data.success) {
            lastDeployedResourceName = data.resource_name;
            showResult('deployResult', 
                `<strong>Success!</strong><br>
                Agent Name: ${formData.agent_name}<br>
                Resource Name: <code>${data.resource_name}</code><br>
                Project: ${data.project}<br>
                Region: ${data.region}<br>
                Model: ${data.model}`, 
                true);
        } else {
            showResult('deployResult', `<strong>Error:</strong> ${data.error}`, false);
        }
    } catch (error) {
        showResult('deployResult', `<strong>Error:</strong> ${error.message}`, false);
    } finally {
        hideLoading();
    }
});

// Edit Configuration button
document.getElementById('editConfigBtn').addEventListener('click', () => {
    document.getElementById('configSection').style.display = 'none';
    document.getElementById('editConfigSection').style.display = 'block';
    
    // Populate edit form with current values
    document.getElementById('editProjectId').value = currentConfig.project_id || '';
    document.getElementById('editLocation').value = currentConfig.location || '';
    document.getElementById('editModelName').value = currentConfig.model || '';
    document.getElementById('editStorageBucket').value = currentConfig.storage_bucket || '';
    document.getElementById('editAgentspaceId').value = currentConfig.agentspace_id || '';
});

// Save Configuration button
document.getElementById('saveConfigBtn').addEventListener('click', () => {
    // Update current config from form
    currentConfig.project_id = document.getElementById('editProjectId').value;
    currentConfig.location = document.getElementById('editLocation').value;
    currentConfig.model = document.getElementById('editModelName').value;
    currentConfig.storage_bucket = document.getElementById('editStorageBucket').value;
    currentConfig.agentspace_id = document.getElementById('editAgentspaceId').value;
    
    // Update display
    updateConfigDisplay();
    updateRegisterAgentspaceDisplay();
    
    // Hide edit section
    document.getElementById('editConfigSection').style.display = 'none';
    document.getElementById('configSection').style.display = 'block';
});

// Cancel Configuration button
document.getElementById('cancelConfigBtn').addEventListener('click', () => {
    // Hide edit section without saving
    document.getElementById('editConfigSection').style.display = 'none';
    document.getElementById('configSection').style.display = 'block';
});

// Test agent
document.getElementById('testForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Use standard loading function
    showLoading();
    
    const resourceName = document.getElementById('resourceName').value || lastDeployedResourceName;
    const query = document.getElementById('query').value;
    
    if (!resourceName) {
        showResult('testResult', '<strong>Error:</strong> No agent resource name available. Please deploy an agent first or provide a resource name.', false);
        hideLoading();
        return;
    }
    
    try {
        const response = await fetch('/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                resource_name: resourceName,
                query: query 
            }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            showResult('testResult', 
                `<strong>Query Response:</strong><br><pre>${data.response}</pre>`, 
                true);
        } else {
            showResult('testResult', `<strong>Error:</strong> ${data.error}`, false);
        }
    } catch (error) {
        showResult('testResult', `<strong>Error:</strong> ${error.message}`, false);
    } finally {
        hideLoading();
    }
});

// Register to Agentspace
document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    showLoading();
    
    const resourceName = document.getElementById('registerResourceName').value || lastDeployedResourceName;
    const displayName = document.getElementById('displayName').value;
    const description = document.getElementById('description').value;
    
    if (!resourceName) {
        showResult('registerResult', '<strong>Error:</strong> No agent resource name available. Please deploy an agent first or provide a resource name.', false);
        hideLoading();
        return;
    }
    
    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                resource_name: resourceName,
                display_name: displayName,
                description: description,
                agentspace_id: currentConfig.agentspace_id
            }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            showResult('registerResult', 
                `<strong>Success!</strong><br>
                Agent registered to Agentspace<br>
                ${data.agent_id ? `Agent ID: <code>${data.agent_id}</code>` : ''}`, 
                true);
        } else {
            showResult('registerResult', `<strong>Error:</strong> ${data.error}`, false);
        }
    } catch (error) {
        showResult('registerResult', `<strong>Error:</strong> ${error.message}`, false);
    } finally {
        hideLoading();
    }
});

// Load agents for deletion dropdown
async function loadDeleteAgents() {
    const button = document.querySelector('button[onclick="loadDeleteAgents()"]');
    const buttonText = button.querySelector('.button-text');
    const buttonLoading = button.querySelector('.button-loading');
    const dropdown = document.getElementById('deleteAgentSelect');
    
    // Show loading state
    buttonText.style.display = 'none';
    buttonLoading.style.display = 'flex';
    button.disabled = true;
    
    // Show loading in dropdown
    dropdown.className = 'loading';
    dropdown.innerHTML = '<option value="">Loading agents from Agentspace...</option>';
    
    try {
        const response = await fetch('/list_agents');
        const data = await response.json();
        
        if (data.success) {
            dropdown.className = '';
            
            if (data.agents.length === 0) {
                dropdown.className = 'empty';
                dropdown.innerHTML = '<option value="">No agents found in Agentspace</option>';
            } else {
                // Store agents data globally
                window.currentDeleteAgents = data.agents;
                
                // Populate dropdown
                let optionsHtml = '<option value="">Select an agent to delete...</option>';
                data.agents.forEach(agent => {
                    optionsHtml += `<option value="${agent.id}" data-display-name="${agent.displayName || 'Unnamed Agent'}" data-description="${agent.description || 'No description'}">
                        ${agent.displayName || 'Unnamed Agent'} (${agent.id})
                    </option>`;
                });
                dropdown.innerHTML = optionsHtml;
            }
        } else {
            dropdown.className = 'empty';
            dropdown.innerHTML = '<option value="">Failed to load agents - Try again</option>';
        }
    } catch (error) {
        dropdown.className = 'empty';
        dropdown.innerHTML = '<option value="">Connection error - Try again</option>';
    } finally {
        // Hide loading state
        buttonText.style.display = 'inline';
        buttonLoading.style.display = 'none';
        button.disabled = false;
    }
}

// Delete agent from Agentspace
document.getElementById('deleteForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const agentId = document.getElementById('agentId').value;
    
    showConfirmDialog(
        'Delete Agent',
        `Are you sure you want to delete agent "${agentId}" from Agentspace? This action cannot be undone.`,
        async () => {
            await deleteAgent(agentId);
        }
    );
});

// Actual delete function
async function deleteAgent(agentId) {
    showLoading();
    
    try {
        const response = await fetch('/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ agent_id: agentId }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            showResult('deleteResult', 
                `<strong>Success!</strong><br>Agent ${agentId} has been deleted from Agentspace.`, 
                true);
            // Clear the form
            document.getElementById('agentId').value = '';
            document.getElementById('deleteAgentSelect').selectedIndex = 0;
            // Refresh the agents dropdown
            loadDeleteAgents();
        } else {
            showResult('deleteResult', `<strong>Error:</strong> ${data.error}`, false);
        }
    } catch (error) {
        showResult('deleteResult', `<strong>Error:</strong> ${error.message}`, false);
    } finally {
        hideLoading();
    }
}

// Fetch deployed agents from Vertex AI
async function fetchDeployedAgents() {
    try {
        const response = await fetch('/list_deployed_agents');
        const data = await response.json();
        
        if (data.success) {
            deployedAgents = data.agents;
            return data.agents;
        }
    } catch (error) {
        console.error('Failed to fetch deployed agents:', error);
    }
    return [];
}

// Fetch agents from Agentspace
async function fetchAgentspaceAgents() {
    try {
        const response = await fetch('/list_agents');
        const data = await response.json();
        
        if (data.success) {
            agentspaceAgents = data.agents;
            return data.agents;
        }
    } catch (error) {
        console.error('Failed to fetch Agentspace agents:', error);
    }
    return [];
}


// Clear form functions
function clearDeployForm() {
    document.getElementById('agentName').value = '';
    const resultDiv = document.getElementById('deployResult');
    if (resultDiv) resultDiv.style.display = 'none';
}

function clearTestForm() {
    document.getElementById('resourceName').value = '';
    document.getElementById('query').value = '';
    const resultDiv = document.getElementById('testResult');
    if (resultDiv) resultDiv.style.display = 'none';
}

function clearRegisterForm() {
    document.getElementById('registerResourceName').value = '';
    document.getElementById('displayName').value = '';
    document.getElementById('description').value = '';
    const resultDiv = document.getElementById('registerResult');
    if (resultDiv) resultDiv.style.display = 'none';
}

function clearDeleteForm() {
    // Clear the agent ID input
    const agentIdField = document.getElementById('agentId');
    if (agentIdField) {
        agentIdField.value = '';
    }
    
    // Clear the result div
    const resultDiv = document.getElementById('deleteResult');
    if (resultDiv) {
        resultDiv.style.display = 'none';
    }
    
    // Also clear the agents list
    const agentsList = document.getElementById('agentsList');
    if (agentsList) {
        agentsList.innerHTML = '';
    }
}

// Load available agent types
async function loadAgentTypes() {
    const button = document.querySelector('.list-btn');
    const buttonText = button.querySelector('.button-text');
    const buttonLoading = button.querySelector('.button-loading');
    
    // Show loading state
    buttonText.style.display = 'none';
    buttonLoading.style.display = 'flex';
    button.disabled = true;
    
    // Show loading in the agent types list
    document.getElementById('agentTypesList').innerHTML = `
        <div class="loading-state">
            <div class="loading-spinner"></div>
            <p>Loading agent types...</p>
        </div>
    `;
    
    try {
        const response = await fetch('/agent_types');
        const data = await response.json();
        
        if (data.success) {
            displayAgentTypes(data.agents, data.selected);
            
            // Load current config to show detailed info
            const configResponse = await loadCurrentConfig();
            if (configResponse && configResponse.config) {
                updateCurrentAgentDisplay(configResponse.config.selected_agent, configResponse.config.agent_config);
            }
        } else {
            showErrorState('agentTypesList', 'Failed to load agent types', data.error, () => loadAgentTypes());
        }
    } catch (error) {
        showErrorState('agentTypesList', 'Connection error', error.message, () => loadAgentTypes());
    } finally {
        // Hide loading state
        buttonText.style.display = 'inline';
        buttonLoading.style.display = 'none';
        button.disabled = false;
    }
}

// Clear configure result
function clearConfigureResult() {
    const resultDiv = document.getElementById('configureResult');
    if (resultDiv) resultDiv.style.display = 'none';
    
    // Also hide the agent config details
    document.getElementById('agentConfigDetails').style.display = 'none';
    
    // Reset the agent types list to initial state
    document.getElementById('agentTypesList').innerHTML = '<p>Click "Refresh Agent Types" to load available agents...</p>';
}

// Display agent types
function displayAgentTypes(agents, selectedType) {
    const agentTypesList = document.getElementById('agentTypesList');
    
    let html = '<div class="agent-types">';
    agents.forEach(agent => {
        const isSelected = agent.type === selectedType;
        html += `
            <div class="agent-type-item ${isSelected ? 'selected' : ''}" onclick="selectAgentType('${agent.type}')">
                <h4>${agent.display_name}</h4>
                <p>${agent.description}</p>
                ${isSelected ? '<span class="selected-badge">Current</span>' : ''}
            </div>
        `;
    });
    html += '</div>';
    
    agentTypesList.innerHTML = html;
}

// Update current agent display
function updateCurrentAgentDisplay(agentType, agentConfig) {    
    if (agentConfig) {
        const configDetails = document.getElementById('configDetails');
        const envVarStatus = document.getElementById('envVarStatus');
        
        // Show config details
        let configHtml = `
            <div class="config-item">
                <label>Display Name:</label>
                <span class="config-value">${agentConfig.display_name}</span>
            </div>
            <div class="config-item">
                <label>Description:</label>
                <span class="config-value">${agentConfig.description}</span>
            </div>
            <div class="config-item">
                <label>Requirements:</label>
                <span class="config-value">${agentConfig.requirements?.join(', ') || 'None'}</span>
            </div>
        `;
        configDetails.innerHTML = configHtml;
        
        // Show environment variable status
        if (agentConfig.env_vars) {
            let envHtml = '<h4>Environment Variables:</h4>';
            for (const [varName, varConfig] of Object.entries(agentConfig.env_vars)) {
                const isSet = !!process?.env?.[varName]; // This won't work in browser, but shows the structure
                envHtml += `
                    <div class="env-var-item">
                        <span class="env-var-name">${varName}</span>
                        <span class="env-var-required">${varConfig.required ? '(Required)' : '(Optional)'}</span>
                        <span class="env-var-description">${varConfig.description}</span>
                    </div>
                `;
            }
            envVarStatus.innerHTML = envHtml;
        }
        
        document.getElementById('agentConfigDetails').style.display = 'block';
    }
}

// Select agent type
async function selectAgentType(agentType) {
    showLoading();
    
    try {
        const response = await fetch('/select_agent', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ agent_type: agentType }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            showResult('configureResult', 
                `<strong>Success!</strong><br>${data.message}
                ${data.missing_env_vars.length > 0 ? 
                    `<br><br><strong>Warning:</strong> Missing required environment variables: ${data.missing_env_vars.join(', ')}` : 
                    ''}`, 
                true);
            
            // Refresh the display
            loadAgentTypes();
        } else {
            showResult('configureResult', `<strong>Error:</strong> ${data.error}`, false);
        }
    } catch (error) {
        showResult('configureResult', `<strong>Error:</strong> ${error.message}`, false);
    } finally {
        hideLoading();
    }
}