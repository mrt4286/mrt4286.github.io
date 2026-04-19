function changeLang(lang) {
    document.querySelectorAll('[data-tr][data-en]').forEach(el => {
        el.textContent = (lang === 'tr') ? el.getAttribute('data-tr') : el.getAttribute('data-en');
    });
    document.querySelectorAll('.lang-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
}

function reveal() {
    var reveals = document.querySelectorAll(".reveal");
    for (var i = 0; i < reveals.length; i++) {
        var windowHeight = window.innerHeight;
        var elementTop = reveals[i].getBoundingClientRect().top;
        if (elementTop < windowHeight - 100) {
            reveals[i].classList.add("active");
        }
    }
}
window.addEventListener("scroll", reveal);
reveal();

function openModal(modalId) {
    document.getElementById(modalId).style.display = "block";
    document.body.style.overflow = "hidden";
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = "none";
    document.body.style.overflow = "auto";
}

window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = "none";
        document.body.style.overflow = "auto";
    }
}

function playVideo(card) {
    const video = card.querySelector('.game-video');
    if (video) video.play().catch(() => {});
}

function pauseVideo(card) {
    const video = card.querySelector('.game-video');
    if (video) video.pause();
}