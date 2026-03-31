(function () {
  function stretchSummernote() {
    var wrappers = document.querySelectorAll('.form-row.field-learning_material .django-summernote-widget');
    wrappers.forEach(function (wrapper) {
      var row = wrapper.closest('.form-row.field-learning_material');
      if (!row) {
        return;
      }

      var target = Math.max(1250, (window.innerWidth || 1400) - 380);

      row.style.width = target + 'px';
      row.style.maxWidth = 'none';

      wrapper.style.width = target + 'px';
      wrapper.style.maxWidth = 'none';

      var editor = wrapper.querySelector('.note-editor');
      if (editor) {
        editor.style.width = target + 'px';
        editor.style.maxWidth = 'none';
      }

      var iframe = wrapper.querySelector('iframe');
      if (iframe) {
        iframe.style.width = target + 'px';
        iframe.style.maxWidth = 'none';
      }
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    stretchSummernote();
    window.setTimeout(stretchSummernote, 200);
    window.setTimeout(stretchSummernote, 700);
  });

  window.addEventListener('resize', stretchSummernote);
})();
