require('dotenv').config({ path: '../.env' });
const axios = require('axios');
const fs = require('fs');

// Use the existing Google API key
const apiKey = process.env.GOOGLE_API_KEY;

async function generateImage(prompt) {
  try {
    console.log('Using API Key:', apiKey);
    console.log('Generating image with prompt:', prompt);
    
    const response = await axios.post(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent?key=${apiKey}`,
      {
        contents: [{
          parts: [
            { text: prompt }
          ]
        }],
        generationConfig: { responseModalities: ["Text", "Image"] }
      },
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );
    
    console.log('Response received');
    
    // Check if we have image data in the response
    if (response.data && 
        response.data.candidates && 
        response.data.candidates[0] && 
        response.data.candidates[0].content && 
        response.data.candidates[0].content.parts) {
      
      const parts = response.data.candidates[0].content.parts;
      
      // Find the image part
      const imagePart = parts.find(part => part.inlineData && part.inlineData.mimeType.startsWith('image/'));
      
      if (imagePart) {
        // Extract and save the image
        const imageData = imagePart.inlineData.data; // This is base64 encoded
        const mimeType = imagePart.inlineData.mimeType;
        const extension = mimeType.split('/')[1];
        
        // Save the image
        const outputPath = `./test_output.${extension}`;
        fs.writeFileSync(outputPath, Buffer.from(imageData, 'base64'));
        console.log(`Image saved to ${outputPath}`);
        
        // Also find and log any text response
        const textPart = parts.find(part => part.text);
        if (textPart) {
          console.log('Text response:', textPart.text);
        }
        
        return { success: true, path: outputPath };
      } else {
        console.error('No image found in response');
        console.log('Full response:', JSON.stringify(response.data, null, 2));
        return { success: false, error: 'No image in response' };
      }
    } else {
      console.error('Unexpected response format');
      console.log('Full response:', JSON.stringify(response.data, null, 2));
      return { success: false, error: 'Unexpected response format' };
    }
  } catch (error) {
    console.error('Error generating image:', error.message);
    if (error.response) {
      console.error('Response data:', JSON.stringify(error.response.data, null, 2));
    }
    return { success: false, error: error.message };
  }
}

// Test with a simple prompt
const testPrompt = "A 3D rendered image of a pig with wings and a top hat flying over a futuristic city with greenery";
generateImage(testPrompt)
  .then(result => {
    if (result.success) {
      console.log('Test successful!');
    } else {
      console.log('Test failed:', result.error);
    }
  })
  .catch(err => {
    console.error('Unexpected error:', err);
  });
