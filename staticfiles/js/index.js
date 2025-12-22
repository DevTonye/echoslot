(function() {
    'use strict';
    
    // Mobile menu toggle
    const mobileMenu = document.getElementById('mobile-menu');
    const navLinks = document.getElementById('nav-links');
    
    if (mobileMenu && navLinks) {
        mobileMenu.addEventListener('click', () => {
            navLinks.classList.toggle('active');
        });
        
        // Close mobile menu when clicking on a link
        document.querySelectorAll('.nav-links a').forEach(link => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('active');
            });
        });
    }
    
    // Navbar scroll effect
    const navbar = document.getElementById('navbar');
    if (navbar) {
        let lastScrollY = window.scrollY;
        
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
            
            // Hide navbar on scroll down, show on scroll up
            if (window.scrollY > lastScrollY && window.scrollY > 100) {
                navbar.classList.add('hidden');
            } else {
                navbar.classList.remove('hidden');
            }
            lastScrollY = window.scrollY;
            
            // Trigger animations when elements come into view
            animateOnScroll();
        });
    }
    
    // FAQ accordion functionality (only runs if FAQ elements exist)
    const faqQuestions = document.querySelectorAll('.faq-question');
    if (faqQuestions.length > 0) {
        faqQuestions.forEach(question => {
            question.addEventListener('click', () => {
                const faqItem = question.parentElement;
                faqItem.classList.toggle('active');
            });
        });
    }
    
    // Universal scroll animation function
    // Works for all pages by checking which elements exist
    function animateOnScroll() {
        const elements = document.querySelectorAll(`
            .section-header, 
            .feature-card, 
            .step, 
            .use-case-card, 
            .value-card, 
            .team-member, 
            .contact-method, 
            .faq-item, 
            .cta-title, 
            .cta-description, 
            .cta .btn
        `);
        
        elements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const elementVisible = 150;
            
            if (elementTop < window.innerHeight - elementVisible) {
                element.classList.add('in-view');
            }
        });
    }
    
    // Helper function to add staggered delays
    function addStaggeredDelays(selector, delayMultiplier) {
        const elements = document.querySelectorAll(selector);
        if (elements.length > 0) {
            elements.forEach((element, index) => {
                element.style.transitionDelay = `${index * delayMultiplier}s`;
            });
        }
    }
    
    // Initial setup on page load
    document.addEventListener('DOMContentLoaded', () => {
        animateOnScroll();
        
        // Add staggered animation delays for all possible elements
        // Only applies to elements that exist on the current page
        addStaggeredDelays('.feature-card', 0.1);      // Index page
        addStaggeredDelays('.step', 0.2);              // Index page
        addStaggeredDelays('.use-case-card', 0.1);     // Index page
        addStaggeredDelays('.value-card', 0.1);        // About page
        addStaggeredDelays('.team-member', 0.1);       // About page
        addStaggeredDelays('.contact-method', 0.1);    // Contact page
        addStaggeredDelays('.faq-item', 0.1);          // Contact page
    });
})();