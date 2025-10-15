document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.star-rating-input').forEach(setupRating);

  function highlight(stars, count) {
    stars.forEach((btn, i) => {
      const icon = btn.querySelector('i');
      icon.classList.toggle('fas', i < count);
      icon.classList.toggle('far', i >= count);
    });
  }

  function setupRating(container) {
    const movieId = container.dataset.movieId;
    const form = container.querySelector('.rating-form');
    const hidden = container.querySelector('#rating-value-' + movieId);
    const stars = Array.from(container.querySelectorAll('.star-btn'));
    const submitBtn = container.querySelector('.submit-rating');
    const feedback = container.querySelector('#rating-feedback-' + movieId);

    stars.forEach((btn, idx) => {
      btn.addEventListener('mouseenter', () => highlight(stars, idx + 1));
      btn.addEventListener('mouseleave', () => highlight(stars, parseInt(hidden.value || '0', 10)));
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const rating = parseInt(btn.dataset.rating, 10);
        hidden.value = rating;
        highlight(stars, rating);
        if (submitBtn) submitBtn.classList.remove('d-none');
        btn.classList.add('star-selected');
        setTimeout(() => btn.classList.remove('star-selected'), 280);
      });
    });

    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fd = new FormData(form);
        if (!fd.get('rating')) return;
        const orig = submitBtn ? submitBtn.textContent : '';
        if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Submitting...'; }
        try {
          const res = await fetch(form.action, { method: 'POST', headers: { 'X-Requested-With': 'XMLHttpRequest' }, body: fd });
          const data = await res.json();
          if (res.ok) {
            // update matching displays
            document.querySelectorAll('.star-rating-display[data-movie-id="' + data.movie_id + '"] .stars-container i')
              .forEach((el, i) => {
                const avg = parseFloat(data.average_rating);
                el.className = '';
                if (i + 1 <= Math.floor(avg)) el.className = 'fas fa-star star-filled';
                else if (i < avg) el.className = 'fas fa-star-half-alt star-half';
                else el.className = 'far fa-star star-empty';
              });
            const val = document.querySelector('.star-rating-display[data-movie-id="' + data.movie_id + '"] .rating-value');
            if (val) val.textContent = data.average_rating;
            const cnt = document.querySelector('.star-rating-display[data-movie-id="' + data.movie_id + '"] .rating-count');
            if (cnt) cnt.textContent = `(${data.rating_count} rating${data.rating_count === 1 ? '' : 's'})`;
            if (feedback) { feedback.className = 'rating-feedback alert alert-success'; feedback.textContent = 'Saved'; feedback.style.display = 'block'; setTimeout(()=> feedback.style.display = 'none', 1500); }
          } else {
            if (feedback) { feedback.className = 'rating-feedback alert alert-danger'; feedback.textContent = 'Error'; feedback.style.display = 'block'; }
          }
        } catch (_) {
          if (feedback) { feedback.className = 'rating-feedback alert alert-danger'; feedback.textContent = 'Network error'; feedback.style.display = 'block'; }
        } finally {
          if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = orig; }
        }
      });
    }

    highlight(stars, parseInt(hidden.value || '0', 10));
  }
});
