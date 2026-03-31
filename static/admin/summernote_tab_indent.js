(function () {
  function insertTextAtCursor(doc, text) {
    if (doc.execCommand) {
      try {
        doc.execCommand('insertText', false, text);
        return;
      } catch (err) {
        // Fallback below.
      }
    }

    var selection = doc.getSelection && doc.getSelection();
    if (!selection || !selection.rangeCount) {
      return;
    }

    var range = selection.getRangeAt(0);
    range.deleteContents();
    var node = doc.createTextNode(text);
    range.insertNode(node);
    range.setStartAfter(node);
    range.setEndAfter(node);
    selection.removeAllRanges();
    selection.addRange(range);
  }

  function bindEditableHandler(editable) {
    if (!editable || editable.__tabIndentBound) {
      return;
    }

    editable.addEventListener('keydown', function (event) {
      if (event.key !== 'Tab') {
        return;
      }

      event.preventDefault();
      event.stopPropagation();
      var doc = editable.ownerDocument;
      insertTextAtCursor(doc, '    ');
    }, true);

    editable.__tabIndentBound = true;
  }

  function bindTabHandler(doc) {
    if (!doc || doc.__tabIndentBound) {
      return;
    }

    function onKeyDown(event) {
      if (event.key !== 'Tab') {
        return;
      }

      event.preventDefault();
      // Use non-breaking spaces so indentation stays visible in HTML paragraphs.
      insertTextAtCursor(doc, '\u00A0\u00A0\u00A0\u00A0');
    }

    doc.addEventListener('keydown', onKeyDown, true);
    if (doc.body) {
      doc.body.addEventListener('keydown', onKeyDown, true);
    }

    doc.__tabIndentBound = true;
  }

  function bindIframe(iframe) {
    if (!iframe || iframe.__tabIndentIframeBound) {
      return;
    }

    function tryBind() {
      try {
        bindTabHandler(iframe.contentDocument);
      } catch (err) {
        // Ignore transient timing issues.
      }
    }

    iframe.addEventListener('load', tryBind);
    iframe.__tabIndentIframeBound = true;
    tryBind();
  }

  function initTabIndent() {
    // Iframe mode (default for django-summernote)
    document.querySelectorAll('.django-summernote-widget iframe').forEach(function (iframe) {
      bindIframe(iframe);
    });

    // Air mode / editable div fallback.
    document.querySelectorAll('.note-editable').forEach(function (editable) {
      bindEditableHandler(editable);
      bindTabHandler(editable.ownerDocument);
    });
  }

  function watchForEditors() {
    if (!window.MutationObserver) {
      return;
    }

    var observer = new MutationObserver(function () {
      initTabIndent();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initTabIndent();
    watchForEditors();
    window.setTimeout(initTabIndent, 250);
    window.setTimeout(initTabIndent, 800);
    window.setTimeout(initTabIndent, 1500);
  });
})();
