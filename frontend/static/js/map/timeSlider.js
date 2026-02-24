/**
 * Time Slider — FIXED version
 * Handles year switching: 1986, 2003, 2023
 */
const TimeSlider = {
    currentYear: 1986,
    years: [1986, 2003, 2023],
    isPlaying: false,
    playInterval: null,
    onYearChange: null,

    init(callback) {
        this.onYearChange = callback;

        // Bind year buttons - use event delegation for robustness
        const container = document.getElementById('time-slider');
        if (container) {
            container.addEventListener('click', (e) => {
                const btn = e.target.closest('.time-btn');
                if (btn) {
                    const year = parseInt(btn.getAttribute('data-year'));
                    if (!isNaN(year)) {
                        this.setYear(year);
                    }
                }
            });
        }

        // Play button
        const playBtn = document.getElementById('time-play');
        if (playBtn) {
            playBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.togglePlay();
            });
        }

        // Set initial state
        this.updateUI(this.currentYear);
    },

    setYear(year) {
        if (this.currentYear === year) return;
        this.currentYear = year;
        this.updateUI(year);

        // Fire callback
        if (this.onYearChange) {
            this.onYearChange(year);
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
