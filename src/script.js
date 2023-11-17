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

document.addEventListener('DOMContentLoaded', () => {
    // Initialize content for LaTeX lines
    document.getElementById('line1').textContent = "line 1: ";
    document.getElementById('line2').textContent = "line 2: ";

    // Render LaTeX equations
    renderLatex("x(x+5)", "line1");
    renderLatex("x^3 + 5x", "line2");

    // Get a math explanation - ensure LLM.js is loaded
    const problem = "You are an assistant in our algebraic debugger. You need to output a response explaining why the step from x(x + 5) to x = 2 or x^3 + 5x is incorrect";
    if (window.getMathExplanation) {
        window.getMathExplanation(problem);
    } else {
        console.error("LLM.js has not been loaded. `getMathExplanation` function is not available.");
    }
});
