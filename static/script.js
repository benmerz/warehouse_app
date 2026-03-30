const statusEl = document.getElementById("status");
const refreshBtn = document.getElementById("refresh-btn");
const headEl = document.getElementById("inventory-head");
const bodyEl = document.getElementById("inventory-body");
const emptyStateEl = document.getElementById("empty-state");
const errorStateEl = document.getElementById("error-state");
const addRecordFormEl = document.getElementById("add-record-form");
const formStatusEl = document.getElementById("form-status");
const submitBtnEl = document.getElementById("submit-btn");
const cancelEditBtnEl = document.getElementById("cancel-edit-btn");
const formTitleEl = document.getElementById("form-title");

const numericFields = new Set([
	"quantity_on_hand",
	"quantity_reserved",
	"unit_cost",
	"unit_price",
	"reorder_level"
]);

let inventoryRows = [];
let editingRecordId = null;

async function loadInventory() {
	statusEl.textContent = "Loading inventory...";
	errorStateEl.classList.add("hidden");
	emptyStateEl.classList.add("hidden");

	try {
		const response = await fetch("/inventory");
		if (!response.ok) {
			throw new Error(`Request failed (${response.status})`);
		}

		const rows = await response.json();
		inventoryRows = rows;
		renderTable(rows);
		statusEl.textContent = `Loaded ${rows.length} row${rows.length === 1 ? "" : "s"}.`;
	} catch (error) {
		headEl.innerHTML = "";
		bodyEl.innerHTML = "";
		errorStateEl.textContent = `Unable to load inventory: ${error.message}`;
		errorStateEl.classList.remove("hidden");
		statusEl.textContent = "Load failed.";
	}
}

function renderTable(rows) {
	headEl.innerHTML = "";
	bodyEl.innerHTML = "";

	if (!rows.length) {
		emptyStateEl.classList.remove("hidden");
		return;
	}

	const columns = Object.keys(rows[0]);

	const headerRow = document.createElement("tr");
	columns.forEach((column) => {
		const th = document.createElement("th");
		th.textContent = column;
		headerRow.appendChild(th);
	});
	const actionsHeader = document.createElement("th");
	actionsHeader.textContent = "actions";
	headerRow.appendChild(actionsHeader);
	headEl.appendChild(headerRow);

	rows.forEach((row) => {
		const tr = document.createElement("tr");
		columns.forEach((column) => {
			const td = document.createElement("td");
			const value = row[column] ?? "";
			td.textContent = String(value);
			tr.appendChild(td);
		});

		const actionsTd = document.createElement("td");
		actionsTd.className = "row-actions";

		const editBtn = document.createElement("button");
		editBtn.type = "button";
		editBtn.className = "btn-secondary row-action-btn";
		editBtn.textContent = "Edit";
		editBtn.dataset.action = "edit";
		editBtn.dataset.id = String(row.inventory_id);

		const deleteBtn = document.createElement("button");
		deleteBtn.type = "button";
		deleteBtn.className = "btn-danger row-action-btn";
		deleteBtn.textContent = "Delete";
		deleteBtn.dataset.action = "delete";
		deleteBtn.dataset.id = String(row.inventory_id);

		actionsTd.appendChild(editBtn);
		actionsTd.appendChild(deleteBtn);
		tr.appendChild(actionsTd);
		bodyEl.appendChild(tr);
	});
}

function setFormModeCreate() {
	editingRecordId = null;
	formTitleEl.textContent = "Add Record";
	submitBtnEl.textContent = "Add Record";
	cancelEditBtnEl.classList.add("hidden");
}

function setFormModeEdit(row) {
	editingRecordId = row.inventory_id;
	formTitleEl.textContent = `Edit Record #${row.inventory_id}`;
	submitBtnEl.textContent = "Save Changes";
	cancelEditBtnEl.classList.remove("hidden");

	for (const element of addRecordFormEl.elements) {
		if (!element.name) {
			continue;
		}
		const value = row[element.name];
		element.value = value == null ? "" : String(value);
	}

	formStatusEl.textContent = `Editing record #${row.inventory_id}.`;
}

function buildPayloadFromForm() {
	const formData = new FormData(addRecordFormEl);
	const payload = {};

	for (const [key, value] of formData.entries()) {
		if (numericFields.has(key)) {
			payload[key] = Number(value);
		} else if (key === "brand") {
			payload[key] = String(value).trim() || null;
		} else {
			payload[key] = String(value).trim();
		}
	}

	return payload;
}

async function parseErrorResponse(response) {
	try {
		const data = await response.json();
		if (typeof data.detail === "string") {
			return data.detail;
		}
		return JSON.stringify(data);
	} catch {
		const text = await response.text();
		return text || `Request failed (${response.status})`;
	}
}

async function deleteRecord(inventoryId) {
	const confirmed = window.confirm(`Delete record #${inventoryId}?`);
	if (!confirmed) {
		return;
	}

	statusEl.textContent = `Deleting record #${inventoryId}...`;

	try {
		const response = await fetch(`/inventory/${inventoryId}`, {
			method: "DELETE"
		});

		if (!response.ok) {
			const message = await parseErrorResponse(response);
			throw new Error(message);
		}

		if (editingRecordId === inventoryId) {
			addRecordFormEl.reset();
			setFormModeCreate();
		}

		formStatusEl.textContent = `Deleted record #${inventoryId}.`;
		await loadInventory();
	} catch (error) {
		formStatusEl.textContent = `Unable to delete record: ${error.message}`;
		statusEl.textContent = "Delete failed.";
	}
}

refreshBtn.addEventListener("click", () => {
	loadInventory();
});

cancelEditBtnEl.addEventListener("click", () => {
	addRecordFormEl.reset();
	setFormModeCreate();
	formStatusEl.textContent = "Edit cancelled.";
});

bodyEl.addEventListener("click", async (event) => {
	const button = event.target.closest("button[data-action]");
	if (!button) {
		return;
	}

	const inventoryId = Number(button.dataset.id);
	if (!Number.isFinite(inventoryId)) {
		return;
	}

	if (button.dataset.action === "edit") {
		const row = inventoryRows.find((item) => item.inventory_id === inventoryId);
		if (!row) {
			formStatusEl.textContent = "Record not found in current table.";
			return;
		}
		setFormModeEdit(row);
		window.scrollTo({ top: 0, behavior: "smooth" });
	}

	if (button.dataset.action === "delete") {
		await deleteRecord(inventoryId);
	}
});

addRecordFormEl.addEventListener("submit", async (event) => {
	event.preventDefault();
	formStatusEl.textContent = "Saving...";
	submitBtnEl.disabled = true;
	const payload = buildPayloadFromForm();
	const endpoint = editingRecordId ? `/inventory/${editingRecordId}` : "/inventory/add_record";
	const method = editingRecordId ? "PATCH" : "POST";

	try {
		const response = await fetch(endpoint, {
			method,
			headers: {
				"Content-Type": "application/json"
			},
			body: JSON.stringify(payload)
		});

		if (!response.ok) {
			const message = await parseErrorResponse(response);
			throw new Error(message);
		}

		formStatusEl.textContent = editingRecordId
			? `Record #${editingRecordId} updated successfully.`
			: "Record added successfully.";
		addRecordFormEl.reset();
		setFormModeCreate();
		await loadInventory();
	} catch (error) {
		formStatusEl.textContent = editingRecordId
			? `Unable to update record: ${error.message}`
			: `Unable to add record: ${error.message}`;
	} finally {
		submitBtnEl.disabled = false;
	}
});

window.addEventListener("DOMContentLoaded", () => {
	setFormModeCreate();
	loadInventory();
});
