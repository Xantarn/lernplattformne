(function () {
  function getRow(fieldName) {
    return document.querySelector('.form-row.field-' + fieldName) || document.getElementById('row_' + fieldName);
  }

  function setVisible(fieldName, isVisible) {
    var row = getRow(fieldName);
    if (!row) {
      return;
    }
    row.style.display = isVisible ? '' : 'none';
  }

  function updateVisibility() {
    var typeField = document.getElementById('id_question_type');
    if (!typeField) {
      return;
    }

    var type = typeField.value;

    var allDynamicFields = [
      'answer_a',
      'answer_b',
      'answer_c',
      'answer_d',
      'correct_answer',
      'options_json',
      'correct_answers_json',
      'matching_pairs_json',
      'order_items_json',
      'blanks_json',
      'prompt_image',
      'code_snippet',
      'code_language',
      'code_validation_mode',
      'code_starter',
      'code_test_input',
      'code_expected_output',
      'scenario_text'
    ];

    allDynamicFields.forEach(function (field) {
      setVisible(field, false);
    });

    if (type === 'mc_single') {
      ['answer_a', 'answer_b', 'answer_c', 'answer_d', 'correct_answer'].forEach(function (f) {
        setVisible(f, true);
      });
      return;
    }

    if (type === 'true_false') {
      setVisible('correct_answers_json', true);
      return;
    }

    if (type === 'multi_select') {
      setVisible('options_json', true);
      setVisible('correct_answers_json', true);
      return;
    }

    if (type === 'short_text') {
      setVisible('correct_answers_json', true);
      setVisible('correct_answer', true);
      return;
    }

    if (type === 'matching') {
      setVisible('matching_pairs_json', true);
      return;
    }

    if (type === 'ordering') {
      setVisible('order_items_json', true);
      setVisible('options_json', true);
      return;
    }

    if (type === 'cloze') {
      setVisible('blanks_json', true);
      return;
    }

    if (type === 'image_single') {
      setVisible('prompt_image', true);
      setVisible('options_json', true);
      setVisible('correct_answers_json', true);
      return;
    }

    if (type === 'code_single') {
      setVisible('code_snippet', true);
      setVisible('code_language', true);
      setVisible('code_validation_mode', true);
      setVisible('code_starter', true);
      setVisible('code_test_input', true);
      setVisible('code_expected_output', true);
      return;
    }

    if (type === 'scenario_single') {
      setVisible('scenario_text', true);
      setVisible('options_json', true);
      setVisible('correct_answers_json', true);
      return;
    }

    if (type === 'self_assessment') {
      setVisible('correct_answers_json', true);
      return;
    }

    // Fallback: show everything if unknown type.
    allDynamicFields.forEach(function (field) {
      setVisible(field, true);
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var typeField = document.getElementById('id_question_type');
    if (!typeField) {
      return;
    }

    updateVisibility();
    typeField.addEventListener('change', updateVisibility);
  });
})();
