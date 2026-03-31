(function () {
  function findBlockElement(node, doc) {
    var current = node;
    while (current && current !== doc.body) {
      if (
        current.nodeType === 1 &&
        /^(P|DIV|LI|BLOCKQUOTE|H1|H2|H3|H4|H5|H6|PRE)$/.test(current.tagName)
      ) {
        return current;
      }
      current = current.parentNode;
    }
    return doc.body;
  }

  function applyLineHeight(container, lineHeight) {
    var iframe = container.querySelector('iframe');
    var doc = iframe && iframe.contentDocument ? iframe.contentDocument : document;
    var selection = doc.getSelection ? doc.getSelection() : window.getSelection();

    if (!selection || !selection.rangeCount) {
      return;
    }

    var range = selection.getRangeAt(0);
    var startNode = range.startContainer;
    if (startNode.nodeType === 3) {
      startNode = startNode.parentNode;
    }

    var block = findBlockElement(startNode, doc);
    if (block) {
      block.style.lineHeight = lineHeight;
    }
  }

  function buildControls(container) {
    if (!container || container.__lineHeightControlsBound) {
      return;
    }

    var editor = container.querySelector('.note-editor') || container;
    if (!editor || !editor.classList || !editor.classList.contains('note-editor')) {
      return;
    }

    var controls = document.createElement('div');
    controls.className = 'summernote-lineheight-controls';

    var label = document.createElement('span');
    label.className = 'summernote-lineheight-label';
    label.textContent = 'Zeilenabstand:';
    controls.appendChild(label);

    [
      { text: 'eng', value: '1.0' },
      { text: 'normal', value: '1.4' },
      { text: 'weit', value: '1.8' },
    ].forEach(function (option) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'button summernote-lineheight-btn';
      button.textContent = option.text;
      button.addEventListener('click', function (event) {
        event.preventDefault();
        applyLineHeight(container, option.value);
      });
      controls.appendChild(button);
    });

    editor.parentNode.insertBefore(controls, editor);
    container.__lineHeightControlsBound = true;
  }

  function initLineHeightControls() {
    // Preferred container from django-summernote.
    document.querySelectorAll('.django-summernote-widget').forEach(function (widget) {
      buildControls(widget);
    });

    // Fallback for pages where only the rendered Summernote editor is present.
    document.querySelectorAll('.note-editor').forEach(function (editor) {
      buildControls(editor.parentElement || editor);
    });
  }

  function watchEditors() {
    if (!window.MutationObserver || !document.body) {
      return;
    }

    var observer = new MutationObserver(function () {
      initLineHeightControls();
    });

    observer.observe(document.body, { childList: true, subtree: true });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initLineHeightControls();
    watchEditors();
    window.setTimeout(initLineHeightControls, 300);
    window.setTimeout(initLineHeightControls, 900);
  });
})();
