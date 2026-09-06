// =========================================================
// SUPER PEST CONTROL
// MAIN JAVASCRIPT
// =========================================================


// =========================================================
// MOBILE MENU + MORE DROPDOWN
// =========================================================

const menuBtn =
    document.getElementById("menuBtn");

const navLinks =
    document.querySelector(".nav-links");

const navDropdown =
    document.querySelector(".nav-dropdown");

const moreLink =
    document.querySelector(".more-link");


// =========================================================
// MOBILE MENU BUTTON
// =========================================================

if (menuBtn && navLinks) {

    menuBtn.addEventListener("click", function () {

        navLinks.classList.toggle("mobile-open");

        if (
            navLinks.classList.contains("mobile-open")
        ) {

            menuBtn.innerHTML = "✕";

        } else {

            menuBtn.innerHTML = "☰";

            if (navDropdown) {

                navDropdown.classList.remove(
                    "mobile-dropdown-open"
                );

            }

        }

    });

}


// =========================================================
// MORE DROPDOWN
// MOBILE = CLICK
// DESKTOP = HOVER THROUGH CSS
// =========================================================

if (moreLink && navDropdown) {

    moreLink.addEventListener("click", function (event) {

        if (window.innerWidth <= 900) {

            event.preventDefault();

            navDropdown.classList.toggle(
                "mobile-dropdown-open"
            );

        }

    });

}


// =========================================================
// CLOSE MOBILE MENU WHEN LINK IS CLICKED
// =========================================================

const mobileLinks =
    document.querySelectorAll(
        ".nav-links > a:not(.more-link), .dropdown-menu a"
    );


mobileLinks.forEach(function (link) {

    link.addEventListener("click", function () {

        if (window.innerWidth <= 900) {

            if (navLinks) {

                navLinks.classList.remove(
                    "mobile-open"
                );

            }

            if (navDropdown) {

                navDropdown.classList.remove(
                    "mobile-dropdown-open"
                );

            }

            if (menuBtn) {

                menuBtn.innerHTML = "☰";

            }

        }

    });

});


// =========================================================
// LOCATION PAGE CUSTOMER REVIEWS
// =========================================================

const districtPage =
    document.querySelector(
        "main.location-page .location-container"
    ) &&
    !/service-location\/(?:index\.html)?$/i.test(
        window.location.pathname
    );


if (
    districtPage &&
    !document.querySelector(".reviews-preview")
) {

    document.querySelector(
        "main.location-page .location-container"
    ).insertAdjacentHTML(
        "afterbegin",
        `
            <section class="section reviews-preview location-reviews">

                <div class="section-title">
                    <span>5 STAR REVIEWS</span>
                    <h2>What Customers Says<br>About us</h2>
                    <p>Trusted pest control services backed by real customer experiences.</p>
                </div>

                <div class="review-carousel">
                    <div class="review-grid-large">

                        <article class="review-card">
                            <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                            <p>I needed urgent cockroach control for my restaurant kitchen in Jodhpur before the busy weekend rush. The team accommodated a 7:00 AM Sunday morning slot. Because they used a highly effective, odorless gel bait, we didn't even have to remove our kitchen utensils or shut down prep areas. Quick, perfectly timed, and zero hassle. Easily the most professional general pest control service in Rajasthan.</p>
                            <strong>Restaurant owner, Jodhpur</strong>
                        </article>

                        <article class="review-card">
                            <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                            <p>We discovered a bed bug issue in our guest house in Ajmer and needed it handled discreetly before new guests checked in. The technicians arrived promptly at 6:00 PM for an evening appointment. They executed a highly detailed crack-and-crevice chemical spray on all the bed frames and baseboards within two hours. Fantastic scheduling, very professional behavior, and completely effective.</p>
                            <strong>Guest house owner, Ajmer</strong>
                        </article>

                        <article class="review-card">
                            <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                            <p>Finding a pest control company in Beawar that works around our factory timings was tough until we found Super Pest Control Services. They sent their technicians at 8:00 PM, right after our main production shift ended, to perform high-volume warehouse fogging and rodent baiting. They didn't disrupt our daytime operations at all. Punctual, flexible, and the mosquito and rat problems are entirely resolved.</p>
                            <strong>Factory manager, Beawar</strong>
                        </article>

                        <article class="review-card">
                            <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                            <p>Our residential society was struggling with a huge mosquito problem. We called Super Pest Control Services for their outdoor thermal fogging service. The knockdown was instant, and our outdoor garden areas are finally usable again in the evenings. If you need reliable vector and mosquito control, these guys are the absolute best!</p>
                            <strong>Residential society, Rajasthan</strong>
                        </article>

                        <article class="review-card">
                            <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                            <p>We scheduled a post-construction termite treatment for our home in Jaipur, and the team from Super Pest Control Services arrived exactly on time at 9:00 AM. They were incredibly knowledgeable, explaining their specific chemical choices—like using AlphaMethrin for our severe infestation to ensure long-term safety and maximum residual effect. By 1:00 PM, the deep-drill process was completely finished, and they cleaned up perfectly. Highly recommend them for fast, punctual, and expert termite control!</p>
                            <strong>Homeowner, Jaipur</strong>
                        </article>

                        <article class="review-card">
                            <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                            <p>I hired Super Pest Control Services for a severe termite problem at my home in Jaipur. The team was punctual, highly professional, and explained exactly how the deep-drill termite treatment would work. They used safe chemicals, sealed everything perfectly, and left no mess behind. It’s been months, and the termites are completely gone. If you need the best residential pest control in Jaipur, this is the company to call! Highly recommended.</p>
                            <strong>Residential customer, Jaipur</strong>
                        </article>

                        <article class="review-card">
                            <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                            <p>We had a major rat problem at our logistics warehouse in Beawar, and Super Pest Control Services handled it perfectly. Their rodent control team installed secure bait stations and sealed the structural entry points. Fast, professional, and our facility is finally rodent-free. Highly recommend them for commercial pest management!</p>
                            <strong>Logistics warehouse, Beawar</strong>
                        </article>

                        <article class="review-card">
                            <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                            <p>We run a busy restaurant in Jaipur and struggled with roaches in our prep areas. Super Pest Control Services was incredible. They applied an odorless gel bait that didn't require us to empty cabinets or shut down the kitchen. Highly professional, and our kitchen is completely pest-free. 5 stars!</p>
                            <strong>Restaurant owner, Jaipur</strong>
                        </article>

                        <article class="review-card">
                            <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                            <p>We had a terrible bed bug issue in our guest house in Jaipur, and Super Pest Control Services completely solved it. Their bed bug eradication treatment was incredibly thorough, targeting every mattress and baseboard. They broke the breeding cycle in just a few visits. Best pest control service in Jaipur for bed bugs!</p>
                            <strong>Guest house owner, Jaipur</strong>
                        </article>

                        <article class="review-card">
                            <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                            <p>Highly recommend Super Pest Control Services for anyone looking for residential pest control in Beawar. We hired them for a general pest treatment to deal with heavy ant and spider activity. The team was punctual, used safe indoor chemicals, and the results were immediate. Fantastic, hassle-free service!</p>
                            <strong>Residential customer, Beawar</strong>
                        </article>

                    </div>
                </div>

            </section>
        `
    );

}


// =========================================================
// REVIEW CAROUSEL TOUCH SWIPE
// =========================================================

const reviewCarousel =
    document.querySelector(".review-carousel");

const reviewTrack =
    document.querySelector(".review-grid-large");


if (reviewCarousel && reviewTrack) {

    let touchStartX = 0;
    let touchStartY = 0;
    let touchDeltaX = 0;
    let reviewIndex = 0;
    let reviewTimer;

    const reviewCards =
        reviewTrack.querySelectorAll(
            ".review-card"
        );

    const getReviewMetrics = function () {

        const reviewCard = reviewCards[0];

        if (!reviewCard) return null;

        const gap = parseFloat(
            getComputedStyle(reviewTrack).gap
        ) || 0;

        const carouselWidth = reviewCarousel.clientWidth;
        const cardWidth = reviewCard.offsetWidth;

        const visibleCards = Math.max(
            1,
            Math.floor(
                (carouselWidth + gap) /
                (cardWidth + gap)
            )
        );

        return {
            gap: gap,
            cardWidth: cardWidth,
            visibleCards: visibleCards
        };

    };

    const setReviewIndex = function (index, metrics) {

        if (!metrics) return;

        const maxIndex = Math.max(
            0,
            reviewCards.length - visibleCards
        );

        reviewIndex = Math.max(
            0,
            Math.min(index, maxIndex)
        );

        reviewTrack.style.transform =
            "translateX(-" +
            (metrics.cardWidth + metrics.gap) * reviewIndex +
            "px)";

    };

    const startReviewAutoplay = function () {

        clearInterval(reviewTimer);

        reviewTimer = setInterval(function () {

            const metrics = getReviewMetrics();

            setReviewIndex(reviewIndex + 1, metrics);

            if (reviewIndex === 0) return;

            if (
                reviewIndex >=
                reviewCards.length - metrics.visibleCards
            ) {
                setTimeout(function () {
                    setReviewIndex(0, getReviewMetrics());
                }, 2600);
            }

        }, 4200);

    };

    reviewCarousel.addEventListener(
        "touchstart",
        function (event) {

            const touch = event.touches[0];

            touchStartX = touch.clientX;
            touchStartY = touch.clientY;
            touchDeltaX = 0;

            reviewTrack.classList.add(
                "review-track-touching"
            );

            clearInterval(reviewTimer);

        },
        { passive: true }
    );

    reviewCarousel.addEventListener(
        "touchmove",
        function (event) {

            const touch = event.touches[0];

            touchDeltaX = touch.clientX - touchStartX;

            if (
                Math.abs(touchDeltaX) >
                Math.abs(touch.clientY - touchStartY)
            ) {
                event.preventDefault();
            }

        },
        { passive: false }
    );

    reviewCarousel.addEventListener(
        "touchend",
        function () {

            reviewTrack.classList.remove(
                "review-track-touching"
            );

            if (Math.abs(touchDeltaX) < 45) {
                startReviewAutoplay();
                return;
            }

            setReviewIndex(
                reviewIndex +
                (touchDeltaX < 0 ? 1 : -1),
                getReviewMetrics()
            );

            startReviewAutoplay();

        },
        { passive: true }
    );

    window.addEventListener("resize", function () {

        setReviewIndex(reviewIndex, getReviewMetrics());

    });

    setReviewIndex(0, getReviewMetrics());
    startReviewAutoplay();

}


// =========================================================
// CLOSE MORE DROPDOWN WHEN WINDOW RESIZES
// =========================================================

window.addEventListener("resize", function () {

    if (window.innerWidth > 900) {

        if (navDropdown) {

            navDropdown.classList.remove(
                "mobile-dropdown-open"
            );

        }

    }

});


// =========================================================
// HEADER SCROLL EFFECT
// =========================================================

const header =
    document.querySelector(".header");


window.addEventListener("scroll", function () {

    if (!header) return;

    if (window.scrollY > 50) {

        header.classList.add(
            "header-scrolled"
        );

    } else {

        header.classList.remove(
            "header-scrolled"
        );

    }

});


// =========================================================
// SCROLL REVEAL ANIMATION
// =========================================================

const revealElements =
    document.querySelectorAll(
        ".service-card, .why-card, .review-card, .about-content, .about-image, .feature-list > div"
    );


if ("IntersectionObserver" in window) {

    const revealObserver =
        new IntersectionObserver(

            function (entries, observer) {

                entries.forEach(function (entry) {

                    if (entry.isIntersecting) {

                        entry.target.classList.add(
                            "reveal-visible"
                        );

                        observer.unobserve(
                            entry.target
                        );

                    }

                });

            },

            {
                threshold: 0.12
            }

        );


    revealElements.forEach(function (element) {

        element.classList.add("reveal");

        revealObserver.observe(element);

    });

} else {

    revealElements.forEach(function (element) {

        element.classList.add(
            "reveal-visible"
        );

    });

}


// =========================================================
// SUPABASE CONFIGURATION
// =========================================================

const SUPABASE_URL =
    "https://yrxymyoegbxjssrcvjwr.supabase.co";


const SUPABASE_PUBLISHABLE_KEY =
    "sb_publishable_g_Gi-0zj6XXOUrxt5pYrPA_uR-Pchu0";


// =========================================================
// CONTACT / ENQUIRY FORM
// =========================================================

const locationHero =
    document.querySelector(
        "main.location-page .location-hero"
    );


if (locationHero) {

    locationHero.classList.add(
        "location-hero-with-form"
    );

    if (!document.getElementById("contactForm")) {

        locationHero.insertAdjacentHTML(
            "beforeend",
            `
                <div class="location-hero-form">

                    <div class="form-box" id="booking">

                        <form id="contactForm">

                            <div class="form-group">
                                <label>Full Name</label>
                                <input type="text" name="name" placeholder="Enter your name" required>
                            </div>

                            <div class="form-group">
                                <label>Phone Number</label>
                                <input type="tel" name="phone" placeholder="Enter 10 digit phone number" inputmode="numeric" pattern="[0-9]{10}" maxlength="10" minlength="10" oninput="this.value = this.value.replace(/[^0-9]/g, '').slice(0, 10)" required>
                            </div>

                            <div class="form-group">
                                <label>Email Address</label>
                                <input type="email" name="email" placeholder="Enter your email address" required>
                            </div>

                            <div class="form-group">
                                <label>Service</label>
                                <select name="service" required>
                                    <option value="">Select Service</option>
                                    <option>Termite &amp; Wood Borer Control</option>
                                    <option>General Pest Control (GPC)</option>
                                    <option>Rodent Management</option>
                                    <option>Vector Control &amp; Fogging</option>
                                    <option>Bed Bug Eradication</option>
                                    <option>Commercial Fumigation</option>
                                    <option>Fly Management Systems</option>
                                    <option>Sanitization &amp; Disinfection</option>
                                    <option>Commercial AMC (IPM)</option>
                                    <option>Other</option>
                                </select>
                            </div>

                            <div class="form-group">
                                <label>Message</label>
                                <textarea name="message" rows="3" placeholder="Describe your pest problem..."></textarea>
                            </div>

                            <button type="submit" class="btn-primary">
                                Send Enquiry
                            </button>

                        </form>

                    </div>

                </div>
            `
        );

    }

}

const contactForm =
    document.getElementById("contactForm");


if (contactForm) {

    contactForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            // -----------------------------------------
            // GET FORM VALUES
            // -----------------------------------------

            const name =
                contactForm
                    .querySelector('[name="name"]')
                    ?.value
                    .trim();


            const phone =
                contactForm
                    .querySelector('[name="phone"]')
                    ?.value
                    .trim();


            const email =
                contactForm
                    .querySelector('[name="email"]')
                    ?.value
                    .trim();


            const service =
                contactForm
                    .querySelector('[name="service"]')
                    ?.value;


            const message =
                contactForm
                    .querySelector('[name="message"]')
                    ?.value
                    .trim();


            // -----------------------------------------
            // VALIDATION
            // -----------------------------------------

            if (!name || !phone || !email || !service) {

                alert(
                    "Please fill all required fields."
                );

                return;

            }


            // -----------------------------------------
            // PHONE VALIDATION
            // -----------------------------------------

            if (!/^[0-9]{10}$/.test(phone)) {

                alert(
                    "Please enter a valid 10-digit phone number."
                );

                return;

            }


            // -----------------------------------------
            // SUBMIT BUTTON
            // -----------------------------------------

            const submitButton =
                contactForm.querySelector(
                    'button[type="submit"]'
                );


            if (submitButton) {

                submitButton.disabled = true;

                submitButton.textContent =
                    "Sending...";

            }


            // -----------------------------------------
            // SEND ENQUIRY TO SUPABASE
            // -----------------------------------------

            try {

                const response =
                    await fetch(
                        SUPABASE_URL +
                        "/rest/v1/enquiries",
                        {

                            method: "POST",

                            headers: {

                                "Content-Type":
                                    "application/json",

                                "apikey":
                                    SUPABASE_PUBLISHABLE_KEY,

                                "Prefer":
                                    "return=minimal"

                            },

                            body: JSON.stringify({

                                name: name,

                                phone: phone,

                                email: email,

                                service: service,

                                message: message,

                                status: "New"

                            })

                        }
                    );


                // -------------------------------------
                // GET SUPABASE RESPONSE
                // -------------------------------------

                if (!response.ok) {

                    let errorMessage =
                        "Unknown Supabase error";


                    try {

                        errorMessage =
                            await response.text();

                    } catch (e) {

                        console.error(
                            "Could not read error response."
                        );

                    }


                    console.error(
                        "SUPABASE ERROR:",
                        response.status,
                        errorMessage
                    );


                    throw new Error(
                        "Supabase returned " +
                        response.status
                    );

                }


                // -------------------------------------
                // SUCCESS
                // -------------------------------------

                alert(
                    "Thank you " +
                    name +
                    "!\n\n" +
                    "Your enquiry has been submitted successfully.\n\n" +
                    "We will contact you soon."
                );


                contactForm.reset();


            } catch (error) {

                console.error(
                    "ENQUIRY ERROR:",
                    error
                );


                alert(
                    "Unable to submit your enquiry.\n\n" +
                    "Please try again."
                );


            } finally {

                // -------------------------------------
                // RESTORE BUTTON
                // -------------------------------------

                if (submitButton) {

                    submitButton.disabled = false;

                    submitButton.textContent =
                        "Send Enquiry";

                }

            }

        }
    );

}


// =========================================================
// WHATSAPP BUTTON
// =========================================================

const whatsappButton =
    document.querySelector(".whatsapp");


if (whatsappButton) {

    whatsappButton.addEventListener(
        "click",
        function (event) {

            event.preventDefault();


            // -----------------------------------------
            // YOUR WHATSAPP BUSINESS NUMBER
            // Country code + number
            // No +, spaces or hyphens
            // -----------------------------------------

            const phone =
                "917976572984";


            // -----------------------------------------
            // DEFAULT WHATSAPP MESSAGE
            // -----------------------------------------

            const message =
                "Hello Super Pest Control, I want to book a pest control service.";


            // -----------------------------------------
            // CREATE WHATSAPP URL
            // -----------------------------------------

            const whatsappURL =
                "https://wa.me/" +
                phone +
                "?text=" +
                encodeURIComponent(message);


            // -----------------------------------------
            // OPEN WHATSAPP
            // -----------------------------------------

            window.open(
                whatsappURL,
                "_blank",
                "noopener,noreferrer"
            );

        }
    );

}


// =========================================================
// ACTIVE NAVIGATION
// =========================================================

const normalizePath = function (path) {

    const normalizedPath =
        path.replace(/\/index\.html$/i, "")
            .replace(/\/$/, "");

    return normalizedPath || "/";

};


const currentPath =
    normalizePath(
        window.location.pathname
    );


const allNavLinks =
    document.querySelectorAll(
        ".nav-links a"
    );


allNavLinks.forEach(function (link) {

    const linkPath =
        normalizePath(
            new URL(
                link.getAttribute("href"),
                window.location.origin
            ).pathname
        );


    if (linkPath === currentPath) {

        allNavLinks.forEach(
            function (item) {

                item.classList.remove(
                    "active"
                );

            }
        );


        link.classList.add("active");

    }

});


// =========================================================
// SMOOTH ANCHOR SCROLL
// =========================================================

const anchorLinks =
    document.querySelectorAll(
        'a[href^="#"]'
    );


anchorLinks.forEach(function (link) {

    link.addEventListener(
        "click",
        function (event) {

            const targetID =
                this.getAttribute("href");


            if (
                !targetID ||
                targetID === "#"
            ) {

                return;

            }


            const target =
                document.querySelector(
                    targetID
                );


            if (target) {

                event.preventDefault();


                target.scrollIntoView({

                    behavior: "smooth",

                    block: "start"

                });

            }

        }
    );

});


// =========================================================
// MOUSE PARALLAX HERO
// =========================================================

const heroVisual =
    document.querySelector(
        ".hero-visual"
    );


const heroCircle =
    document.querySelector(
        ".hero-circle"
    );


if (heroVisual && heroCircle) {

    heroVisual.addEventListener(
        "mousemove",
        function (event) {

            const rect =
                heroVisual.getBoundingClientRect();


            const x =
                event.clientX -
                rect.left;


            const y =
                event.clientY -
                rect.top;


            const moveX =
                (x / rect.width - 0.5) * 15;


            const moveY =
                (y / rect.height - 0.5) * 15;


            heroCircle.style.transform =
                `translate(${moveX}px, ${moveY}px)`;

        }
    );


    heroVisual.addEventListener(
        "mouseleave",
        function () {

            heroCircle.style.transform =
                "translate(0, 0)";

        }
    );

}


// =========================================================
// BUTTON CLICK EFFECT
// =========================================================

const buttons =
    document.querySelectorAll(
        ".btn-primary, .btn-outline, .btn-light, .nav-btn"
    );


buttons.forEach(function (button) {

    button.addEventListener(
        "click",
        function () {

            this.classList.add(
                "button-clicked"
            );


            setTimeout(function () {

                button.classList.remove(
                    "button-clicked"
                );

            }, 300);

        }
    );

});


// =========================================================
// CONSOLE MESSAGE
// =========================================================

console.log(
    "%cSUPER PEST CONTROL",
    "font-size:20px;font-weight:bold;"
);


console.log(
    "Website loaded successfully."
);


console.log(
    "Supabase enquiry system connected."
);


console.log(
    "WhatsApp button configured: +91 79765 72984"
);