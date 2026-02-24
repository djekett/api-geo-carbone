/**
 * Import Wizard - 4-step shapefile import
 */
let importSession = null;
let previewMap = null;

function showStep(step) {
    document.querySelectorAll('.step-content').forEach(s => s.classList.add('hidden'));
    document.getElementById(`step-${step}`).classList.remove('hidden');

    document.querySelectorAll('.step-indicator').forEach(s => {
        const sStep = parseInt(s.dataset.step);
        s.classList.remove('active', 'completed');
        if (sStep === step) s.classList.add('active');
        else if (sStep < step) s.classList.add('completed');
    });
}

// File input handler
document.getElementById('file-input').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('fichier', file);

    try {
        const resp = await fetch('/api/v1/admin/import/upload/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            },
        });
        const data = await resp.json();

        if (data.error) {
            alert(data.error);
            return;
        }

        importSession = data;

        // Show preview
        document.getElementById('preview-info').innerHTML = `
            <p><strong>Fichier:</strong> ${data.fichier}</p>
            <p><strong>Features:</strong> ${data.nombre_features}</p>
            <p><strong>CRS:</strong> ${data.crs}</p>
            <p><strong>Colonnes:</strong> ${(data.colonnes || []).join(', ')}</p>
        `;

        showStep(2);

        // Init preview map
        setTimeout(() => {
            if (!previewMap) {
                previewMap = L.map('preview-map').setView([6.5, -5.5], 10);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(previewMap);
            }
            if (data.preview && data.preview.features) {
                const layer = L.geoJSON(data.preview).addTo(previewMap);
                previewMap.fitBounds(layer.getBounds());
            }
        }, 100);

        // Load forets and nomenclatures for step 3
        loadForetsAndTypes();

    } catch (err) {
        alert('Erreur upload: ' + err.message);
    }
});

async function loadForetsAndTypes() {
    try {
        const forets = await fetch('/api/v1/forets/liste/').then(r => r.json());
        const select = document.getElementById('import-foret');
        (forets || []).forEach(f => {
            const opt = document.createElement('option');
            opt.value = f.code;
            opt.textContent = f.nom;
            select.appendChild(opt);
        });

        const noms = await fetch('/api/v1/nomenclatures/').then(r => r.json());
        const typeSelect = document.getElementById('import-type');
        (noms.results || noms || []).forEach(n => {
            const opt = document.createElement('option');
            opt.value = n.code;
            opt.textContent = n.libelle_fr;
            typeSelect.appendChild(opt);
        });
    } catch (err) {
        console.error('Error loading refs:', err);
    }
}

async function executeImport() {
    if (!importSession) return;

    const foretCode = document.getElementById('import-foret').value;
    const annee = document.getElementById('import-annee').value;
    const typeCouvert = document.getElementById('import-type').value;

    try {
        const resp = await fetch('/api/v1/admin/import/execute/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({
                session_id: importSession.session_id,
                foret_code: foretCode,
                annee: annee,
                type_couvert: typeCouvert,
                mapping: {},
            }),
        });
        const data = await resp.json();

        showStep(4);
        const resultEl = document.getElementById('import-result');
        if (data.error) {
            resultEl.innerHTML = `<div class="bg-red-50 p-4 rounded-lg text-red-700"><i class="fas fa-exclamation-circle mr-2"></i>${data.error}</div>`;
        } else {
            resultEl.innerHTML = `
                <div class="bg-green-50 p-4 rounded-lg text-green-700">
                    <i class="fas fa-check-circle mr-2"></i>Import termine avec succes !
                    <p class="mt-2">${data.imported} features importees, ${data.errors} erreurs</p>
                    <p class="text-sm text-gray-500 mt-1">${data.rapport}</p>
                </div>`;
        }
    } catch (err) {
        showStep(4);
        document.getElementById('import-result').innerHTML = `<div class="bg-red-50 p-4 rounded-lg text-red-700">Erreur: ${err.message}</div>`;
    }
}

function getCookie(name) {
    const cookie = document.cookie.split(';').find(c => c.trim().startsWith(name + '='));
    return cookie ? cookie.split('=')[1] : '';
}
