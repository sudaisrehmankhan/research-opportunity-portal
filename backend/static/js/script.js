const form = document.getElementById('opportunity-form');
const listNode = document.getElementById('opportunity-list');
const messageNode = document.getElementById('message');
const paginationNode = document.getElementById('pagination');
const filterButton = document.getElementById('filter-button');

const apiBaseUrl = '/api/opportunities';
const detailUrlTemplate = document.body.dataset.detailUrlTemplate;
let currentPage = 1;
const canManage = document.body.dataset.canManage === 'true';
const isAdmin = document.body.dataset.isAdmin === 'true';
const currentUserId = Number(document.body.dataset.userId);
const submitButton = document.getElementById('submit-button');
const idInput = document.getElementById('opportunity-id');

function setMessage(text, type = 'success') {
   if (messageNode) {
       messageNode.textContent = text;
       messageNode.className = `message ${type}`;
   }
}

function resetForm() {
   if (!form) return;
   form.reset();
   idInput.value = '';
   submitButton.textContent = 'Create Opportunity';
   setMessage('');
}

function getCookie(name) {
   const item = document.cookie.split('; ').find((cookie) => cookie.startsWith(`${name}=`));
   return item ? decodeURIComponent(item.split('=').slice(1).join('=')) : '';
}

async function fetchJson(url, options = {}) {
    const response = await fetch(url, {
        headers: {
            'Content-Type': 'application/json',
            ...(options.method && options.method !== 'GET' ? { 'X-CSRFToken': getCookie('csrftoken') } : {}),
            ...(options.headers || {}),
        },
        ...options,
    });

    const contentType = response.headers.get('content-type') || '';
    const data = contentType.includes('application/json') ? await response.json() : {};

    if (!response.ok) {
        const errors = data && typeof data === 'object' ? Object.values(data).flat().join(' ') : 'Request failed.';
        throw new Error(errors || 'Request failed.');
    }

    return data;
}

function renderOpportunity(opportunity) {
    const card = document.createElement('article');
    card.className = `opportunity-card ${opportunity.status === 'Closed' ? 'closed' : ''}`;
    card.innerHTML = `
        <h3><a href="${detailUrlTemplate.replace('/0/', `/${opportunity.id}/`)}">${escapeHtml(opportunity.title)}</a></h3>
        <div class="meta">
            <span class="badge ${opportunity.status === 'Closed' ? 'closed' : ''}">${opportunity.status}</span>
            <span>${escapeHtml(opportunity.research_area)}</span>
            <span>${escapeHtml(opportunity.department)}</span>
            <span>Positions: ${opportunity.available_positions}</span>
        </div>
        <p>${escapeHtml(opportunity.description)}</p>
        <div class="meta">
            <span>Faculty: ${escapeHtml(opportunity.faculty_name)}</span>
            <span>Deadline: ${opportunity.application_deadline}</span>
        </div>
        <div class="meta">
            <span>Skills: ${escapeHtml(opportunity.required_skills)}</span>
        </div>
        ${canManage && (isAdmin || opportunity.owner_id === currentUserId) ? `
        <div class="action-row">
            <button type="button" class="secondary-btn" data-action="edit">Edit</button>
            <button type="button" class="secondary-btn" data-action="toggle">${opportunity.status === 'Open' ? 'Mark Closed' : 'Mark Open'}</button>
            <button type="button" class="danger-btn" data-action="delete">Delete</button>
        </div>` : ''}
    `;

    card.querySelector('[data-action="edit"]')?.addEventListener('click', () => populateForm(opportunity));
    card.querySelector('[data-action="toggle"]')?.addEventListener('click', () => toggleStatus(opportunity));
    card.querySelector('[data-action="delete"]')?.addEventListener('click', () => deleteOpportunity(opportunity.id));
    return card;
}

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

async function loadOpportunities() {
    listNode.innerHTML = '<div class="empty-state">Loading opportunities...</div>';
    try {
        const params = new URLSearchParams({ page: currentPage });
        const search = document.getElementById('search').value.trim();
        const department = document.getElementById('department-filter').value.trim();
        const status = document.getElementById('status-filter').value;
        if (search) params.set('search', search);
        if (department) params.set('department', department);
        if (status) params.set('status', status);
        const page = await fetchJson(`${apiBaseUrl}?${params.toString()}`);
        if (!page.results.length) {
            listNode.innerHTML = '<div class="empty-state">No research opportunities available.</div>';
            paginationNode.innerHTML = '';
            return;
        }

        listNode.innerHTML = '';
        page.results.forEach((opportunity) => {
            listNode.appendChild(renderOpportunity(opportunity));
        });
        if (!paginationNode) return;
        paginationNode.innerHTML = `
            <button type="button" class="secondary-btn" id="previous-page" ${page.previous ? '' : 'disabled'}>Previous</button>
            <span>Page ${currentPage}</span>
            <button type="button" class="secondary-btn" id="next-page" ${page.next ? '' : 'disabled'}>Next</button>
        `;
        document.getElementById('previous-page').addEventListener('click', () => {
            currentPage -= 1;
            loadOpportunities();
        });
        document.getElementById('next-page').addEventListener('click', () => {
            currentPage += 1;
            loadOpportunities();
        });
    } catch (error) {
        listNode.innerHTML = '<div class="empty-state">Unable to load opportunities.</div>';
        setMessage(error.message, 'error');
    }
}

function populateForm(opportunity) {
    idInput.value = opportunity.id;
    document.getElementById('title').value = opportunity.title;
    document.getElementById('description').value = opportunity.description;
    document.getElementById('research_area').value = opportunity.research_area;
    document.getElementById('faculty_name').value = opportunity.faculty_name;
    document.getElementById('department').value = opportunity.department;
    document.getElementById('required_skills').value = opportunity.required_skills;
    document.getElementById('available_positions').value = opportunity.available_positions;
    document.getElementById('application_deadline').value = opportunity.application_deadline;
    document.getElementById('status').value = opportunity.status;
    submitButton.textContent = 'Update Opportunity';
    document.getElementById('title').focus();
}

async function submitForm(event) {
    event.preventDefault();
    const payload = {
        title: document.getElementById('title').value,
        description: document.getElementById('description').value,
        research_area: document.getElementById('research_area').value,
        faculty_name: document.getElementById('faculty_name').value,
        department: document.getElementById('department').value,
        required_skills: document.getElementById('required_skills').value,
        available_positions: Number(document.getElementById('available_positions').value),
        application_deadline: document.getElementById('application_deadline').value,
        status: document.getElementById('status').value,
    };

    const url = idInput.value ? `${apiBaseUrl}/${idInput.value}` : apiBaseUrl;
    const method = idInput.value ? 'PUT' : 'POST';

    try {
        await fetchJson(url, {
            method,
            body: JSON.stringify(payload),
        });

        const successMessage = idInput.value
            ? 'Opportunity updated successfully.'
            : 'Opportunity created successfully.';
        resetForm();
        await loadOpportunities();
        setMessage(successMessage);
    } catch (error) {
        setMessage(error.message, 'error');
    }
}

async function toggleStatus(opportunity) {
    const updatedStatus = opportunity.status === 'Open' ? 'Closed' : 'Open';
    try {
        await fetchJson(`${apiBaseUrl}/${opportunity.id}`, {
            method: 'PUT',
            body: JSON.stringify({
                ...opportunity,
                status: updatedStatus,
            }),
        });
        setMessage(`Opportunity marked as ${updatedStatus}.`);
        await loadOpportunities();
    } catch (error) {
        setMessage(error.message, 'error');
    }
}

async function deleteOpportunity(id) {
    if (!window.confirm('Delete this research opportunity?')) {
        return;
    }

    try {
        await fetchJson(`${apiBaseUrl}/${id}`, { method: 'DELETE' });
        setMessage('Opportunity deleted successfully.');
        await loadOpportunities();
    } catch (error) {
        setMessage(error.message, 'error');
    }
}

form?.addEventListener('submit', (event) => {
    if (idInput?.value) {
        submitForm(event);
    }
});
document.getElementById('cancel-button')?.addEventListener('click', resetForm);
filterButton?.addEventListener('click', () => {
    currentPage = 1;
    loadOpportunities();
});
loadOpportunities();
