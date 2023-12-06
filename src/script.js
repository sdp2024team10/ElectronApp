/*
requires HTML elements with the following IDs:
  verif-parameters
    variable-name
    sample-start
    sample-end
    num-samples
    sample-spacing
  min-difference-detect-error
  expressions-table (table)
  verif-parameters-json
  run-verif-button (button)
  verif-output
  chart (canvas)
*/

const NUM_EXPRESSIONS = 10

require("../src/jquery1.7.2.min.js")
require("../node_modules/mathquill/build/mathquill.js")
const Chart = require('chart.js/auto');

var MQ = MathQuill.getInterface(2)
var expressionMathFields = []
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
}
var chart = null
var chartData = {
    labels: [],
    datasets: [{
        label: '',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        borderColor: 'rgba(255, 99, 132, 1)',
        borderWidth: 1,
        data: [],
    }, {
        label: '',
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1,
        data: [],
    }]
};
var chartOptions = {
    scales: {
        y: {
            beginAtZero: true
        }
    }
};

function updateVerifParametersText() {
    document.getElementById('verif-parameters-json').textContent = JSON.stringify(verifParameters, null, 2)
}

function addExpressionField() {

    var expressionsTable = document.getElementById('expressions-table')
    var row = expressionsTable.insertRow()
    var indexCell = row.insertCell()
    var mathFieldCell = row.insertCell()
    var mathFieldSpan = document.createElement('span')

    indexCell.textContent = expressionMathFields.length
    mathFieldCell.appendChild(mathFieldSpan)

    var mathField = MQ.MathField(mathFieldSpan, {
        spaceBehavesLikeTab: true,
        handlers: {
            edit: function () {
                var latex = mathField.latex()
                var index = expressionMathFields.indexOf(mathField)
                verifParameters.expressions[index] = latex
                updateVerifParametersText()            }
        }
    })

    expressionMathFields.push(mathField)
    verifParameters.expressions.push('')
    updateVerifParametersText()
}

function updateParameters() {
    verifParameters.unknown_variables[0] = {
        name: document.getElementById('variable-name').value,
        sample_start: parseFloat(document.getElementById('sample-start').value),
        sample_end: parseFloat(document.getElementById('sample-end').value),
        num_samples: parseInt(document.getElementById('num-samples').value, 10),
        sample_spacing: document.getElementById('sample-spacing').value
    }
    verifParameters.min_difference_detect_error = parseFloat(document.getElementById('min-difference-detect-error').value)
    updateVerifParametersText()
}

document.querySelectorAll('#verif-parameters input, #verif-parameters select').forEach(input => {
    input.addEventListener('change', updateParameters)
})

function initTestExpressions() {
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
        expressionMathFields[i].latex(test_exprs[i])
    }
}

function initChart(){
    var chartElementContext = document.getElementById("chart").getContext("2d")
    chart = new Chart(chartElementContext, {
        type: "line",
        data: chartData,
        options: chartOptions,
    })
}

function clearChart(){
    chart.data.labels = []
    chart.data.datasets[0].data = []
    // chart.data.datasets[0].label = ""
    chart.data.datasets[1].data = []
    // chart.data.datasets[1].label = ""
    chart.update()
}

function displayVerifResults(results){
    if(results["all-equal"] == true){
        console.log("all equal!")
        clearChart()
    }else{
        console.log(`results.data: ${results.data}`)
        results.data = JSON.parse(results.data) // I don't know why this is a string and not an object
        console.log(`results.data: ${results.data}`)
        // chart.data.labels =  [0, 1, 2, 3],
        // chart.data.datasets[0].data = [1, 2, 3, 4],
        // chart.data.datasets[1].data = [2, 3, 4, 5],
        console.log(`results: ${JSON.stringify(results)}`)
        console.log(`results.data: ${JSON.stringify(results.data)}`)
        console.log(`x axis array: ${results.data["x-axis-array"]}`)
        chart.data.labels = results["data"]["x-axis-array"]
        chart.data.datasets[0].data = results["data"]["y-axis-array1"]
        // chart.data.datasets[0].label = `expression ${results["first-inequal-indeces"][0]}`
        chart.data.datasets[1].data = results["data"]["y-axis-array2"]
        // chart.data.datasets[1].label = `expression ${results["first-inequal-indeces"][1]}`
        chart.update()
    }
}

function main() {
    var ws = new WebSocket('ws://localhost:8080')
    var verifOutputElement = document.getElementById('verif-output')
    
    ws.onmessage = function(event) {
        var message = JSON.parse(event.data)
        console.log(message)
        if (message.type == 'verif-running') {
            verifOutputElement.textContent = message.data + '\n'
        } else if (message.type === 'verif-output') {
            verifOutputElement.textContent = message.data + '\n'
            displayVerifResults(message)
        } else {
            verifOutputElement.textContent = "ERROR"
            console.log(`ERROR: unrecognized message of type \"${message.type}\"\n${message.data}`)
        }
    }
    
    document.getElementById('run-verif-button').addEventListener('click', function() {
        ws.send(JSON.stringify({ type: 'run-verif', data: verifParameters }))
    })
    for (var i = 0; i < NUM_EXPRESSIONS; i++) {
        addExpressionField()
    }
    initTestExpressions()
    initChart()
    updateParameters()
}

window.onload = main
