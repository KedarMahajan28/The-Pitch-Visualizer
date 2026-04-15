
document.addEventListener('DOMContentLoaded', () => {
  
    const styleSelect = document.getElementById('style-select');
    const narrativeInput = document.getElementById('narrative-input');
    const charCurrent = document.getElementById('char-current');
    const generateForm = document.getElementById('generate-form');
    const generateBtn = document.getElementById('generate-btn');
    const btnText = generateBtn.querySelector('.btn-text');
    const generateSpinner = document.getElementById('generate-spinner');
    const errorBanner = document.getElementById('error-message');
    const resultsSection = document.getElementById('results-section');
    const storyboardGrid = document.getElementById('storyboard-grid');
    const exportBtn = document.getElementById('export-btn');

   
    let currentStoryboard = null;
    
   
    narrativeInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        const len = this.value.length;
        charCurrent.textContent = len;
        
        if (len < 20 || len > 3000) {
            charCurrent.style.color = 'var(--error)';
        } else {
            charCurrent.style.color = 'var(--text-muted)';
        }
    });

    
    const API_BASE = window.location.protocol === 'file:' 
        ? 'http://localhost:8000/api' 
        : '/api';

   
    async function fetchStyles() {
        try {
            const res = await fetch(`${API_BASE}/styles`);
            if (!res.ok) throw new Error('Failed to load styles.');
            const data = await res.json();
            
            styleSelect.innerHTML = '';
            if (data.styles && data.styles.length > 0) {
                data.styles.forEach(style => {
                    const opt = document.createElement('option');
                    opt.value = style;
                    opt.textContent = style;
                    styleSelect.appendChild(opt);
                });
            } else {
                throw new Error('No styles returned.');
            }
        } catch (err) {
            console.error('API Error:', err);
            styleSelect.innerHTML = '<option value="">Error loading styles</option>';
            showError('Could not connect to the backend API to fetch styles.');
        }
    }

   
    generateForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const narrative = narrativeInput.value.trim();
        const style = styleSelect.value;

        if (narrative.length < 20) {
            showError('Narrative must be at least 20 characters long.');
            return;
        }

        hideError();
        setLoading(true);

        try {
            const res = await fetch(`${API_BASE}/generate-storyboard`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ narrative, style })
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || `Server error: ${res.status}`);
            }

            const data = await res.json();
            currentStoryboard = data; 
            renderStoryboard(data);
        } catch (err) {
            console.error(err);
            showError(err.message || 'An unexpected error occurred during generation.');
            resultsSection.classList.add('hidden');
        } finally {
            setLoading(false);
        }
    });

    // 3. Render results
    function renderStoryboard(data) {
        storyboardGrid.innerHTML = ''; // clear exiting
        resultsSection.classList.remove('hidden');

        // Scroll to results cleanly
        setTimeout(() => {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);

        data.scenes.forEach((scene) => {
            const card = document.createElement('div');
            card.className = 'card';
            
            let imgSrc = '';
            if (scene.image_format === 'base64') {
                imgSrc = `data:image/png;base64,${scene.image_data}`;
            } else if (scene.image_format === 'url') {
                imgSrc = scene.image_data;
            } else {
                // fallback or placeholder
                imgSrc = `data:image/svg+xml;base64,${scene.image_data}`; // fallback decoding
            }

            // Provide a purely grey box if nothing is available
            const imgElement = imgSrc && scene.image_data 
                ? `<img src="${imgSrc}" alt="Scene ${scene.beat_index + 1}" loading="lazy"/>`
                : `<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;background:#1a1a2e"><span style="color:#666;font-size:0.8rem">Image Unavailable</span></div>`;

            card.innerHTML = `
                <div class="card-img-wrapper">
                    ${imgElement}
                </div>
                <div class="card-body">
                    <div class="scene-badge">Scene ${scene.beat_index + 1}</div>
                    <p class="scene-text">${scene.original_text}</p>
                </div>
            `;
            storyboardGrid.appendChild(card);
        });
    }

    // 4. Export functionality
    exportBtn.addEventListener('click', async () => {
        if (!currentStoryboard) return;

        try {
            exportBtn.disabled = true;
            exportBtn.textContent = 'Generating...';

            const res = await fetch(`${API_BASE}/export-html`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(currentStoryboard)
            });

            if (!res.ok) throw new Error('Failed to generate export file.');

            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `storyboard_${currentStoryboard.style.replace(/\s+/g, '_')}.html`;
            document.body.appendChild(a);
            a.click();
            
            // cleanup
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (err) {
            console.error(err);
            alert('Failed to export storyboard. See console for details.');
        } finally {
            exportBtn.disabled = false;
            exportBtn.textContent = 'Export HTML';
        }
    });

    // Utilities
    function setLoading(isLoading) {
        if (isLoading) {
            generateBtn.disabled = true;
            btnText.textContent = 'Generating... (Takes ~10-30s)';
            generateSpinner.classList.remove('hidden');
        } else {
            generateBtn.disabled = false;
            btnText.textContent = 'Generate Storyboard';
            generateSpinner.classList.add('hidden');
        }
    }

    function showError(msg) {
        errorBanner.textContent = msg;
        errorBanner.classList.remove('hidden');
    }

    function hideError() {
        errorBanner.classList.add('hidden');
    }

    // Init
    fetchStyles();
});
