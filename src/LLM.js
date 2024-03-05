// const axios = require('axios');

// window.getMathExplanation = async function(problemDescription) {
//     try {
//         const response = await axios.post('https://api.openai.com/v1/chat/completions', {
//             model: "gpt-3.5-turbo",
//             messages: [
//                 {"role": "user", "content": problemDescription}
//             ]
//         }, {
//             headers: {
//                 'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
//                 'Content-Type': 'application/json'
//             }
//         });

//         // Extracting the content from the response
//         const explanation = response.data.choices[0].message.content;

//         // Update the DOM with the explanation
//         document.getElementById('math-explanation').innerText = explanation;
//     } catch (error) {
//         console.error("Error getting explanation:", error);
//         document.getElementById('math-explanation').innerText = "Error getting explanation.";
//     }
// };


