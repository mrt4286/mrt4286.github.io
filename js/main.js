// Language Switcher Logic
function changeLang(lang) {
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    document.querySelectorAll('[data-tr][data-en]').forEach(el => {
        if (lang === 'tr') {
            el.textContent = el.getAttribute('data-tr');
        } else {
            el.textContent = el.getAttribute('data-en');
        }
    });
    document.documentElement.lang = lang;
}

// Scroll Reveal Animation
function reveal() {
    var reveals = document.querySelectorAll(".reveal");
    for (var i = 0; i < reveals.length; i++) {
        var windowHeight = window.innerHeight;
        var elementTop = reveals[i].getBoundingClientRect().top;
        var elementVisible = 100; // Ekrana girme hassasiyeti
        if (elementTop < windowHeight - elementVisible) {
            reveals[i].classList.add("active");
        }
    }
}
window.addEventListener("scroll", reveal);
reveal(); // Sayfa yüklendiğinde tetikle

// Custom Cursor Logic
const cursor = document.querySelector('.cursor');
const follower = document.querySelector('.cursor-follower');

if (cursor && follower) {
    document.addEventListener('mousemove', (e) => {
        cursor.style.left = e.clientX - 10 + 'px';
        cursor.style.top = e.clientY - 10 + 'px';
        
        setTimeout(() => {
            follower.style.left = e.clientX - 20 + 'px';
            follower.style.top = e.clientY - 20 + 'px';
        }, 80);
    });

    document.querySelectorAll('a, button, .game-card, .shop-card').forEach(el => {
        el.addEventListener('mouseenter', () => {
            cursor.style.transform = 'scale(1.5)';
            cursor.style.background = 'rgba(0, 243, 255, 0.2)';
            follower.style.transform = 'scale(1.5)';
        });
        el.addEventListener('mouseleave', () => {
            cursor.style.transform = 'scale(1)';
            cursor.style.background = 'transparent';
            follower.style.transform = 'scale(1)';
        });
    });
}

// Smooth Scroll for Navigation
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Skills Animation Observer
const observerOptions = { threshold: 0.5 };
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const progressBars = entry.target.querySelectorAll('.skill-progress');
            progressBars.forEach(bar => {
                const width = bar.style.width;
                bar.style.width = '0';
                setTimeout(() => {
                    bar.style.width = width;
                }, 100);
            });
        }
    });
}, observerOptions);

document.querySelectorAll('.skills-container').forEach(section => {
    observer.observe(section);
});

// PRO FEATURE: Play Video on Hover Logic
function playVideo(cardElement) {
    const video = cardElement.querySelector('.game-video');
    if (video) {
        video.currentTime = 0; // Videoyu başa sar
        video.play().catch(e => console.log("Video otomatik oynatma engellendi: " + e));
    }
}

function pauseVideo(cardElement) {
    const video = cardElement.querySelector('.game-video');
    if (video) {
        video.pause();
    }
}

// MODAL MANTIĞI
function openModal(modalId) {
    document.getElementById(modalId).style.display = "block";
    document.body.style.overflow = "hidden"; // Arka planın kaymasını engelle
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = "none";
    document.body.style.overflow = "auto"; // Kaydırmayı geri aç
}

window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = "none";
        document.body.style.overflow = "auto";
    }
}