/*
requires HTML elements with the following IDs:
  verif-parameters
    variable-name
    sample-start
    sample-end
    num-samples
    sample-spacing
  min-difference-detect-error
  expressions-container
  verif-parameters-json
  run-verif-button
  verif-output
*/

const NUM_EXPRESSIONS = 10

require("../src/jquery1.7.2.min.js")
require("../node_modules/mathquill/build/mathquill.js")

var MQ = MathQuill.getInterface(2);
var expressionFields = [];
var verifParameters = {
    unknown_variables: [{
        name: '',
        sample_start: 0,
        sample_end: 0,
        num_samples: 0,
        sample_spacing: ''
    }],
    min_difference_detect_error: null,
    expressions: []
};

function updateJSONOutput() {
    document.getElementById('verif-parameters-json').textContent = JSON.stringify(verifParameters, null, 2);
}

function addExpressionField() {
    var container = document.createElement('div');
    var expressionSpan = document.createElement('span');

    container.appendChild(expressionSpan);
    document.getElementById('expressions-container').appendChild(container);

    var mathField = MQ.MathField(expressionSpan, {
        spaceBehavesLikeTab: true,
        handlers: {
            edit: function () {
                var latex = mathField.latex();
                var index = expressionFields.indexOf(mathField);
                verifParameters.expressions[index] = latex;
                updateJSONOutput();            }
        }
    });

    expressionFields.push(mathField);
    verifParameters.expressions.push(''); // Initialize with empty string
    updateJSONOutput();
}

function updateOptions() {
    verifParameters.unknown_variables[0] = {
        name: document.getElementById('variable-name').value,
        sample_start: parseFloat(document.getElementById('sample-start').value),
        sample_end: parseFloat(document.getElementById('sample-end').value),
        num_samples: parseInt(document.getElementById('num-samples').value, 10),
        sample_spacing: document.getElementById('sample-spacing').value
    };
    verifParameters.min_difference_detect_error = parseFloat(document.getElementById('min-difference-detect-error').value);
    updateJSONOutput();
}

document.querySelectorAll('#options input, #options select').forEach(input => {
    input.addEventListener('change', updateOptions);
});

function initializeTestExpressions() {
    const test_exprs = [
        "x^2",
        "x^2",
        "x^2",
        "x^2",
        "x^2",
        "x^2",
        "x^2",
        "x^2",
        "x^2",
        "x^2",
    ]
    for (var i = 0; i < NUM_EXPRESSIONS; i++) {
        expressionFields[i].latex(test_exprs[i])
    }
}

var ws = new WebSocket('ws://localhost:8080');
var verifOutputElement = document.getElementById('verif-output');

ws.onmessage = function(event) {
    var message = JSON.parse(event.data);
    console.log(message)
    if (message.type === 'verif-output') {
        verifOutputElement.textContent = message.data + '\n';
    } else {
        verifOutputElement.textContent = "ERROR"
        console.log(`ERROR: unrecognized message of type \"${message.type}\"\n${message.data}`)
    }
};

document.getElementById('run-verif-button').addEventListener('click', function() {
    ws.send(JSON.stringify({ type: 'run-verif', data: verifParameters }));
});

function init() {
    for (var i = 0; i < NUM_EXPRESSIONS; i++) {
        addExpressionField()
    }
    initializeTestExpressions()
    updateOptions()
}
window.onload = init;
