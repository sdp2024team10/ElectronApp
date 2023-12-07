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
  run-verif-button (button)
  verif-status
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
var chartOptions = {}
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
            }
        }
    })

    expressionMathFields.push(mathField)
    verifParameters.expressions.push('')
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
}

document.querySelectorAll('#verif-parameters input, #verif-parameters select').forEach(input => {
    input.addEventListener('change', updateParameters)
})

function overwriteExpressions(newExpressions){
    if(expressionMathFields.length != newExpressions.length){
        console.log(`ERROR: cannot overwrite a ${expressionMathFields.length} element list with a ${newExpressions.length} element list!`)
        return
    }
    for (var i = 0; i < expressionMathFields.length; i++) {
        expressionMathFields[i].latex(newExpressions[i])
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
    chart.data.datasets[0].label = ""
    chart.data.datasets[1].data = []
    chart.data.datasets[1].label = ""
    chart.update()
}

function updateStatusElement(x){
    document.getElementById('verif-status').textContent = x.toString()
}

function displayVerifResults(results){
    if(results["all-equal"] == true){
        updateStatusElement("all expressions are equal!")
        clearChart()
    }else{
        updateStatusElement("inequality found in expressions.")
        chart.data.labels = results["x-axis-array"]
        chart.data.datasets[0].data = results["y-axis-array1"]
        chart.data.datasets[0].label = `expression ${results["first-non-equal-indexes"][0]}`
        chart.data.datasets[1].data = results["y-axis-array2"]
        chart.data.datasets[1].label = `expression ${results["first-non-equal-indexes"][1]}`
        chart.update()
    }
}

function main() {
    var ws = new WebSocket('ws://localhost:8080')
    ws.onmessage = function(event) {
        var message = JSON.parse(event.data)
        console.log(JSON.stringify(message))
        switch (message.type){
            case "verif-status":
                updateStatusElement(message["data"])
                break
            case "verif-output":
                var messageData = JSON.parse(message["data"]) // unclear why I need to parse twice
                displayVerifResults(messageData) // this also does updateStatusElement()
                break
            case "expressions":
                var response = confirm("new expressions received. Overwrite previous expressions?")
                if(response == true){
                    overwriteExpressions(message["data"])
                }
                break
            default:
                updateStatusElement("ERROR")
                console.log(`ERROR: unrecognized message of type \"${message.type}\"`)
        }
    }
    document.getElementById('run-verif-button').addEventListener('click', function() {
        ws.send(JSON.stringify({ type: 'run-verif', data: verifParameters }))
    })
    for (var i = 0; i < NUM_EXPRESSIONS; i++) {
        addExpressionField()
    }
    initChart()
    updateParameters()
}

window.onload = main
