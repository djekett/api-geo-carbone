/**
 * Time Slider — with Carbon Stock mode
 * Handles year switching: 1986, 2003, 2023
 * AND carbon stock mode toggle (CO2 button)
 *
 * Two modes:
 *   - 'temporal'  → year buttons active, play button enabled
 *   - 'carbone'   → CO2 spatialization, year buttons disabled
 */
const TimeSlider = {
    currentYear: 1986,
    years: [1986, 2003, 2023],
    isPlaying: false,
    playInterval: null,
    onYearChange: null,

    // Mode: 'temporal' (year buttons) or 'carbone' (carbon stock 2023)
    mode: 'temporal',
    onModeChange: null,

    init(callback, modeCallback) {
        this.onYearChange = callback;
        this.onModeChange = modeCallback || null;

        // Bind year buttons - use event delegation for robustness
        const container = document.getElementById('time-slider');
        if (container) {
            container.addEventListener('click', (e) => {
                const btn = e.target.closest('.time-btn');
                if (btn && !btn.classList.contains('disabled')) {
                    const year = parseInt(btn.getAttribute('data-year'));
                    if (!isNaN(year)) {
                        // If in carbone mode, switch back to temporal first
                        if (this.mode === 'carbone') {
                            this.setMode('temporal');
                        }
                        this.setYear(year);
                    }
                }
            });
        }

        // Carbon stock button
        const carboneBtn = document.getElementById('btn-stock-carbone');
        if (carboneBtn) {
            carboneBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (this.isPlaying) this.stop();
                const newMode = this.mode === 'carbone' ? 'temporal' : 'carbone';
                this.setMode(newMode);
            });
        }

        // Play button
        const playBtn = document.getElementById('time-play');
        if (playBtn) {
            playBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                // Disable play in carbon mode
                if (this.mode === 'carbone') return;
                this.togglePlay();
            });
        }

        // Set initial state
        this.updateUI(this.currentYear);
    },

    setYear(year) {
        if (this.currentYear === year && this.mode === 'temporal') return;
        this.currentYear = year;
        this.updateUI(year);

        // Fire callback
        if (this.onYearChange) {
            this.onYearChange(year);
        }
    },

    // ──── Mode switching ────
    setMode(mode) {
        if (this.mode === mode) return;
        this.mode = mode;
        this.updateModeUI();
        if (this.onModeChange) {
            this.onModeChange(mode);
        }
    },

    updateModeUI() {
        const carboneBtn = document.getElementById('btn-stock-carbone');
        const timeBtns = document.querySelectorAll('.time-btn');
        const playBtn = document.getElementById('time-play');
        const label = document.getElementById('time-label');
        const slider = document.getElementById('time-slider');

        if (this.mode === 'carbone') {
            // ── Activate CARBONE mode ──
            if (carboneBtn) carboneBtn.classList.add('active');

            // Disable year buttons with smooth transition
            timeBtns.forEach(btn => {
                btn.classList.remove('active');
                btn.classList.add('disabled');
            });

            // Disable play button
            if (playBtn) {
                playBtn.classList.add('opacity-40', 'pointer-events-none');
            }

            // Update label with CO2 indicator
            if (label) {
                label.textContent = 'CO\u2082 2023';
                label.classList.add('text-green-700', 'font-semibold');
                label.classList.remove('text-gray-400');
            }

            // Subtle border glow on the slider container
            if (slider) {
                slider.classList.add('carbone-active-glow');
            }

        } else {
            // ── Return to TEMPORAL mode ──
            if (carboneBtn) carboneBtn.classList.remove('active');

            // Re-enable year buttons
            timeBtns.forEach(btn => btn.classList.remove('disabled'));

            // Re-enable play button
            if (playBtn) {
                playBtn.classList.remove('opacity-40', 'pointer-events-none');
            }

            // Restore label
            if (label) {
                label.classList.remove('text-green-700', 'font-semibold');
                label.classList.add('text-gray-400');
            }

            // Remove glow
            if (slider) {
                slider.classList.remove('carbone-active-glow');
            }

            // Restore year highlight
            this.updateUI(this.currentYear);
        }
    },

    updateUI(year) {
        // Update ALL time buttons
        document.querySelectorAll('.time-btn').forEach(btn => {
            const btnYear = parseInt(btn.getAttribute('data-year'));
            if (btnYear === year) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // Update label
        const label = document.getElementById('time-label');
        if (label) label.textContent = year;
    },

    togglePlay() {
        if (this.isPlaying) {
            this.stop();
        } else {
            this.play();
        }
    },

    play() {
        this.isPlaying = true;
        const playBtn = document.getElementById('time-play');
        if (playBtn) playBtn.innerHTML = '<i class="fas fa-pause text-sm"></i>';

        let idx = this.years.indexOf(this.currentYear);

        this.playInterval = setInterval(() => {
            idx = (idx + 1) % this.years.length;
            this.setYear(this.years[idx]);

            // Stop at the end
            if (idx === this.years.length - 1) {
                this.stop();
            }
        }, 2500);
    },

    stop() {
        this.isPlaying = false;
        const playBtn = document.getElementById('time-play');
        if (playBtn) playBtn.innerHTML = '<i class="fas fa-play text-sm"></i>';

        if (this.playInterval) {
            clearInterval(this.playInterval);
            this.playInterval = null;
        }
    },
};
