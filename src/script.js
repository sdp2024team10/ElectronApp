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

const axios = require('axios');

window.getMathExplanation = async function(problemDescription) {
    try {
        const response = await axios.post('https://api.openai.com/v1/chat/completions', {
            model: "gpt-3.5-turbo",
            messages: [
                {"role": "user", "content": problemDescription}
            ]
        }, {
            headers: {
                'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
                'Content-Type': 'application/json'
            }
        });

        // Extracting the content from the response
        const explanation = response.data.choices[0].message.content;

        // Update the DOM with the explanation
        document.getElementById('math-explanation').innerText = explanation;
    } catch (error) {
        console.error("Error getting explanation:", error);
        document.getElementById('math-explanation').innerText = "Error getting explanation.";
    }
};

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
        borderWidth: 2,
        pointRadius: 0, // no circle around points
        data: {},
    }, {
        label: '',
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 2,
        pointRadius: 0, // no circle around points
        data: {},
    }]
};
var chartOptions = {
    scales: {
        x: {
            type: "linear" // I think the default value might be graphing 10^x rather than x
        }
    }
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
        let [beforeIndex, afterIndex] = results["first-non-equal-indexes"]
        updateStatusElement(`expression #${afterIndex} is different from expression #${beforeIndex}`)
        chart.data.datasets[0].data = convertToChartData(results["x-axis-array"], results["y-axis-array1"])
        chart.data.datasets[0].label = `expression #${beforeIndex}`
        chart.data.datasets[1].data = convertToChartData(results["x-axis-array"], results["y-axis-array2"])
        chart.data.datasets[1].label = `expression #${afterIndex}`
        chart.update()
    }
}

function convertToChartData(xArray, yArray) {
    return xArray.map((x, index) => {
        return { x: x, y: yArray[index] };
    });
}

function renderLatex(latexString, elementId) {
    try {
        const latexElement = document.createElement('span');  // Create a new span for the LaTeX
        latexElement.innerHTML = katex.renderToString(latexString, {
            throwOnError: false
        });

        document.getElementById(elementId).appendChild(latexElement); // Append the span to the element
    } catch (error) {
        console.error("Error rendering LaTeX:", error);
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
                doOverwrite = false
                if (verifParameters.expressions.every(str => str === "")){
                    doOverwrite = true
                } else{
                    doOverwrite = confirm("new expressions received. Overwrite previous expressions?")
                }
                if(doOverwrite == true){
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
    document.getElementById('run-pred-button').addEventListener('click', function() {
        ws.send(JSON.stringify({ type: 'run-prediction' }));
    })
    for (var i = 0; i < NUM_EXPRESSIONS; i++) {
        addExpressionField()
    }
    initChart()
    updateParameters()
    
    const problem = "You are an assistant in our algebraic debugger. You need to output a response explaining why the step from x(x + 5) to x = 2 or x^3 + 5x is incorrect";
    getMathExplanation(problem);
}

window.onload = main
