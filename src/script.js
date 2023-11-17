function renderLatex(latexString) {
    try {
        document.getElementById('latex-output').innerHTML = katex.renderToString(latexString, {
            throwOnError: false
        });
    } catch (error) {
        console.error("Error rendering LaTeX:", error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Render a LaTeX equation
    renderLatex("y = x^2 + \\frac{x}{2} + 85");

    // Get a math explanation - ensure LLM.js is loaded
    const problem = "Explain why the step from x^2 + x = 5 to x = 2 or x = 3 is incorrect in solving a quadratic equation.";
    if (window.getMathExplanation) {
        window.getMathExplanation(problem);
    } else {
        console.error("LLM.js has not been loaded. `getMathExplanation` function is not available.");
    }
});

