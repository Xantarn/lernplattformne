(function () {
  var blockTemplates = [
    {
      label: 'Info',
      html: '<div class="topic-panel topic-panel--info"><div class="topic-panel__title">Definition</div><p>Wichtige Erklaerung oder Zusammenfassung.</p></div><p><br></p>'
    },
    {
      label: 'Beispiel',
      html: '<div class="topic-panel topic-panel--example"><div class="topic-panel__title">Beispiel</div><p>Zum Beispiel ...</p></div><p><br></p>'
    },
    {
      label: 'Merke',
      html: '<div class="topic-panel topic-panel--accent"><div class="topic-panel__title">Merke</div><p>Zentrale Aussage, die im Kopf bleiben soll.</p></div><p><br></p>'
    },
    {
      label: 'Achtung',
      html: '<div class="topic-panel topic-panel--warning"><div class="topic-panel__title">Achtung</div><p>Typischer Fehler oder wichtige Einschraenkung.</p></div><p><br></p>'
    },
    {
      label: 'Abschnitt',
      html: '<div class="topic-divider"><span>Abschnittstitel</span></div><p><br></p>'
    },
    {
      label: 'Linie',
      html: '<hr class="topic-rule"><p><br></p>'
    }
  ];

  function getAdminJQuery() {
    if (window.django && window.django.jQuery) {
      return window.django.jQuery;
    }

    if (window.jQuery) {
      return window.jQuery;
    }

    return null;
  }

  function insertTemplate(editor, html) {
    var adminJQuery = getAdminJQuery();
    if (!editor || !adminJQuery) {
      return false;
    }

    var $editor = adminJQuery(editor);

    try {
      $editor.summernote('focus');
      $editor.summernote('pasteHTML', html);
      return true;
    } catch (err) {
      try {
        editor.value = (editor.value || '') + html;
        return true;
      } catch (fallbackErr) {
        return false;
      }
    }
  }

  function buildPalette(editor) {
    var row = editor.closest('.form-row.field-learning_material') || editor.closest('.form-row') || editor.parentElement;
    if (!row || row.querySelector('.topic-layout-palette')) {
      return false;
    }

    var flexContainer = row.querySelector('.flex-container');
    var target = flexContainer || row;

    var palette = document.createElement('div');
    palette.className = 'topic-layout-palette';

    var title = document.createElement('span');
    title.className = 'topic-layout-palette__label';
    title.textContent = 'Layout-Bausteine:';
    palette.appendChild(title);

    blockTemplates.forEach(function (template) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'button topic-layout-palette__btn';
      button.title = template.label + ' einfuegen';
      button.textContent = template.label;
      button.addEventListener('mousedown', function (event) {
        event.preventDefault();
      });
      button.addEventListener('click', function (event) {
        event.preventDefault();
        insertTemplate(editor, template.html);
      });
      palette.appendChild(button);
    });

    if (flexContainer) {
      flexContainer.insertAdjacentElement('beforebegin', palette);
    } else {
      target.insertAdjacentElement('afterbegin', palette);
    }

    return true;
  }

  function initEditors() {
    var found = false;
    document.querySelectorAll('textarea[id="id_learning_material"]').forEach(function (editor) {
      if (editor.classList.contains('topic-layout-palette-bound')) {
        return;
      }

      if (buildPalette(editor)) {
        editor.classList.add('topic-layout-palette-bound');
        found = true;
      }
    });

    return found;
  }

  function pollForEditors(attempt) {
    initEditors();

    if (attempt >= 40) {
      return;
    }

    window.setTimeout(function () {
      pollForEditors(attempt + 1);
    }, 150);
  }

  document.addEventListener('DOMContentLoaded', function () {
    pollForEditors(0);

    if (window.MutationObserver && document.body) {
      var observer = new MutationObserver(function () {
        initEditors();
      });
      observer.observe(document.body, { childList: true, subtree: true });
    }
  });
})();