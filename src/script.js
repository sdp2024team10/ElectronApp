function renderLatex(latexString) {
    try {
        document.getElementById('latex-output').innerHTML = katex.renderToString(latexString, {
            throwOnError: false
        });
    } catch (error) {
        console.error("Error rendering LaTeX:", error);
    }
}

// Example usage
renderLatex("y = x^2 + \\frac{x}{2} + 85");
