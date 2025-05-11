// Script to extract LaTeX from an image using Mathpix API
require('dotenv').config();
const fs = require('fs');
const path = require('path');
const axios = require('axios');

const IMAGE_PATH = path.join(__dirname, 'maxresdefault.jpg');
const APP_ID = process.env.MATHPIX_APP_ID;
const APP_KEY = process.env.MATHPIX_APP_KEY;

if (!APP_ID || !APP_KEY) {
  console.error('Please set MATHPIX_APP_ID and MATHPIX_APP_KEY in your .env file.');
  process.exit(1);
}

async function extractLatexFromImage(imagePath) {
  const imageData = fs.readFileSync(imagePath, { encoding: 'base64' });
  const data = {
    src: `data:image/jpeg;base64,${imageData}`,
    formats: ['latex_simplified'],
    data_options: {
      include_asciimath: false,
      include_latex: true
    }
  };

  try {
    const response = await axios.post(
      'https://api.mathpix.com/v3/text',
      data,
      {
        headers: {
          'app_id': APP_ID,
          'app_key': APP_KEY,
          'Content-type': 'application/json'
        }
      }
    );
    console.log('Extracted LaTeX:', response.data.latex_simplified || response.data.latex);
    return response.data.latex_simplified || response.data.latex;
  } catch (error) {
    console.error('Mathpix API error:', error.response ? error.response.data : error.message);
    process.exit(1);
  }
}

extractLatexFromImage(IMAGE_PATH);
