/**
 * GadgetCare Center — Main JavaScript
 * Handles: navbar scroll, hamburger menu, scroll animations, smooth scroll
 */

document.addEventListener('DOMContentLoaded', () => {
    initNavbar();
    initHamburger();
    initScrollAnimations();
    initSmoothScroll();
    initActiveNavHighlight();
});

/* ============================================
   NAVBAR — scroll state
   ============================================ */
function initNavbar() {
    const navbar = document.getElementById('navbar');
    if (!navbar) return;

    const onScroll = () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    };

    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll(); // initial check
}

/* ============================================
   HAMBURGER — mobile menu toggle
   ============================================ */
function initHamburger() {
    const btn = document.getElementById('hamburgerBtn');
    const menu = document.getElementById('navMenu');
    if (!btn || !menu) return;

    const toggleMenu = () => {
        const isOpen = menu.classList.toggle('open');
        btn.classList.toggle('open');
        btn.setAttribute('aria-expanded', isOpen);
        document.body.style.overflow = isOpen ? 'hidden' : '';
    };

    const closeMenu = () => {
        menu.classList.remove('open');
        btn.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
    };

    btn.addEventListener('click', toggleMenu);

    // Close menu when clicking a link
    menu.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', closeMenu);
    });

    // Close menu on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && menu.classList.contains('open')) {
            closeMenu();
        }
    });

    // Close menu when resizing above mobile breakpoint
    const mediaQuery = window.matchMedia('(min-width: 993px)');
    mediaQuery.addEventListener('change', (e) => {
        if (e.matches && menu.classList.contains('open')) {
            closeMenu();
        }
    });
}

/* ============================================
   SCROLL ANIMATIONS — Intersection Observer
   ============================================ */
function initScrollAnimations() {
    const elements = document.querySelectorAll('.animate-on-scroll');
    if (!elements.length) return;

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        },
        {
            threshold: 0.15,
            rootMargin: '0px 0px -40px 0px'
        }
    );

    elements.forEach(el => observer.observe(el));
}

/* ============================================
   SMOOTH SCROLL — for anchor links
   ============================================ */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(link => {
        link.addEventListener('click', (e) => {
            const id = link.getAttribute('href');
            if (id === '#') return;

            const target = document.querySelector(id);
            if (!target) return;

            e.preventDefault();

            const navHeight = document.getElementById('navbar')?.offsetHeight || 80;
            const top = target.getBoundingClientRect().top + window.scrollY - navHeight - 20;

            window.scrollTo({
                top,
                behavior: 'smooth'
            });
        });
    });
}

/* ============================================
   ACTIVE NAV — highlight current section
   ============================================ */
function initActiveNavHighlight() {
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.navbar__link');
    if (!sections.length || !navLinks.length) return;

    const sectionMap = {
        'hero': 'nav-home',
        'features': 'nav-services',
        'steps': 'nav-tracking',
        'cta': 'nav-about'
    };

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const linkId = sectionMap[entry.target.id];
                    if (!linkId) return;

                    navLinks.forEach(l => l.classList.remove('active'));
                    const activeLink = document.getElementById(linkId);
                    if (activeLink) activeLink.classList.add('active');
                }
            });
        },
        {
            threshold: 0.3,
            rootMargin: '-80px 0px -40% 0px'
        }
    );

    sections.forEach(section => observer.observe(section));
}
