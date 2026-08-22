// =========================================================
// SUPER PEST CONTROL
// MAIN JAVASCRIPT
// =========================================================


// =========================================================
// INTRO ANIMATION - SHOW ONLY ON FIRST VISIT
// =========================================================

document.addEventListener("DOMContentLoaded", function () {

    const intro = document.getElementById("intro");

    if (!intro) return;

    const introPlayed =
        sessionStorage.getItem("pestIntroPlayed");

    if (introPlayed === "true") {

        intro.style.display = "none";

        document.body.classList.remove("intro-active");

        return;
    }

    document.body.classList.add("intro-active");

    setTimeout(function () {

        intro.classList.add("hide");

        document.body.classList.remove("intro-active");

        sessionStorage.setItem(
            "pestIntroPlayed",
            "true"
        );

    }, 3400);

});


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

const currentPage =
    window.location.pathname
        .split("/")
        .pop();


const allNavLinks =
    document.querySelectorAll(
        ".nav-links a"
    );


allNavLinks.forEach(function (link) {

    const linkPage =
        link.getAttribute("href");


    if (
        linkPage === currentPage ||
        (
            currentPage === "" &&
            linkPage === "index.html"
        )
    ) {

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