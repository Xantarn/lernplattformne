(function () {
  var templateCounter = 0;

  function nextTemplateId(prefix) {
    templateCounter += 1;
    return prefix + '-' + Date.now() + '-' + templateCounter;
  }

  function buildBoxTemplate(variantClass, text) {
    var className = 'topic-box';
    if (variantClass) {
      className += ' ' + variantClass;
    }

    return '<div class="' + className + '" data-topic-box-id="' + nextTemplateId('topic-box') + '"><p>' + text + '</p></div><p><br></p>';
  }

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
    },
    {
      label: 'Verbinder',
      html: '<div class="topic-connector"><span class="topic-connector__line">&nbsp;</span><span class="topic-connector__label">Verbindungstext</span><span class="topic-connector__line">&nbsp;</span></div><p><br></p>'
    },
    {
      label: 'Pfeil Rechts',
      html: '<div class="topic-arrow-row"><span class="topic-arrow-row__label">Weiter zu diesem Block</span><span class="topic-arrow-row__shaft">&nbsp;</span><span class="topic-arrow-row__head">&#8594;</span></div><p><br></p>'
    },
    {
      label: 'Pfeil Unten',
      html: '<div class="topic-arrow-stack"><span class="topic-arrow-stack__label">Naechster Schritt</span><span class="topic-arrow-stack__shaft">&nbsp;</span><span class="topic-arrow-stack__head">&#8595;</span></div><p><br></p>'
    },
    {
      label: 'Hinweis-Pin',
      html: '<div class="topic-callout"><div class="topic-callout__rail"><div class="topic-callout__pin"></div><div class="topic-callout__stem"></div></div><div class="topic-callout__body">Kurzer Hinweistext, der optisch an ein Bild oder einen Block angedockt wirkt.</div></div><p><br></p>'
    },
    {
      label: 'Box Frei',
      html: function () {
        return buildBoxTemplate('', 'Textblock in einer abgerundeten Box.');
      }
    },
    {
      label: 'Box Blau',
      html: function () {
        return buildBoxTemplate('topic-box--blue', 'Textblock in einer blauen Box.');
      }
    },
    {
      label: 'Box Gruen',
      html: function () {
        return buildBoxTemplate('topic-box--green', 'Textblock in einer gruenen Box.');
      }
    },
    {
      label: 'Box Gelb',
      html: function () {
        return buildBoxTemplate('topic-box--yellow', 'Textblock in einer gelben Box.');
      }
    },
    {
      label: 'Box Rot',
      html: function () {
        return buildBoxTemplate('topic-box--red', 'Textblock in einer roten Box.');
      }
    },
    {
      label: 'Vergleich',
      html: '<div class="topic-compare"><div class="topic-compare__column"><div class="topic-compare__title">Option A</div><p>Erster Aspekt oder Eigenschaft.</p></div><div class="topic-compare__column"><div class="topic-compare__title">Option B</div><p>Zweiter Aspekt oder Gegenueberstellung.</p></div></div><p><br></p>'
    },
    {
      label: 'Schritte',
      html: '<div class="topic-steps"><div class="topic-step"><div class="topic-step__number">1</div><div class="topic-step__body"><div class="topic-step__title">Erster Schritt</div><p>Kurze Erklaerung zum ersten Schritt.</p></div></div><div class="topic-step"><div class="topic-step__number">2</div><div class="topic-step__body"><div class="topic-step__title">Zweiter Schritt</div><p>Kurze Erklaerung zum zweiten Schritt.</p></div></div><div class="topic-step"><div class="topic-step__number">3</div><div class="topic-step__body"><div class="topic-step__title">Dritter Schritt</div><p>Kurze Erklaerung zum dritten Schritt.</p></div></div></div><p><br></p>'
    },
    {
      label: 'Bild mit Caption',
      html: '<figure class="topic-figure"><img src="" alt="Bildbeschreibung" /><figcaption><strong>Bildunterschrift:</strong> Kurze Beschreibung oder Quelle.</figcaption></figure><p><br></p>'
    },
    {
      label: '2 Spalten',
      html: '<div class="topic-columns"><div class="topic-column topic-column--image"><p><img src="" alt="Bildbeschreibung" /></p></div><div class="topic-column"><h4>Ueberschrift</h4><p>Textinhalt in der zweiten Spalte.</p></div></div><p><br></p>'
    }
  ];

  var boxColorOptions = [
    { label: 'Neutral', className: '' },
    { label: 'Blau', className: 'topic-box--blue' },
    { label: 'Gruen', className: 'topic-box--green' },
    { label: 'Gelb', className: 'topic-box--yellow' },
    { label: 'Rot', className: 'topic-box--red' }
  ];

  var spacingOptions = [
    { label: 'Tab', mode: 'tab', count: 1 },
    { label: 'Tab x2', mode: 'tab', count: 2 }
  ];

  function getTopicTextarea() {
    return document.querySelector('textarea#id_learning_material.django_ckeditor_5') || document.querySelector('textarea#id_learning_material');
  }

  function getEditor(textarea) {
    if (!textarea || !window.editors) {
      return null;
    }

    return window.editors[textarea.id] || null;
  }

  function insertHtmlWithEditor(editor, html) {
    if (!editor || !editor.model || !editor.data || !editor.data.processor) {
      return false;
    }

    try {
      editor.model.change(function () {
        var viewFragment = editor.data.processor.toView(html);
        var modelFragment = editor.data.toModel(viewFragment);
        editor.model.insertContent(modelFragment, editor.model.document.selection);
      });
      editor.editing.view.focus();
      return true;
    } catch (err) {
      return false;
    }
  }

  function insertTemplate(textarea, html) {
    var editor = getEditor(textarea);
    if (insertHtmlWithEditor(editor, html)) {
      return;
    }

    if (!textarea) {
      return;
    }

    textarea.value = (textarea.value || '') + html;
    textarea.dispatchEvent(new Event('input', { bubbles: true }));
    textarea.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function escapeHtml(value) {
    return (value || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function plainTextToHtml(text) {
    var lines = (text || '').replace(/\r\n/g, '\n').split('\n');
    var blocks = [];
    var paragraph = [];

    lines.forEach(function (line) {
      if (!line.trim()) {
        if (paragraph.length) {
          blocks.push('<p>' + paragraph.join('<br>') + '</p>');
          paragraph = [];
        }
        return;
      }
      paragraph.push(escapeHtml(line));
    });

    if (paragraph.length) {
      blocks.push('<p>' + paragraph.join('<br>') + '</p>');
    }

    return blocks.join('');
  }

  function getCsrfToken() {
    var hiddenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (hiddenInput && hiddenInput.value) {
      return hiddenInput.value;
    }

    var cookieName = 'csrftoken=';
    var cookies = document.cookie ? document.cookie.split(';') : [];
    for (var i = 0; i < cookies.length; i += 1) {
      var cookie = cookies[i].trim();
      if (cookie.indexOf(cookieName) === 0) {
        return decodeURIComponent(cookie.substring(cookieName.length));
      }
    }
    return '';
  }

  function setStatus(element, message, kind) {
    if (!element) {
      return;
    }
    element.textContent = message || '';
    element.classList.remove('topic-layout-palette__ocr-status--ok', 'topic-layout-palette__ocr-status--error');
    if (kind === 'ok') {
      element.classList.add('topic-layout-palette__ocr-status--ok');
    }
    if (kind === 'error') {
      element.classList.add('topic-layout-palette__ocr-status--error');
    }
  }

  function buildOcrControls(textarea, palette) {
    var ocrUrl = textarea.getAttribute('data-ocr-url');
    if (!ocrUrl) {
      return;
    }

    var wrap = document.createElement('span');
    wrap.className = 'topic-layout-palette__ocr-wrap';

    var button = document.createElement('button');
    button.type = 'button';
    button.className = 'button topic-layout-palette__ocr-btn';
    button.textContent = 'PDF scannen';
    button.title = 'Gescannte PDF per OCR in Lernmaterial einfuegen';

    var input = document.createElement('input');
    input.type = 'file';
    input.accept = 'application/pdf';
    input.className = 'topic-layout-palette__ocr-input';

    var status = document.createElement('span');
    status.className = 'topic-layout-palette__ocr-status';

    button.addEventListener('mousedown', function (event) {
      event.preventDefault();
    });

    button.addEventListener('click', function (event) {
      event.preventDefault();
      input.click();
    });

    input.addEventListener('change', function () {
      var file = input.files && input.files[0];
      if (!file) {
        return;
      }

      setStatus(status, 'PDF wird verarbeitet...', '');
      button.disabled = true;

      var payload = new FormData();
      payload.append('pdf_file', file);

      fetch(ocrUrl, {
        method: 'POST',
        body: payload,
        credentials: 'same-origin',
        headers: {
          'X-CSRFToken': getCsrfToken(),
          'Accept': 'application/json'
        }
      })
        .then(function (response) {
          var contentType = (response.headers.get('content-type') || '').toLowerCase();
          if (contentType.indexOf('application/json') >= 0) {
            return response.json().then(function (data) {
              return { ok: response.ok, status: response.status, data: data };
            });
          }

          return response.text().then(function (htmlText) {
            var shortText = (htmlText || '').replace(/\s+/g, ' ').trim().slice(0, 180);
            return {
              ok: false,
              status: response.status,
              data: {
                error: 'Server lieferte kein JSON (Status ' + response.status + '). ' + shortText
              }
            };
          });
        })
        .then(function (result) {
          if (!result.ok) {
            throw new Error(result.data && result.data.error ? result.data.error : 'OCR fehlgeschlagen.');
          }

          var extractedText = (result.data && result.data.text) || '';
          if (!extractedText.trim()) {
            throw new Error('Kein Text erkannt.');
          }

          insertTemplate(textarea, plainTextToHtml(extractedText));

          if (result.data.truncated) {
            setStatus(status, 'Text eingefuegt (gekuerzt).', 'ok');
          } else {
            setStatus(status, 'Text erfolgreich eingefuegt.', 'ok');
          }
        })
        .catch(function (error) {
          setStatus(status, error.message || 'OCR fehlgeschlagen.', 'error');
        })
        .finally(function () {
          button.disabled = false;
          input.value = '';
        });
    });

    wrap.appendChild(button);
    wrap.appendChild(input);
    wrap.appendChild(status);
    palette.appendChild(wrap);
  }

  function insertSpacing(textarea, count, mode) {
    var editor = getEditor(textarea);
    var safeCount = Math.max(1, Number(count || 1));
    var spacingText = mode === 'tab' ? '\t'.repeat(safeCount) : '\u00A0'.repeat(safeCount);

    if (editor && editor.model && editor.model.change) {
      try {
        editor.model.change(function (writer) {
          editor.editing.view.focus();
          var selection = editor.model.document.selection;
          var firstPosition = selection.getFirstPosition();

          if (!firstPosition) {
            return;
          }

          // Table selections can be non-collapsed; collapse before inserting spacing.
          if (!selection.isCollapsed) {
            writer.setSelection(firstPosition);
          }

          editor.model.insertContent(writer.createText(spacingText), editor.model.document.selection);
        });
        return;
      } catch (err) {
        // Fallback below.
      }
    }

    if (!textarea) {
      return;
    }

    textarea.value = (textarea.value || '') + spacingText;
    textarea.dispatchEvent(new Event('input', { bubbles: true }));
    textarea.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function getSelectedTopicBox() {
    var selection = window.getSelection && window.getSelection();
    if (!selection || !selection.anchorNode) {
      return null;
    }

    var node = selection.anchorNode.nodeType === 1 ? selection.anchorNode : selection.anchorNode.parentElement;
    if (!node || !node.closest) {
      return null;
    }

    var box = node.closest('.topic-box');
    if (!box) {
      return null;
    }

    var editable = box.closest('.ck-editor__editable');
    return editable ? box : null;
  }

  function updateSelectedBoxVariant(textarea, variantClass) {
    var editor = getEditor(textarea);
    var selectedBox = getSelectedTopicBox();
    if (!editor || !selectedBox) {
      return false;
    }

    var boxId = selectedBox.getAttribute('data-topic-box-id');
    if (!boxId) {
      return false;
    }

    var parser = new DOMParser();
    var doc = parser.parseFromString(editor.getData(), 'text/html');
    var box = doc.querySelector('[data-topic-box-id="' + boxId + '"]');
    if (!box) {
      return false;
    }

    box.classList.remove('topic-box--blue', 'topic-box--green', 'topic-box--yellow', 'topic-box--red');
    box.classList.add('topic-box');
    if (variantClass) {
      box.classList.add(variantClass);
    }

    editor.setData(doc.body.innerHTML);
    return true;
  }

  function resolveTemplateHtml(template) {
    if (typeof template.html === 'function') {
      return template.html();
    }

    return template.html;
  }

  function buildPalette(textarea) {
    var row = textarea.closest('.form-row.field-learning_material') || textarea.closest('.form-row') || textarea.parentElement;
    if (!row || row.querySelector('.topic-layout-palette')) {
      return false;
    }

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
        insertTemplate(textarea, resolveTemplateHtml(template));
      });
      palette.appendChild(button);
    });

    var separator = document.createElement('span');
    separator.className = 'topic-layout-palette__separator';
    separator.textContent = 'Box-Farbe:';
    palette.appendChild(separator);

    boxColorOptions.forEach(function (option) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'button topic-layout-palette__swatch';
      button.textContent = option.label;
      if (option.className) {
        button.classList.add('topic-layout-palette__swatch--' + option.className.replace('topic-box--', ''));
      }
      button.addEventListener('mousedown', function (event) {
        event.preventDefault();
      });
      button.addEventListener('click', function (event) {
        event.preventDefault();
        if (!updateSelectedBoxVariant(textarea, option.className)) {
          insertTemplate(textarea, buildBoxTemplate(option.className, 'Textblock in einer abgerundeten Box.'));
        }
      });
      palette.appendChild(button);
    });

    var spacingSeparator = document.createElement('span');
    spacingSeparator.className = 'topic-layout-palette__separator';
    spacingSeparator.textContent = 'Abstand:';
    palette.appendChild(spacingSeparator);

    spacingOptions.forEach(function (option) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'button topic-layout-palette__space-btn';
      button.textContent = option.label;
      button.title = 'Abstand einfuegen ' + option.label;
      button.addEventListener('mousedown', function (event) {
        event.preventDefault();
      });
      button.addEventListener('click', function (event) {
        event.preventDefault();
        insertSpacing(textarea, option.count, option.mode);
      });
      palette.appendChild(button);
    });

    var ocrSeparator = document.createElement('span');
    ocrSeparator.className = 'topic-layout-palette__separator';
    ocrSeparator.textContent = 'OCR:';
    palette.appendChild(ocrSeparator);
    buildOcrControls(textarea, palette);

    var editorContainer = row.querySelector('.ck-editor-container');
    if (editorContainer) {
      editorContainer.insertAdjacentElement('beforebegin', palette);
    } else {
      row.insertAdjacentElement('beforeend', palette);
    }

    return true;
  }

  function initPalette() {
    var textarea = getTopicTextarea();
    if (!textarea) {
      return false;
    }

    if (textarea.classList.contains('topic-layout-palette-bound')) {
      return true;
    }

    if (buildPalette(textarea)) {
      textarea.classList.add('topic-layout-palette-bound');
      return true;
    }

    return false;
  }

  function pollForEditor(attempt) {
    initPalette();
    if (attempt >= 40) {
      return;
    }

    window.setTimeout(function () {
      pollForEditor(attempt + 1);
    }, 150);
  }

  document.addEventListener('DOMContentLoaded', function () {
    pollForEditor(0);

    if (window.MutationObserver && document.body) {
      var observer = new MutationObserver(function () {
        initPalette();
      });
      observer.observe(document.body, { childList: true, subtree: true });
    }
  });
})();
