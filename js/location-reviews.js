(function () {
    const districtMain = document.querySelector("main.location-page");
    const areaMain = document.querySelector("main.area-main");
    const reviewSection = `
        <section class="section reviews-preview location-reviews">
            <div class="section-title">
                <span class="section-label">5 STAR REVIEWS</span>
                <h2>What Customers Says<br>About us</h2>
                <p>Trusted pest control services backed by real customer experiences.</p>
            </div>
            <div class="review-carousel">
                <div class="review-grid-large">
                    <article class="review-card">
                        <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                        <p>I needed urgent cockroach control for my restaurant kitchen in Jodhpur before the busy weekend rush. The team accommodated a 7:00 AM Sunday morning slot. Because they used a highly effective, odorless gel bait, we didn't even have to remove our kitchen utensils or shut down prep areas. Quick, perfectly timed, and zero hassle. Easily the most professional general pest control service in Rajasthan.</p>
                        <strong>Raju Singh</strong>
                    </article>
                    <article class="review-card">
                        <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                        <p>We discovered a bed bug issue in our guest house in Ajmer and needed it handled discreetly before new guests checked in. The technicians arrived promptly at 6:00 PM for an evening appointment. They executed a highly detailed crack-and-crevice chemical spray on all the bed frames and baseboards within two hours. Fantastic scheduling, very professional behavior, and completely effective.</p>
                        <strong>Abhay rai singh</strong>
                    </article>
                    <article class="review-card">
                        <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                        <p>Finding a pest control company in Beawar that works around our factory timings was tough until we found Super Pest Control Services. They sent their technicians at 8:00 PM, right after our main production shift ended, to perform high-volume warehouse fogging and rodent baiting. They didn't disrupt our daytime operations at all. Punctual, flexible, and the mosquito and rat problems are entirely resolved.</p>
                        <strong>Sachin Sain</strong>
                    </article>
                    <article class="review-card">
                        <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                        <p>Our residential society was struggling with a huge mosquito problem. We called Super Pest Control Services for their outdoor thermal fogging service. The knockdown was instant, and our outdoor garden areas are finally usable again in the evenings. If you need reliable vector and mosquito control, these guys are the absolute best!</p>
                        <strong>Yogendra Yadav</strong>
                    </article>
                    <article class="review-card">
                        <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                        <p>We scheduled a post-construction termite treatment for our home in Jaipur, and the team from Super Pest Control Services arrived exactly on time at 9:00 AM. They were incredibly knowledgeable, explaining their specific chemical choices—like using Alphacypermethrin for our severe infestation to ensure long-term safety and maximum residual effect. By 1:00 PM, the deep-drill process was completely finished, and they cleaned up perfectly. Highly recommend them for fast, punctual, and expert termite control!</p>
                        <strong>Shiva Meena</strong>
                    </article>
                    <article class="review-card">
                        <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                        <p>I hired Super Pest Control Services for a severe termite problem at my home in Jaipur. The team was punctual, highly professional, and explained exactly how the deep-drill termite treatment would work. They used safe chemicals, sealed everything perfectly, and left no mess behind. It’s been months, and the termites are completely gone. If you need the best residential pest control in Jaipur, this is the company to call! Highly recommended.</p>
                        <strong>Shivangi Katheriya</strong>
                    </article>
                    <article class="review-card">
                        <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                        <p>We had a major rat problem at our logistics warehouse in Beawar, and Super Pest Control Services handled it perfectly. Their rodent control team installed secure bait stations and sealed the structural entry points. Fast, professional, and our facility is finally rodent-free. Highly recommend them for commercial pest management!</p>
                        <strong>Punit Samaria</strong>
                    </article>
                    <article class="review-card">
                        <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                        <p>We run a busy restaurant in Jaipur and struggled with roaches in our prep areas. Super Pest Control Services was incredible. They applied an odorless gel bait that didn't require us to empty cabinets or shut down the kitchen. Highly professional, and our kitchen is completely pest-free. 5 stars!</p>
                        <strong>Soniya Sharma</strong>
                    </article>
                    <article class="review-card">
                        <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                        <p>We had a terrible bed bug issue in our guest house in Jaipur, and Super Pest Control Services completely solved it. Their bed bug eradication treatment was incredibly thorough, targeting every mattress and baseboard. They broke the breeding cycle in just a few visits. Best pest control service in Jaipur for bed bugs!</p>
                        <strong>Rakesh kumar Upadhyay</strong>
                    </article>
                    <article class="review-card">
                        <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                        <p>Highly recommend Super Pest Control Services for anyone looking for residential pest control in Beawar. We hired them for a general pest treatment to deal with heavy ant and spider activity. The team was punctual, used safe indoor chemicals, and the results were immediate. Fantastic, hassle-free service!</p>
                        <strong>Krish Raj Singh Solanki</strong>
                    </article>
                    <article class="review-card">
                        <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                        <p>I had a good experience with the pest control service. The team explained the treatment process clearly and shared useful tips to prevent pests from returning. A helpful option for anyone looking for professional pest control services.</p>
                        <strong>Rahul Sharma</strong>
                    </article>
                    <article class="review-card">
                        <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                        <p>I contacted the team for cockroach control at my home. The staff explained the treatment and prevention measures professionally. The service process was organised, and my questions were answered properly.</p>
                        <strong>Priya Verma</strong>
                    </article>
                    <article class="review-card">
                        <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                        <p>I was looking for termite control services and wanted to understand the available treatment options. The team explained the process and the importance of preventive measures. Overall, the communication was professional.</p>
                        <strong>Amit Singh</strong>
                    </article>
                    <article class="review-card">
                        <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                        <p>The pest control team was courteous and explained how to maintain cleanliness and reduce pest activity. The appointment process was straightforward, and the staff answered my questions patiently.</p>
                        <strong>Neha Choudhary</strong>
                    </article>
                    <article class="review-card">
                        <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                        <p>We needed pest management for commercial premises. The team discussed inspection, monitoring, hygiene, and preventive measures. Their explanation helped us understand how a planned pest management programme works.</p>
                        <strong>Vikas Jain</strong>
                    </article>
                    <article class="review-card">
                        <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                        <p>I wanted a solution for common household pests. The team explained the treatment procedure and gave practical advice about keeping pest-prone areas clean. The overall interaction was helpful.</p>
                        <strong>Pooja Meena</strong>
                    </article>
                    <article class="review-card">
                        <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                        <p>I contacted the pest control team regarding rodent activity. They explained the importance of identifying entry points, removing attractants, and monitoring affected areas. The guidance was clear and professional.</p>
                        <strong>Sandeep Rathore</strong>
                    </article>
                    <article class="review-card">
                        <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                        <p>I enquired about mosquito control for my property. The team explained treatment options and suggested reducing standing water around the premises. The information was useful for planning mosquito prevention.</p>
                        <strong>Kavita Joshi</strong>
                    </article>
                    <article class="review-card">
                        <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                        <p>Booking the pest control service was straightforward. The team explained the areas to be checked and shared practical prevention advice. I appreciated the professional communication and clear instructions.</p>
                        <strong>Manish Agarwal</strong>
                    </article>
                    <article class="review-card">
                        <div class="review-stars" aria-label="5 out of 5 stars">★★★★★</div>
                        <p>I was comparing pest control services for a property and appreciated the clear explanation of treatment options, inspection, and preventive measures. The team helped me understand what to consider when selecting a pest management service.</p>
                        <strong>Anjali Kumawat</strong>
                    </article>
                </div>
            </div>
        </section>
    `;

    if (districtMain) {
        const container = districtMain.querySelector(".location-container");
        if (!container || container.querySelector(".reviews-preview")) return;
        container.insertAdjacentHTML("afterbegin", reviewSection);
    } else if (areaMain) {
        const content = areaMain.querySelector(".area-content");
        if (!content || content.querySelector(".reviews-preview")) return;
        const cta = content.querySelector(".area-cta");
        if (cta) {
            cta.insertAdjacentHTML("beforebegin", reviewSection);
        } else {
            content.insertAdjacentHTML("beforeend", reviewSection);
        }
    } else {
        return;
    }

    const carousel = document.querySelector(".location-reviews .review-carousel");
    const track = carousel && carousel.querySelector(".review-grid-large");
    if (!carousel || !track) return;
    track.style.cursor = "grab";

    let pointerStartX = 0;
    let pointerStartY = 0;
    let trackStartX = 0;
    let dragging = false;

    function currentOffset() {
        const transform = window.getComputedStyle(track).transform;
        return transform === "none" ? 0 : new DOMMatrixReadOnly(transform).m41;
    }

    function maximumOffset() {
        return Math.max(0, track.scrollWidth - carousel.clientWidth);
    }

    carousel.addEventListener("pointerdown", function (event) {
        if (event.pointerType !== "mouse" || event.button !== 0) return;
        pointerStartX = event.clientX;
        pointerStartY = event.clientY;
        trackStartX = currentOffset();
        dragging = false;
        carousel.setPointerCapture(event.pointerId);
    });

    carousel.addEventListener("pointermove", function (event) {
        if (event.pointerType !== "mouse" || !carousel.hasPointerCapture(event.pointerId)) return;

        const deltaX = event.clientX - pointerStartX;
        const deltaY = event.clientY - pointerStartY;
        if (!dragging && Math.abs(deltaX) < 4 && Math.abs(deltaY) < 4) return;
        if (!dragging && Math.abs(deltaY) > Math.abs(deltaX)) {
            carousel.releasePointerCapture(event.pointerId);
            return;
        }

        dragging = true;
        track.classList.add("review-track-dragging");
        track.style.cursor = "grabbing";
        track.style.transition = "none";
        track.style.transform = "translateX(" + Math.max(-maximumOffset(), Math.min(0, trackStartX + deltaX)) + "px)";
        event.preventDefault();
    });

    function finishDrag(event) {
        if (event.pointerType !== "mouse" || !carousel.hasPointerCapture(event.pointerId)) return;
        carousel.releasePointerCapture(event.pointerId);
        if (!dragging) return;

        const firstCard = track.querySelector(".review-card");
        const gap = parseFloat(window.getComputedStyle(track).gap) || 0;
        const cardStep = firstCard ? firstCard.getBoundingClientRect().width + gap : 0;
        if (cardStep) {
            const nearestOffset = Math.round(Math.abs(currentOffset()) / cardStep) * cardStep;
            track.style.removeProperty("transition");
            track.style.transform = "translateX(-" + Math.min(maximumOffset(), nearestOffset) + "px)";
        }

        track.classList.remove("review-track-dragging");
        track.style.cursor = "grab";
        track.style.removeProperty("transition");
        dragging = false;
    }

    carousel.addEventListener("pointerup", finishDrag);
    carousel.addEventListener("pointercancel", finishDrag);
}());
