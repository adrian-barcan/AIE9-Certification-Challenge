document.addEventListener('DOMContentLoaded', () => {
    const slides = document.querySelectorAll('.slide');
    const counter = document.getElementById('counter');
    const progress = document.getElementById('progress');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    let current = 0;

    function show(idx) {
        slides.forEach((s, i) => {
            s.classList.remove('active', 'prev');
            if (i === idx) s.classList.add('active');
            else if (i < idx) s.classList.add('prev');
        });
        if (counter) counter.textContent = `${idx + 1} / ${slides.length}`;
        progress.style.width = `${((idx + 1) / slides.length) * 100}%`;
        prevBtn.disabled = idx === 0;
        nextBtn.disabled = idx === slides.length - 1;
        current = idx;
    }

    prevBtn.onclick = () => { if (current > 0) show(current - 1); };
    nextBtn.onclick = () => { if (current < slides.length - 1) show(current + 1); };

    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowRight' || e.key === ' ') { e.preventDefault(); if (current < slides.length - 1) show(current + 1); }
        if (e.key === 'ArrowLeft') { if (current > 0) show(current - 1); }
        if (e.key === 'Home') show(0);
        if (e.key === 'End') show(slides.length - 1);
    });

    show(0);
});
